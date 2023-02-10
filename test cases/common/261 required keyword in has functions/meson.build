project('required keyword in has functions', 'c')

cc = meson.get_compiler('c')
opt = get_option('opt')

cc.has_function('printf', prefix : '#include<stdio.h>', required : true)
cc.has_type('time_t', prefix : '#include<time.h>', required : true)
cc.has_member('struct tm', 'tm_sec', prefix : '#include<time.h>', required : true)
cc.has_members('struct tm', ['tm_sec', 'tm_min'], prefix : '#include<time.h>', required : true)

assert(not cc.has_function('printf', prefix : '#include<stdio.h>', required : opt))
assert(not cc.has_type('time_t', prefix : '#include<time.h>', required : opt))
assert(not cc.has_member('struct tm', 'tm_sec', prefix : '#include<time.h>', required : opt))
assert(not cc.has_members('struct tm', ['tm_sec', 'tm_min'], prefix : '#include<time.h>', required : opt))

# compiler.has_argument
if cc.get_id() == 'msvc'
  is_arg = '/O2'
else
  is_arg = '-O2'
endif
cc.has_argument(is_arg, required: true)
assert(not cc.has_argument(is_arg, required: opt))

# compiler.has_multi_arguments
if cc.get_id() == 'gcc'
  pre_arg = '-Wformat'
  arg = '-Werror=format-security'
  cc.has_multi_arguments([pre_arg, arg], required: true)
  assert(not cc.has_multi_arguments(pre_arg, arg, required: opt))
endif

# compiler.has_link_argument
if cc.get_argument_syntax() == 'msvc'
  is_arg = '/OPT:REF'
else
  is_arg = '-Wl,-L/tmp'
endif
cc.has_link_argument(is_arg, required: true)
assert(not cc.has_link_argument(is_arg, required: opt))

# compiler.has_multi_link_argument

# compiler.has_function_attribute
if not ['pgi', 'msvc', 'clang-cl', 'intel-cl'].contains(cc.get_id())
  a = 'aligned'
  cc.has_function_attribute(a, required: true)
  assert(not cc.has_function_attribute(a, required: opt))
endif
