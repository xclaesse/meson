project('My Project', version : '1.0')

sec1 = {'driver' : 'foobar'}
sec2 = {'driver' : 'dive comp', 'API' : '1.1.2'}
sec3 = {'with' : {'mesa' : true, 'gbm' : false}}


subproject('sub')
subproject('sub2', required : false)

summary('Directories', {'bindir': get_option('bindir'),
                        'libdir': get_option('libdir'),
                        'datadir': get_option('datadir'),
                        })
summary('Configuration', {'Some boolean': false,
                          'Another boolean': true,
                          'Some string': 'Hello World',
                          'A list': ['string', 1, true],
                          })
