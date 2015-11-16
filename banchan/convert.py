def boolean(value):
    val = str(value)
    if val.lower() in ['true', 't', 'y', '1', 'yes']:
        return True
    else:
        return False

# (c) 2005 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
def asbool(obj):
    if isinstance(obj, string_type):
        obj = obj.strip().lower()
        if obj in ['true', 'yes', 'on', 'y', 't', '1']:
            return True
        elif obj in ['false', 'no', 'off', 'n', 'f', '0']:
            return False
        else:
            raise ValueError(
                "String is not true/false: %r" % obj)
    return bool(obj)


def aslist(obj, sep=None, strip=True):
    if isinstance(obj, string_type):
        lst = obj.split(sep)
        if strip:
            lst = [v.strip() for v in lst]
        return lst
    elif isinstance(obj, (list, tuple)):
        return obj
    elif obj is None:
        return []
    else:
        return [obj]


def asint(obj):
    if isinstance(obj, int):
        return obj
    elif isinstance(obj, string_type) and re.match(r'^\d+$', obj):
        return int(obj)
    else:
        raise Exception("This is not a proper int")


def strtobool(term, table={'false': False, 'no': False, '0': False,
                           'true': True, 'yes': True, '1': True,
                           'on': True, 'off': False}):
    """Convert common terms for true/false to bool
    (true/false/yes/no/on/off/1/0)."""
    if isinstance(term, string_t):
        try:
            return table[term.lower()]
        except KeyError:
            raise TypeError('Cannot coerce {0!r} to type bool'.format(term))
    return term


def integer(value):
    try:
        return int(value)
    except (ValueError, OverflowError):
        return long(value) # why does this help ValueError? (CM)

TRUTHY_STRINGS = ('yes', 'true', 'on', '1')
FALSY_STRINGS  = ('no', 'false', 'off', '0')

def boolean(s):
    """Convert a string value to a boolean value."""
    ss = str(s).lower()
    if ss in TRUTHY_STRINGS:
        return True
    elif ss in FALSY_STRINGS:
        return False
    else:
        raise ValueError("not a valid boolean value: " + repr(s))
