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


class LRUCache(dict):
    """A dictionary-like object that stores only a certain number of items, and
    discards its least recently used item when full.

    >>> cache = LRUCache(3)
    >>> cache['A'] = 0
    >>> cache['B'] = 1
    >>> cache['C'] = 2
    >>> len(cache)
    3

    >>> cache['A']
    0

    Adding new items to the cache does not increase its size. Instead, the least
    recently used item is dropped:

    >>> cache['D'] = 3
    >>> len(cache)
    3
    >>> 'B' in cache
    False

    Iterating over the cache returns the keys, starting with the most recently
    used:

    >>> for key in cache:
    ...     print key
    D
    A
    C

    This code is based on the LRUCache class from Genshi which is based on
    `Myghty <http://www.myghty.org>`_'s LRUCache from ``myghtyutils.util``,
    written by Mike Bayer and released under the MIT license (Genshi uses the
    BSD License).
    """

    class _Item(object):
        def __init__(self, key, value):
            self.previous = self.next = None
            self.key = key
            self.value = value

        def __repr__(self):
            return repr(self.value)

    def __init__(self, capacity):
        self._dict = dict()
        self.capacity = capacity
        self.head = None
        self.tail = None

    def __contains__(self, key):
        return key in self._dict

    def __iter__(self):
        cur = self.head
        while cur:
            yield cur.key
            cur = cur.next

    def __len__(self):
        return len(self._dict)

    def __getitem__(self, key):
        item = self._dict[key]
        self._update_item(item)
        return item.value

    def __setitem__(self, key, value):
        item = self._dict.get(key)
        if item is None:
            item = self._Item(key, value)
            self._dict[key] = item
            self._insert_item(item)
        else:
            item.value = value
            self._update_item(item)
            self._manage_size()

    def __repr__(self):
        return repr(self._dict)

    def _insert_item(self, item):
        item.previous = None
        item.next = self.head
        if self.head is not None:
            self.head.previous = item
        else:
            self.tail = item
        self.head = item
        self._manage_size()

    def _manage_size(self):
        while len(self._dict) > self.capacity:
            del self._dict[self.tail.key]
            if self.tail != self.head:
                self.tail = self.tail.previous
                self.tail.next = None
            else:
                self.head = self.tail = None

    def _update_item(self, item):
        if self.head == item:
            return

        previous = item.previous
        previous.next = item.next
        if item.next is not None:
            item.next.previous = previous
        else:
            self.tail = previous

        item.previous = None
        item.next = self.head
        self.head.previous = self.head = item


