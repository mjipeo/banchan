import collections


def convert_to_byte(data, encoding='utf-8'):
    if isinstance(data, basestring):
        return data.encode(encoding) if isinstance(data, unicode) else \
               data
    elif isinstance(data, collections.Mapping):
        return dict(map(convert_to_byte, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert_to_byte, data))
    else:
        return data


def truncate(value, size=80):
    return value[:size]


def compact(things):
    if isinstance(things, basestring):
        return _compact(things)
    elif isinstance(things, (tuple, list)):
        return [_compact(thing) for thing in things if _compact(thing)]
    else:
        raise Exception('Unsupported type')


def _compact(thing):
    if isinstance(thing, basestring):
        return re.sub(r'\s+', ' ', thing.strip())
    return thing
