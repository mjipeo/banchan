from collections import defaultdict
import heapq
import re
import string

try:
    import datrie
except ImportError:
    pass


recursive_dict = lambda: defaultdict(recursive_dict)


class AttributeDict(dict):
    """Accessing dict values via attributes."""

    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            raise AttributeError


# For consistency with Python built-in naming (e.g. defaultdict)
attrdict = AttributeDict


def pick(d, *args):
    keys = args
    if len(keys) == 1 and isinstance(keys[0], (list, tuple)):
        # Allow `pick(d, ['key1', 'key2'])` as well
        keys = keys[0]
    keys = set(keys)
    return dict([(k, v) for k, v in d.iteritems() if k in keys])

def updated(*args):
    data = {}
    for d in args:
        data.update(d)
    return data


# Computation
# -----------

def permutation(source, index=0):
    if index == len(source) - 1:
        return [[target] for target in source[index]]
    perms = []
    for perm in permutation(source, index + 1):
        for target in source[index]:
            perms.append([target] + perm)
    return perms


class MutableHashHeap(object):
    """A heap data structure which supports updating of value. """

    def __init__(self):
        self._heap = []
        self._dict = {}

    @property
    def is_empty(self):
        return not bool(self._heap)

    @property
    def top(self):
        if self._heap:
            priority, key, entry = self._heap[0]
            return key, entry, priority
        else:
            return None, None, None

    def has_key(self, key):
        return self._dict.has_key(key)

    def push(self, key, entry, priority=1):
        e = [priority, key, entry]
        heapq.heappush(self._heap, e)
        self._dict[key] = e

    def pop(self):
        priority, key, entry = heapq.heappop(self._heap)
        del self._dict[key]
        return key, entry, priority

    def update_priority(self, key, priority):
        self._dict[key][0] = priority
        heapq.heapify(self._heap)

    def push_or_update(self, key, entry, priority):
        if self.has_key(key):
            self.update_priority(key, priority)
        else:
            self.push(key, entry, priority)


class PrefixQueue(object):
    DEFAULT_ALPHABET = string.ascii_lowercase + string.digits + '.-_ '

    def __init__(self, alphabet=DEFAULT_ALPHABET):
        self._alphabet = alphabet
        self._trie = datrie.Trie(alphabet)
        self._count = 0

    def __len__(self):
        return self._count

    @property
    def length(self):
        """Uncached version of __len__"""
        return sum([len(queue) for queue in self._trie.values()])

    def normalize_key(self, key):
        return unicode(re.sub(r'[^{0}]'.format(self._alphabet), ' ', key))

    def keys(self):
        return self._trie.keys()

    def push(self, key, value):
        key = self.normalize_key(key)
        try:
            queue = self._trie[key]
        except KeyError:
            self._trie[key] = [value]
        else:
            queue.append(value)
        self._count += 1

    def pop_from_queue_of_longest_prefix(self, key, checker=lambda x: True):
        key = self.normalize_key(key)
        checked = set()

        for length in reversed(range(len(key) + 1)):
            prefix = key[:length]
            candidates = set(self._trie.keys(prefix)).difference(checked)
            for key in candidates:
                queue = self._trie[key]
                for i, value in enumerate(queue):
                    if checker(value):
                        queue.pop(i)
                        if not queue:
                            del self._trie[key]
                        self._count -= 1
                        return value
            checked.update(candidates)

        return None

    pop = pop_from_queue_of_longest_prefix
