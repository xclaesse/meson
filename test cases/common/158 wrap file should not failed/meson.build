project('mainproj', 'c',
  default_options : ['wrap_mode=nodownload'],
)

subproject('zlib')

if find_program('patch', required : false).found()
  exe = subproject('foo').get_variable('foo_exe')
  test('test_foo', exe)
endif

executable('grabprog', files('src/subprojects/prog.c'))
executable('grabprog2', files('src/subprojects/foo/prog2.c'))
subdir('src')
