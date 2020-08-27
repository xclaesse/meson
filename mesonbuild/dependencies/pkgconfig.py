# Copyright 2020 The Meson development team

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, itertools
from collections import OrderedDict
from pathlib import Path

from .. import mesonlib

ONE_ARG_PATHS = {'-I', '-L'}
TWO_ARGS_PATHS = {'-isystem'}

class PkgConfigException(mesonlib.MesonException):
    pass

class Package:
    def __init__(self, repo, filename, sysroot):
        self.repo = repo
        self.filename = filename
        self.sysroot = sysroot

        self.variables = {}
        self.raw_variables = OrderedDict()
        self.name = ''
        self.description = ''
        self.version = ''
        self.url = ''
        self.requires_private = []
        self.requires = []
        self.conflicts = []
        self.libs_private = []
        self.libs = []
        self.cflags = []

        self._parse()

    def _parse(self):
        for line in self._readlines():
            key_len = next((i for i, ch in enumerate(line) if ch in ['=', ':']), None)
            if not key_len:
                continue
            key = line[:key_len].strip()
            raw_value = line[key_len+1:].strip()
            value = self._expand(raw_value, self.variables)
            if line[key_len] == '=':
                self.variables[key] = value
                self.raw_variables[key] = raw_value
            elif key == 'Name':
                self.name = value
            elif key == 'Description':
                self.description = value
            elif key == 'Version':
                self.version = value
            elif key == 'URL':
                self.url = value
            elif key == 'Requires.private':
                self.requires_private = self._parse_requires(value)
            elif key == 'Requires':
                self.requires = self._parse_requires(value)
            elif key == 'Conflicts':
                self.conflicts = self._parse_requires(value)
            elif key == 'Libs.private':
                self.libs_private = self._parse_args(value)
            elif key == 'Libs':
                self.libs = self._parse_args(value)
            elif key == 'Cflags' or key == 'CFlags':
                self.cflags = self._parse_args(value)

    def _parse_args(self, value):
        args = []
        iterator = iter(mesonlib.split_args(value))
        for a in iterator:
            if a in ONE_ARG_PATHS:
                # ['-I', '/foo'] -> '-I/sysroot/foo'
                args.append(a + self._prepend_sysroot(next(iterator)))
            elif any(a.startswith(flag) for flag in ONE_ARG_PATHS):
                # '-I/foo' -> '-I/sysroot/foo'
                args.append(a[:2] + self._prepend_sysroot(a[2:]))
            elif a in TWO_ARGS_PATHS:
                # ['-isystem', '/foo'] -> ['-isystem', '/sysroot/foo']
                args.append(a)
                args.append(self._prepend_sysroot(next(iterator)))
            else:
                args.append(a)
        return args

    def _prepend_sysroot(self, path):
        if not self.sysroot:
            return path
        path = Path(path)
        path = path.relative_to(path.anchor)
        return Path(self.sysroot, path).as_posix()

    def _parse_requires(self, content):
        SEPARATORS = ' ,'
        OPERATORS = '<>=!'

        STATE_NAME = 1,
        STATE_OPERATOR = 2,
        STATE_VERSION = 3

        packages = []
        name = ''
        op = ''
        version = ''

        def process_package():
            wanted = op + version
            pkg = self.repo.lookup(name)
            if wanted and not mesonlib.version_compare(pkg.version, wanted):
                raise PkgConfigException('Version mismatch: wanted {!r} but got {!r}'.format(wanted, pkg.version))
            packages.append(pkg)

        start = 0
        state = STATE_NAME
        for i, c in enumerate(itertools.chain(content, ' ')):
            if state == STATE_NAME:
                if c in SEPARATORS:
                    if not name:
                        name = content[start:i]
                    start = i + 1
                elif c in OPERATORS:
                    state = STATE_OPERATOR
                    if not name:
                        name = content[start:i]
                    start = i
                elif name:
                    process_package()
                    name = ''
                    start = i
            elif state == STATE_OPERATOR:
                if c in SEPARATORS:
                    state = STATE_VERSION
                    op = content[start:i]
                    start = i + 1
                elif c not in OPERATORS:
                    state = STATE_VERSION
                    op = content[start:i]
                    start = i
            elif state == STATE_VERSION:
                if c in SEPARATORS:
                    if not version:
                        version = content[start:i]
                    if version:
                        process_package()
                        name = op = version = ''
                        state = STATE_NAME
                    start = i + 1
        if name:
            process_package()
        return packages

    def _expand(self, content, variables):
        dollar = False
        brackets = False
        start = 0
        line = ''
        for i, c in enumerate(content):
            if brackets:
                if c == '}':
                    brackets = False
                    varname = content[start:i]
                    line += variables[varname]
                    start = i + 1
            elif dollar:
                if c == '{':
                    dollar = False
                    brackets = True
                    line += content[start:i-1]
                    start = i + 1
                elif c == '$':
                    line += content[start:i]
                    start = i + 1
                    dollar = False
            elif c == '$':
                dollar = True
        line += content[start:]
        return line

    def _readlines(self):
        with open(self.filename, 'r') as f:
            content = f.read()
        # Parse the file char by char. Avoid appending each char individually
        # into line string because that creates a new string each time, instead
        # keep track of the start of the chunk and append only once we found
        # a char that cannot be copied as-is.
        escaped = False
        comment = False
        start = 0
        line = ''
        for i, c in enumerate(itertools.chain(content, '\n')):
            # '\r' and '\r\n' are treated as if it was a single '\n' char
            if c == '\r':
                if content[i+1] == '\n':
                    continue
                c = '\n'
            if comment:
               # When inside a comment, ignore everything until end of line.
                if c == '\n':
                    comment = False
                    start = i + 1
            elif escaped:
                escaped = False
                if c == '\n':
                    # '\\n' - Skip both chars and continue current line.
                    start = i + 1
                elif c == '#':
                    # '\#' - Skip '\' and include '#'
                    start = i
                else:
                    # '\?' - Include both chars.
                    start = i - 1
            elif c == '\\':
                # Next char is escaped, copy everything we had so far.
                escaped = True
                line += content[start:i]
            elif c == '#':
                # '#' ends the current line. Next line will start after the
                # first '\n' we'll find.
                comment = True
                line += content[start:i]
                yield line
                line = ''
            elif c == '\n':
                # '\n' ends the current line. Next like starts at the next char.
                line += content[start:i]
                yield line
                line = ''
                start = i + 1

    def _get_args(self, args, system_args, allow_system_args):
        if allow_system_args:
            return args.copy()
        return [a for a in args if a not in system_args]

    def get_cflags(self, allow_system_cflags=False):
        cflags = self._get_args(self.cflags, self.repo.system_cflags, allow_system_cflags)
        for pkg in self.requires_private:
            cflags.extend(pkg.get_cflags(allow_system_cflags))
        for pkg in self.requires:
            cflags.extend(pkg.get_cflags(allow_system_cflags))
        return cflags

    def get_libs(self, static, allow_system_libs=False):
        libs = self._get_args(self.libs, self.repo.system_libs, allow_system_libs)
        for pkg in self.requires:
            libs.extend(pkg.get_libs(static))
        if static:
            libs.extend(self._get_args(self.libs_private, self.repo.system_libs, allow_system_libs))
            for pkg in self.requires_private:
                libs.extend(pkg.get_libs(static))
        return libs

    def get_variable(self, varname, default=None, definition=None):
        if not definition:
            return self.variables.get(varname, default)

        defname, defvalue = definition
        if varname == defname:
            return defvalue

        # Reevaluate all variables in order, with the new definition, until we
        # find the one we want.
        variables = {defname: defvalue}
        for key, raw_value in self.raw_variables.items():
            if key == defname:
                continue
            value = self._expand(raw_value, variables)
            if key == varname:
                return value
            variables[key] = value

        if default is not None:
            return default

        raise PkgConfigException('Unknown variable name: {!r}'.format(varname))

