project('dependency fallbacks', 'c')

cc = meson.get_compiler('c')

dep = dependency('foo', 'foo1',
  cc.find_library_fallback('foo', has_headers : ['foo.h']),
  subproject_fallback('foo', variable: 'foo_dep'),
)
assert(dep.found(), 'Dependency fallbacks not working')

dep = dependency('foo')
assert(dep.found(), 'Dependency caching not working')

dep = dependency('foo1')
assert(dep.found(), 'Dependency caching not working')
