import os
from .dependencies import pkgconfig

def add_arguments(parser: 'argparse.ArgumentParser') -> None:
    parser.add_argument("--cflags", action='store_true')
    parser.add_argument("--libs", action='store_true')
    parser.add_argument("--static", action='store_true')
    parser.add_argument("--modversion", action='store_true')
    parser.add_argument("--variable")
    parser.add_argument("--define-variable")
    parser.add_argument("modules", nargs="*")

def run(options: 'argparse.Namespace') -> int:
    env = os.environ.get('PKG_CONFIG_LIBDIR')
    system_paths = env.split(os.pathsep) if env else None

    env = os.environ.get('PKG_CONFIG_PATH')
    extra_paths = env.split(os.pathsep) if env else None

    allow_system_cflags = os.environ.get('PKG_CONFIG_ALLOW_SYSTEM_CFLAGS') is not None
    allow_system_libs = os.environ.get('PKG_CONFIG_ALLOW_SYSTEM_LIBS') is not None

    sysroot_dir = os.environ.get('PKG_CONFIG_SYSROOT_DIR', '')

    # 'a:b:c:d' -> {'a': 'b', 'c': 'd'}
    sysroot_map = os.environ.get('PKG_CONFIG_SYSROOT_MAP', '')
    sysroot_map = sysroot_map.split(os.pathsep)
    sysroot_map = dict(zip(sysroot_map[::2], sysroot_map[1::2]))

    define_variable = None
    if options.define_variable:
        define_variable = options.define_variable.split('=', 1)

    all_cflags = []
    all_libs = []
    repo = pkgconfig.Repository(system_paths, extra_paths, sysroot_dir, sysroot_map)
    for module in options.modules:
        pkg = repo.lookup(module)
        if options.modversion:
            print(pkg.version)
        if options.variable:
            print(pkg.get_variable(options.variable, definition=define_variable))
        if options.cflags:
            all_cflags += pkg.get_cflags(allow_system_cflags)
        if options.libs:
            all_libs += pkg.get_libs(options.static, allow_system_libs)
    all_args = all_cflags + all_libs
    if all_args:
        print(' '.join(all_args))
    return 0
