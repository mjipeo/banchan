from __future__ import absolute_import

import inspect

from django.utils import six


def getargspec(func):
    if six.PY2:
        return inspect.getargspec(func)

    sig = inspect.signature(func)
    args = [
        p.name for p in sig.parameters.values()
        if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]
    varargs = [
        p.name for p in sig.parameters.values()
        if p.kind == inspect.Parameter.VAR_POSITIONAL
    ]
    varargs = varargs[0] if varargs else None
    varkw = [
        p.name for p in sig.parameters.values()
        if p.kind == inspect.Parameter.VAR_KEYWORD
    ]
    varkw = varkw[0] if varkw else None
    defaults = [
        p.default for p in sig.parameters.values()
        if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and p.default is not p.empty
    ] or None
    return args, varargs, varkw, defaults


def get_func_args(func):
    if six.PY2:
        argspec = inspect.getargspec(func)
        return argspec.args[1:]  # ignore 'self'

    sig = inspect.signature(func)
    return [
        arg_name for arg_name, param in sig.parameters.items()
        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]


def get_func_full_args(func):
    """
    Return a list of (argument name, default value) tuples. If the argument
    does not have a default value, omit it in the tuple. Arguments such as
    *args and **kwargs are also included.
    """
    if six.PY2:
        argspec = inspect.getargspec(func)
        args = argspec.args[1:]  # ignore 'self'
        defaults = argspec.defaults or []
        # Split args into two lists depending on whether they have default value
        no_default = args[:len(args) - len(defaults)]
        with_default = args[len(args) - len(defaults):]
        # Join the two lists and combine it with default values
        args = [(arg,) for arg in no_default] + zip(with_default, defaults)
        # Add possible *args and **kwargs and prepend them with '*' or '**'
        varargs = [('*' + argspec.varargs,)] if argspec.varargs else []
        kwargs = [('**' + argspec.keywords,)] if argspec.keywords else []
        return args + varargs + kwargs

    sig = inspect.signature(func)
    args = []
    for arg_name, param in sig.parameters.items():
        name = arg_name
        # Ignore 'self'
        if name == 'self':
            continue
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            name = '*' + name
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            name = '**' + name
        if param.default != inspect.Parameter.empty:
            args.append((name, param.default))
        else:
            args.append((name,))
    return args


def func_accepts_kwargs(func):
    if six.PY2:
        # Not all callables are inspectable with getargspec, so we'll
        # try a couple different ways but in the end fall back on assuming
        # it is -- we don't want to prevent registration of valid but weird
        # callables.
        try:
            argspec = inspect.getargspec(func)
        except TypeError:
            try:
                argspec = inspect.getargspec(func.__call__)
            except (TypeError, AttributeError):
                argspec = None
        return not argspec or argspec[2] is not None

    return any(
        p for p in inspect.signature(func).parameters.values()
        if p.kind == p.VAR_KEYWORD
    )


def func_accepts_var_args(func):
    """
    Return True if function 'func' accepts positional arguments *args.
    """
    if six.PY2:
        return inspect.getargspec(func)[1] is not None

    return any(
        p for p in inspect.signature(func).parameters.values()
        if p.kind == p.VAR_POSITIONAL
    )


def func_has_no_args(func):
    args = inspect.getargspec(func)[0] if six.PY2 else [
        p for p in inspect.signature(func).parameters.values()
        if p.kind == p.POSITIONAL_OR_KEYWORD
    ]
    return len(args) == 1


def func_supports_parameter(func, parameter):
    if six.PY3:
        return parameter in inspect.signature(func).parameters
    else:
        args, varargs, varkw, defaults = inspect.getargspec(func)
        return parameter in args


def isclass(obj):
    """Is obj a class? Inspect's isclass is too liberal and returns True
    for objects that can't be subclasses of anything.
    """
    obj_type = type(obj)
    return obj_type in class_types or issubclass(obj_type, type)


# backwards compat (issue #64)
is_generator = isgenerator


def ispackage(path):
    """
    Is this path a package directory?

    >>> ispackage('nose')
    True
    >>> ispackage('unit_tests')
    False
    >>> ispackage('nose/plugins')
    True
    >>> ispackage('nose/loader.py')
    False
    """
    if os.path.isdir(path):
        # at least the end of the path must be a legal python identifier
        # and __init__.py[co] must exist
        end = os.path.basename(path)
        if ident_re.match(end):
            for init in ('__init__.py', '__init__.pyc', '__init__.pyo'):
                if os.path.isfile(os.path.join(path, init)):
                    return True
            if sys.platform.startswith('java') and \
                    os.path.isfile(os.path.join(path, '__init__$py.class')):
                return True
    return False


def isproperty(obj):
    """
    Is this a property?

    >>> class Foo:
    ...     def got(self):
    ...         return 2
    ...     def get(self):
    ...         return 1
    ...     get = property(get)

    >>> isproperty(Foo.got)
    False
    >>> isproperty(Foo.get)
    True
    """
    return type(obj) == property


def class_hierarchy(cls):
    """Return an unordered sequence of all classes related to cls.

    Traverses diamond hierarchies.

    Fibs slightly: subclasses of builtin types are not returned.  Thus
    class_hierarchy(class A(object)) returns (A, object), not A plus every
    class systemwide that derives from object.

    Old-style classes are discarded and hierarchies rooted on them
    will not be descended.

    """
    if compat.py2k:
        if isinstance(cls, types.ClassType):
            return list()

    hier = set([cls])
    process = list(cls.__mro__)
    while process:
        c = process.pop()
        if compat.py2k:
            if isinstance(c, types.ClassType):
                continue
            bases = (_ for _ in c.__bases__
                     if _ not in hier and not isinstance(_, types.ClassType))
        else:
            bases = (_ for _ in c.__bases__ if _ not in hier)

        for b in bases:
            process.append(b)
            hier.add(b)

        if compat.py3k:
            if c.__module__ == 'builtins' or not hasattr(c, '__subclasses__'):
                continue
        else:
            if c.__module__ == '__builtin__' or not hasattr(
                    c, '__subclasses__'):
                continue

        for s in [_ for _ in c.__subclasses__() if _ not in hier]:
            process.append(s)
            hier.add(s)
    return list(hier)


