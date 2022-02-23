from functools import wraps
from time import time

def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print('func:%r args:[%r, %r] took: %2.5f msec' % \
          (f.__name__, args, kw, (te-ts)*1000))
        return result
    return wrap