# Copyright 2014-2016 The Meson development team

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

import itertools
import shutil
import textwrap
import typing as T
import collections

from . import build
from . import coredata
from . import environment
from . import mesonlib
from . import mintro
from . import mlog
from .ast import AstIDGenerator
from .mesonlib import MachineChoice, OptionKey

if T.TYPE_CHECKING:
    import argparse

def add_arguments(parser: 'argparse.ArgumentParser') -> None:
    coredata.register_builtin_arguments(parser)
    parser.add_argument('-B', dest='builddir', default=None,
                        help='The directory containing build files (optional).')
    parser.add_argument('dir1', nargs='?', default=None, metavar='build or source dir',
                        help='Directory containing build or source files (default to current directory).')
    parser.add_argument('--clearcache', action='store_true', default=False,
                        help='Clear cached state (e.g. found dependencies)')
    parser.add_argument('--no-pager', action='store_false', dest='pager',
                        help='Do not redirect output to a pager')

def stringify(val: T.Any) -> T.Union[str, T.List[T.Any]]:  # T.Any because of recursion...
    if isinstance(val, bool):
        return str(val).lower()
    elif isinstance(val, list):
        s = ', '.join(stringify(i) for i in val)
        return f'[{s}]'
    elif val is None:
        return ''
    else:
        return str(val)


class ConfException(mesonlib.MesonException):
    pass


