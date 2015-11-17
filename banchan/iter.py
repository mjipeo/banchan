def distinct(iterable):
    """Yield all items in an iterable collection that are distinct.

    Unlike when using sets for a similar effect, the original ordering of the
    items in the collection is preserved by this function.

    >>> print list(distinct([1, 2, 1, 3, 4, 4]))
    [1, 2, 3, 4]
    >>> print list(distinct('foobar'))
    ['f', 'o', 'b', 'a', 'r']

    :param iterable: the iterable collection providing the data
    """
    seen = set()
    for item in iter(iterable):
        if item not in seen:
            yield item
            seen.add(item)


def is_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    return True


def flatten(fields):
    """Returns a list which is a single level of flattening of the
    original list."""
    flat = []
    for field in fields:
        if isinstance(field, (list, tuple)):
            flat.extend(field)
        else:
            flat.append(field)
    return flat


def shufflecycle(it):
    it = list(it)  # don't modify callers list
    shuffle = random.shuffle
    for _ in repeat(None):
        shuffle(it)
        yield it[0]


def iter_slices(string, slice_length):
    """Iterate over slices of a string."""
    pos = 0
    while pos < len(string):
        yield string[pos:pos + slice_length]
        pos += slice_length


def list_of_strings(arg):
    if not arg:
        return []
    try:
        return [x.strip() for x in arg.split(',')]
    except:
        raise ValueError("not a valid list of strings: " + repr(arg))

def list_of_ints(arg):
    if not arg:
        return []
    else:
        try:
            return list(map(int, arg.split(",")))
        except:
            raise ValueError("not a valid list of ints: " + repr(arg))

def list_of_exitcodes(arg):
    try:
        vals = list_of_ints(arg)
        for val in vals:
            if (val > 255) or (val < 0):
                raise ValueError('Invalid exit code "%s"' % val)
        return vals
    except:
        raise ValueError("not a valid list of exit codes: " + repr(arg))


def iter_multi_items(mapping):
    """Iterates over the items of a mapping yielding keys and values
    without dropping any from more complex structures.
    """
    if isinstance(mapping, MultiDict):
        for item in iteritems(mapping, multi=True):
            yield item
    elif isinstance(mapping, dict):
        for key, value in iteritems(mapping):
            if isinstance(value, (tuple, list)):
                for value in value:
                    yield key, value
            else:
                yield key, value
    else:
        for item in mapping:
            yield item


def _compat_rl_partition(S, sep, direction=None):
    if direction is None:
        direction = S.split
    items = direction(sep, 1)
    if len(items) == 1:
        return items[0], sep, ''
    return items[0], sep, items[1]


def _compat_partition(S, sep):
    """``partition(S, sep) -> (head, sep, tail)``
    Search for the separator ``sep`` in ``S``, and return the part before
    it, the separator itself, and the part after it. If the separator is not
    found, return ``S`` and two empty strings.
    """
    return _compat_rl_partition(S, sep, direction=S.split)


def _compat_rpartition(S, sep):
    """``rpartition(S, sep) -> (tail, sep, head)``
    Search for the separator ``sep`` in ``S``, starting at the end of ``S``,
    and return the part before it, the separator itself, and the part
    after it. If the separator is not found, return two empty
    strings and ``S``.
    """
    return _compat_rl_partition(S, sep, direction=S.rsplit)



def partition(S, sep):
    if hasattr(S, 'partition'):
        return S.partition(sep)
    else:  # Python <= 2.4:
        return _compat_partition(S, sep)


def rpartition(S, sep):
    if hasattr(S, 'rpartition'):
        return S.rpartition(sep)
    else:  # Python <= 2.4:
        return _compat_rpartition(S, sep)


def repeatlast(it):
    """Iterate over all elements in the iterator, and when its exhausted
    yield the last value infinitely."""
    for item in it:
        yield item
    while 1: # pragma: no cover
        yield item


def consume(iterable):
    """Consumes an iterable without doing anything with it."""
    for event in iterable:
        pass
