project('subdir subproject')

subdir('foo', subproject : true)

assert(subproject('foo').get_variable('foo_var'))