class Conf:
    def __init__(self, builddir, sourcedir):
        self.build = None
        self.max_choices_line_length = 60
        self.name_col = []
        self.value_col = []
        self.choices_col = []
        self.descr_col = []
        self.all_subprojects: T.Set[str] = set()

        if builddir:
            self.build_dir = builddir
            self.build = build.load(self.build_dir)
            self.source_dir = self.build.environment.get_source_dir()
            self.coredata = coredata.load(self.build_dir)
            self.default_values_only = False
        else:
            # Make sure that log entries in other parts of meson don't interfere with the JSON output
            mlog.disable()
            self.source_dir = sourcedir
            intr = mintro.IntrospectionInterpreter(self.source_dir, '', 'ninja', visitors = [AstIDGenerator()])
            intr.analyze()
            # Re-enable logging just in case
            mlog.enable()
            self.coredata = intr.coredata
            self.default_values_only = True

    def clear_cache(self):
        self.coredata.clear_deps_cache()

    def set_options(self, options):
        self.coredata.set_options(options)

    def save(self):
        # Do nothing when using introspection
        if self.default_values_only:
            return
        coredata.save(self.coredata, self.build_dir)
        # We don't write the build file because any changes to it
        # are erased when Meson is executed the next time, i.e. when
        # Ninja is run.

    def print_aligned(self) -> None:
        """Do the actual printing.

        This prints the generated output in an aligned, pretty form. it aims
        for a total width of 160 characters, but will use whatever the tty
        reports it's value to be. Though this is much wider than the standard
        80 characters of terminals, and even than the newer 120, compressing
        it to those lengths makes the output hard to read.

        Each column will have a specific width, and will be line wrapped.
        """
        total_width = shutil.get_terminal_size(fallback=(160, 0))[0]
        _col = max(total_width // 5, 20)
        last_column = total_width - (3 * _col) - 3
        four_column = (_col, _col, _col, last_column if last_column > 1 else _col)

        for line in zip(self.name_col, self.value_col, self.choices_col, self.descr_col):
            if not any(line):
                mlog.log('')
                continue

            # This is a header, like `Subproject foo:`,
            # We just want to print that and get on with it
            if line[0] and not any(line[1:]):
                mlog.log(line[0])
                continue

            def wrap_text(text, width):
                raw = text.text if isinstance(text, mlog.AnsiDecorator) else text
                indent = ' ' if raw.startswith('[') else ''
                wrapped = textwrap.wrap(raw, width, subsequent_indent=indent)
                if isinstance(text, mlog.AnsiDecorator):
                    wrapped = [mlog.AnsiDecorator(i, text.code) for i in wrapped]
                # Add padding here to get even rows, as `textwrap.wrap()` will
                # only shorten, not lengthen each item
                return [str(i) + ' ' * (width - len(i)) for i in wrapped]

            # wrap will take a long string, and create a list of strings no
            # longer than the size given. Then that list can be zipped into, to
            # print each line of the output, such the that columns are printed
            # to the right width, row by row.
            name = wrap_text(line[0], four_column[0])
            val = wrap_text(line[1], four_column[1])
            choice = wrap_text(line[2], four_column[2])
            desc = wrap_text(line[3], four_column[3])
            for l in itertools.zip_longest(name, val, choice, desc, fillvalue=''):
                items = [l[i] if l[i] else ' ' * four_column[i] for i in range(4)]
                mlog.log(*items)

    def split_options_per_subproject(self, options: 'coredata.KeyedOptionDictType') -> T.Dict[str, 'coredata.KeyedOptionDictType']:
        result: T.Dict[str, 'coredata.KeyedOptionDictType'] = {}
        for k, o in options.items():
            if k.subproject:
                self.all_subprojects.add(k.subproject)
            result.setdefault(k.subproject, {})[k] = o
        return result

    def _add_line(self, name, value, choices, descr) -> None:
        if isinstance(name, mlog.AnsiDecorator):
            name.text = ' ' * self.print_margin + name.text
        else:
            name = ' ' * self.print_margin + name
        self.name_col.append(name)
        self.value_col.append(value)
        self.choices_col.append(choices)
        self.descr_col.append(descr)

    def add_option(self, name, descr, value, choices):
        value = stringify(value)
        choices = stringify(choices)
        self._add_line(mlog.green(name), mlog.yellow(value), mlog.blue(choices), descr)

    def add_title(self, title):
        title = mlog.cyan(title)
        descr = mlog.cyan('Description')
        value = mlog.cyan('Default Value' if self.default_values_only else 'Current Value')
        choices = mlog.cyan('Possible Values')
        self._add_line('', '', '', '')
        self._add_line(title, value, choices, descr)
        self._add_line('-' * len(title), '-' * len(value), '-' * len(choices), '-' * len(descr))

    def add_section(self, section):
        self.print_margin = 0
        self._add_line('', '', '', '')
        self._add_line(mlog.normal_yellow(section + ':'), '', '', '')
        self.print_margin = 2

    def print_options(self, title: str, options: 'coredata.KeyedOptionDictType') -> None:
        if not options:
            return
        if title:
            self.add_title(title)
        auto = T.cast('coredata.UserFeatureOption', self.coredata.options[OptionKey('auto_features')])
        for k, o in sorted(options.items()):
            printable_value = o.printable_value()
            root = k.as_root()
            if o.yielding and k.subproject and root in self.coredata.options:
                printable_value = '<inherited from main project>'
            if isinstance(o, coredata.UserFeatureOption) and o.is_auto():
                printable_value = auto.printable_value()
            self.add_option(str(root), o.description, printable_value, o.choices)

    def print_conf(self, pager: bool):
        if pager:
            mlog.start_pager()

        def print_default_values_warning():
            mlog.warning('The source directory instead of the build directory was specified.')
            mlog.warning('Only the default values for the project are printed, and all command line parameters are ignored.')

        if self.default_values_only:
            print_default_values_warning()
            mlog.log('')

        mlog.log('Core properties:')
        mlog.log('  Source dir', self.source_dir)
        if not self.default_values_only:
            mlog.log('  Build dir ', self.build_dir)

        dir_option_names = set(coredata.BUILTIN_DIR_OPTIONS)
        test_option_names = {OptionKey('errorlogs'),
                             OptionKey('stdsplit')}

        dir_options: 'coredata.KeyedOptionDictType' = {}
        test_options: 'coredata.KeyedOptionDictType' = {}
        core_options: 'coredata.KeyedOptionDictType' = {}
        module_options: T.Dict[str, 'coredata.KeyedOptionDictType'] = collections.defaultdict(dict)
        for k, v in self.coredata.options.items():
            if k in dir_option_names:
                dir_options[k] = v
            elif k in test_option_names:
                test_options[k] = v
            elif k.module:
                # Ignore module options if we did not use that module during
                # configuration.
                if self.build and k.module not in self.build.modules:
                    continue
                module_options[k.module][k] = v
            elif k.is_builtin():
                core_options[k] = v

        host_core_options = self.split_options_per_subproject({k: v for k, v in core_options.items() if k.machine is MachineChoice.HOST})
        build_core_options = self.split_options_per_subproject({k: v for k, v in core_options.items() if k.machine is MachineChoice.BUILD})
        host_compiler_options = self.split_options_per_subproject({k: v for k, v in self.coredata.options.items() if k.is_compiler() and k.machine is MachineChoice.HOST})
        build_compiler_options = self.split_options_per_subproject({k: v for k, v in self.coredata.options.items() if k.is_compiler() and k.machine is MachineChoice.BUILD})
        project_options = self.split_options_per_subproject({k: v for k, v in self.coredata.options.items() if k.is_project()})
        show_build_options = self.default_values_only or self.build.environment.is_cross_build()

        self.add_section('Main project options')
        self.print_options('Core options', host_core_options[''])
        if show_build_options:
            self.print_options('', build_core_options[''])
        self.print_options('Backend options', {k: v for k, v in self.coredata.options.items() if k.is_backend()})
        self.print_options('Base options', {k: v for k, v in self.coredata.options.items() if k.is_base()})
        self.print_options('Compiler options', host_compiler_options.get('', {}))
        if show_build_options:
            self.print_options('', build_compiler_options.get('', {}))
        for mod, mod_options in module_options.items():
            self.print_options(f'{mod} module options', mod_options)
        self.print_options('Directories', dir_options)
        self.print_options('Testing options', test_options)
        self.print_options('Project options', project_options.get('', {}))
        for subproject in sorted(self.all_subprojects):
            if subproject == '':
                continue
            self.add_section('Subproject ' + subproject)
            if subproject in host_core_options:
                self.print_options('Core options', host_core_options[subproject])
            if subproject in build_core_options and show_build_options:
                self.print_options('', build_core_options[subproject])
            if subproject in host_compiler_options:
                self.print_options('Compiler options', host_compiler_options[subproject])
            if subproject in build_compiler_options and show_build_options:
                self.print_options('', build_compiler_options[subproject])
            if subproject in project_options:
                self.print_options('Project options', project_options[subproject])
        self.print_aligned()

        # Print the warning twice so that the user shouldn't be able to miss it
        if self.default_values_only:
            mlog.log('')
            print_default_values_warning()

        self.print_nondefault_buildtype_options()

    def print_nondefault_buildtype_options(self):
        mismatching = self.coredata.get_nondefault_buildtype_args()
        if not mismatching:
            return
        mlog.log("\nThe following option(s) have a different value than the build type default\n")
        mlog.log('               current   default')
        for m in mismatching:
            mlog.log(f'{m[0]:21}{m[1]:10}{m[2]:10}')

def run(options):
    coredata.parse_cmd_line_options(options)
    sourcedir, builddir = environment.validate_single_dir(options.builddir, options.dir1)
    c = None
    try:
        c = Conf(builddir, sourcedir)
        if c.default_values_only:
            c.print_conf(options.pager)
            return 0

        save = False
        if options.cmd_line_options:
            c.set_options(options.cmd_line_options)
            coredata.update_cmd_line_file(builddir, options)
            save = True
        elif options.clearcache:
            c.clear_cache()
            save = True
        else:
            c.print_conf(options.pager)
        if save:
            c.save()
            mintro.update_build_options(c.coredata, c.build.environment.info_dir)
            mintro.write_meson_info_file(c.build, [])
    except ConfException as e:
        mlog.log('Meson configurator encountered an error:')
        if c is not None and c.build is not None:
            mintro.write_meson_info_file(c.build, [e])
        raise e
    except BrokenPipeError:
        # Pager quit before we wrote everything.
        pass
    return 0
