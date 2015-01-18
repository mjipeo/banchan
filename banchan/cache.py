import functools
import time


class Cacheable(object):
    """Local memeory cache which periodically refresh the data by executing
    given generating function. Note that this cache isn't shared across
    multiple servers.
    """

    def __init__(self, func, timeout=None, lazy=True):
        self._func = func
        self._timeout = timeout
        self._lazy = lazy
        self._value = None
        self._last_fetched_at = None

        if not lazy:
            self._fetch()

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    @property
    def elapsed(self):
        return (time.time() - self._last_fetched_at
                if self._last_fetched_at else None)

    def get(self, force_fetch=False):
        if (force_fetch
                or self._value is None
                or (self._timeout is not None
                    and self.elapsed >= self._timeout)):
            self._fetch()
        return self._value

    def _fetch(self):
        self._value = self._func()
        self._last_fetched_at = time.time()


def cached(timeout):
    """Simple decorator"""

    _vault = {}

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = u'{args}_{kwargs}'.format(
                args=tuple(args),
                kwargs=tuple(sorted(kwargs.items()))
            )
            generator = functools.partial(func, *args, **kwargs)
            cacheable = _vault.get(cache_key)
            if cacheable is None:
                cacheable = Cacheable(generator, timeout)
                _vault[cache_key] = cacheable
            return cacheable.get()
        return wrapper
    return decorator


# memoized is similar to cached but timeout is none
memoized = functools.partial(cached, timeout=None)
