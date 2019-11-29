## Added `has_header_symbol` argument to `find_library`

Similar to the existing `has_header` keyword argument, but also checks that a
given symbol is defined in the header.

```meson
compiler.find_library('mylib', has_header_symbol: ['mylib.h', 'mylib_foo'])
```