class Repository:
    def __init__(self, system_paths=None, extra_paths=None, sysroot_dir=None, sysroot_map=None):
        system_prefix = 'c:/' if mesonlib.is_windows() else '/usr'
        self.system_libdir = Path(system_prefix, mesonlib.default_libdir())
        self.system_incdir = Path(system_prefix, 'include')
        if not system_paths:
            system_paths = [Path(self.system_libdir, 'pkgconfig')]
        self.system_paths = system_paths
        self.extra_paths = extra_paths if extra_paths else []
        self.system_cflags = ['-I' + self.system_incdir.as_posix()]
        self.system_libs = ['-L' + self.system_libdir.as_posix()]

        self.sysroot_map = {Path(k): Path(v) for k, v in sysroot_map.items()} if sysroot_map else {}
        self.sysroot_dir = Path(sysroot_dir) if sysroot_dir else None

        self.cache = {}

    def lookup(self, name):
        pkg = self.cache.get(name)
        if pkg:
            return pkg

        pkg = self._lookup_internal(name + '-uninstalled.pc')
        if not pkg:
            pkg = self._lookup_internal(name + '.pc')
        if not pkg:
            raise PkgConfigException('Package not found: ' + name)

        self.cache[name] = pkg

        return pkg

    def _lookup_internal(self, fname):
        for d in itertools.chain(self.system_paths, self.extra_paths):
            filename = Path(d, fname)
            if filename.is_file():
                sysroot = self.sysroot_map.get(d, self.sysroot_dir)
                return Package(self, filename, sysroot)
        return None
