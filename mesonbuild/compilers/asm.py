import typing as T

from ..mesonlib import EnvironmentException, get_meson_command
from .compilers import Compiler

if T.TYPE_CHECKING:
    from ..coredata import KeyedOptionDictType
    from ..environment import Environment


class NasmCompiler(Compiler):
    language = 'nasm'
    id = 'nasm'

    def needs_static_linker(self) -> bool:
        return False

    def get_always_args(self) -> T.List[str]:
        cpu = '64' if self.info.is_64_bit else '32'
        if self.info.is_windows() or self.info.is_cygwin():
            plat = 'win'
            define = f'WIN{cpu}'
        elif self.info.is_darwin():
            plat = 'macho'
            define = 'MACHO'
        else:
            plat = 'elf'
            define = 'ELF'
        args = ['-f', f'{plat}{cpu}', f'-D{define}']
        if self.info.is_64_bit:
            args.append('-D__x86_64__')
        return args

    def get_werror_args(self) -> T.List[str]:
        return ['-Werror']

    def get_output_args(self, outputname: str) -> T.List[str]:
        return ['-o', outputname]

    def get_optimization_args(self, optimization_level: str) -> T.List[str]:
        return [f'-O{optimization_level}']

    def get_debug_args(self, is_debug: bool) -> T.List[str]:
        if self.info.is_windows():
            return []
        return ['-g', '-F', 'dwarf']

    def get_depfile_suffix(self) -> str:
        return 'd'

    def get_dependency_gen_args(self, outtarget: str, outfile: str) -> T.List[str]:
        return ['-MD', '-MQ', outtarget, '-MF', outfile]

    def sanity_check(self, work_dir: str, environment: 'Environment') -> None:
        if self.info.cpu_family not in {'x86', 'x86_64'}:
            raise EnvironmentException(f'ASM compiler {self.id!r} does not support {self.info.cpu_family} CPU family')

    def get_buildtype_args(self, buildtype: str) -> T.List[str]:
        # FIXME: Not implemented
        return []

    def get_pic_args(self) -> T.List[str]:
        return []

    def get_include_args(self, path: str, is_system: bool) -> T.List[str]:
        if not path:
            path = '.'
        return ['-I' + path]

    def compute_parameters_with_absolute_paths(self, parameter_list: T.List[str],
                                               build_dir: str) -> T.List[str]:
        # FIXME: What is it?
        return parameter_list.copy()

    def get_options(self) -> 'KeyedOptionDictType':
        return super().get_options()

    def get_option_compile_args(self, options: 'KeyedOptionDictType') -> T.List[str]:
        return []

class YasmCompiler(NasmCompiler):
    id = 'yasm'

    def get_exelist(self) -> T.List[str]:
        # Wrap yasm executable with an internal script that will write depfile.
        exelist = super().get_exelist()
        return get_meson_command() + ['--internal', 'yasm'] + exelist

    def get_debug_args(self, is_debug: bool) -> T.List[str]:
        if self.info.is_windows():
            return ['-g', 'null']
        return ['-g', 'dwarf2']

    def get_dependency_gen_args(self, outtarget: str, outfile: str) -> T.List[str]:
        return ['--depfile', outfile]

class MasmCompiler(Compiler):
    language = 'masm'
    id = 'ml'

    def needs_static_linker(self) -> bool:
        return False

    def sanity_check(self, work_dir: str, environment: 'Environment') -> None:
        pass

    def get_always_args(self) -> T.List[str]:
        return ['/nologo']

    def get_optimization_args(self, optimization_level: str) -> T.List[str]:
        return []

    def get_compile_only_args(self) -> T.List[str]:
        return ['/c']

    def get_output_args(self, target: str) -> T.List[str]:
        return ['/Fo' + target]

    def get_debug_args(self, is_debug: bool) -> T.List[str]:
        return ['/Zi', '/Zd'] if is_debug else []

    def get_argument_syntax(self) -> str:
        return 'msvc'

class ArmAsmCompiler(MasmCompiler):
    id = 'armasm'

    def get_output_args(self, target: str) -> T.List[str]:
        return ['-o', target]

    def get_debug_args(self, is_debug: bool) -> T.List[str]:
        return ['-g'] if is_debug else []
