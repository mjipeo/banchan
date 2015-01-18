import re


def camel_to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def camel_to_hyphen(name):
    return underscore_to_hyphen(camel_to_underscore(name))


def underscore_to_camel(name):
    return ''.join([token.capitalize() for token in name.split('_')])


def underscore_to_hyphen(name):
    return re.sub('_', '-', name)


def hyphen_to_underscore(val):
    return re.sub('-', '_', val)


def pythonify(params):
    """Convert hyphenated-keys dict to underscored-keys dict.

    Mostly used to directly forward GET or POST params from HTTP request to
    python models.
    """
    return dict([(hyphen_to_underscore(k), v) for k, v in params.iteritems()])
