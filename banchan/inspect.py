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


##


def get_cls_kwargs(cls, _set=None):
    """Return the full set of inherited kwargs for the given `cls`.

    Probes a class's __init__ method, collecting all named arguments.  If the
    __init__ defines a \**kwargs catch-all, then the constructor is presumed
    to pass along unrecognized keywords to its base classes, and the
    collection process is repeated recursively on each of the bases.

    Uses a subset of inspect.getargspec() to cut down on method overhead.
    No anonymous tuple arguments please !

    """
    toplevel = _set is None
    if toplevel:
        _set = set()

    ctr = cls.__dict__.get('__init__', False)

    has_init = ctr and isinstance(ctr, types.FunctionType) and \
        isinstance(ctr.__code__, types.CodeType)

    if has_init:
        names, has_kw = inspect_func_args(ctr)
        _set.update(names)

        if not has_kw and not toplevel:
            return None

    if not has_init or has_kw:
        for c in cls.__bases__:
            if get_cls_kwargs(c, _set) is None:
                break

    _set.discard('self')
    return _set


try:
    # TODO: who doesn't have this constant?
    from inspect import CO_VARKEYWORDS

    def inspect_func_args(fn):
        co = fn.__code__
        nargs = co.co_argcount
        names = co.co_varnames
        args = list(names[:nargs])
        has_kw = bool(co.co_flags & CO_VARKEYWORDS)
        return args, has_kw

except ImportError:
    def inspect_func_args(fn):
        names, _, has_kw, _ = inspect.getargspec(fn)
        return names, bool(has_kw)


def get_func_kwargs(func):
    """Return the set of legal kwargs for the given `func`.

    Uses getargspec so is safe to call for methods, functions,
    etc.

    """

    return compat.inspect_getargspec(func)[0]


def get_callable_argspec(fn, no_self=False, _is_init=False):
    """Return the argument signature for any callable.

    All pure-Python callables are accepted, including
    functions, methods, classes, objects with __call__;
    builtins and other edge cases like functools.partial() objects
    raise a TypeError.

    """
    if inspect.isbuiltin(fn):
        raise TypeError("Can't inspect builtin: %s" % fn)
    elif inspect.isfunction(fn):
        if _is_init and no_self:
            spec = compat.inspect_getargspec(fn)
            return compat.ArgSpec(spec.args[1:], spec.varargs,
                                  spec.keywords, spec.defaults)
        else:
            return compat.inspect_getargspec(fn)
    elif inspect.ismethod(fn):
        if no_self and (_is_init or fn.__self__):
            spec = compat.inspect_getargspec(fn.__func__)
            return compat.ArgSpec(spec.args[1:], spec.varargs,
                                  spec.keywords, spec.defaults)
        else:
            return compat.inspect_getargspec(fn.__func__)
    elif inspect.isclass(fn):
        return get_callable_argspec(
            fn.__init__, no_self=no_self, _is_init=True)
    elif hasattr(fn, '__func__'):
        return compat.inspect_getargspec(fn.__func__)
    elif hasattr(fn, '__call__'):
        if inspect.ismethod(fn.__call__):
            return get_callable_argspec(fn.__call__, no_self=no_self)
        else:
            raise TypeError("Can't inspect callable: %s" % fn)
    else:
        raise TypeError("Can't inspect callable: %s" % fn)


def format_argspec_plus(fn, grouped=True):
    """Returns a dictionary of formatted, introspected function arguments.

    A enhanced variant of inspect.formatargspec to support code generation.

    fn
       An inspectable callable or tuple of inspect getargspec() results.
    grouped
      Defaults to True; include (parens, around, argument) lists

    Returns:

    args
      Full inspect.formatargspec for fn
    self_arg
      The name of the first positional argument, varargs[0], or None
      if the function defines no positional arguments.
    apply_pos
      args, re-written in calling rather than receiving syntax.  Arguments are
      passed positionally.
    apply_kw
      Like apply_pos, except keyword-ish args are passed as keywords.

    Example::

      >>> format_argspec_plus(lambda self, a, b, c=3, **d: 123)
      {'args': '(self, a, b, c=3, **d)',
       'self_arg': 'self',
       'apply_kw': '(self, a, b, c=c, **d)',
       'apply_pos': '(self, a, b, c, **d)'}

    """
    if compat.callable(fn):
        spec = compat.inspect_getfullargspec(fn)
    else:
        # we accept an existing argspec...
        spec = fn
    args = inspect.formatargspec(*spec)
    if spec[0]:
        self_arg = spec[0][0]
    elif spec[1]:
        self_arg = '%s[0]' % spec[1]
    else:
        self_arg = None

    if compat.py3k:
        apply_pos = inspect.formatargspec(spec[0], spec[1],
                                          spec[2], None, spec[4])
        num_defaults = 0
        if spec[3]:
            num_defaults += len(spec[3])
        if spec[4]:
            num_defaults += len(spec[4])
        name_args = spec[0] + spec[4]
    else:
        apply_pos = inspect.formatargspec(spec[0], spec[1], spec[2])
        num_defaults = 0
        if spec[3]:
            num_defaults += len(spec[3])
        name_args = spec[0]

    if num_defaults:
        defaulted_vals = name_args[0 - num_defaults:]
    else:
        defaulted_vals = ()

    apply_kw = inspect.formatargspec(name_args, spec[1], spec[2],
                                     defaulted_vals,
                                     formatvalue=lambda x: '=' + x)
    if grouped:
        return dict(args=args, self_arg=self_arg,
                    apply_pos=apply_pos, apply_kw=apply_kw)
    else:
        return dict(args=args[1:-1], self_arg=self_arg,
                    apply_pos=apply_pos[1:-1], apply_kw=apply_kw[1:-1])


def format_argspec_init(method, grouped=True):
    """format_argspec_plus with considerations for typical __init__ methods

    Wraps format_argspec_plus with error handling strategies for typical
    __init__ cases::

      object.__init__ -> (self)
      other unreflectable (usually C) -> (self, *args, **kwargs)

    """
    if method is object.__init__:
        args = grouped and '(self)' or 'self'
    else:
        try:
            return format_argspec_plus(method, grouped=grouped)
        except TypeError:
            args = (grouped and '(self, *args, **kwargs)'
                    or 'self, *args, **kwargs')
    return dict(self_arg='self', args=args, apply_pos=args, apply_kw=args)


def getargspec_init(method):
    """inspect.getargspec with considerations for typical __init__ methods

    Wraps inspect.getargspec with error handling for typical __init__ cases::

      object.__init__ -> (self)
      other unreflectable (usually C) -> (self, *args, **kwargs)

    """
    try:
        return inspect.getargspec(method)
    except TypeError:
        if method is object.__init__:
            return (['self'], None, None, None)
        else:
            return (['self'], 'args', 'kwargs', None)


def unbound_method_to_callable(func_or_cls):
    """Adjust the incoming callable such that a 'self' argument is not
    required.

    """

    if isinstance(func_or_cls, types.MethodType) and not func_or_cls.__self__:
        return func_or_cls.__func__
    else:
        return func_or_cls


def generic_repr(obj, additional_kw=(), to_inspect=None, omit_kwarg=()):
    """Produce a __repr__() based on direct association of the __init__()
    specification vs. same-named attributes present.

    """
    if to_inspect is None:
        to_inspect = [obj]
    else:
        to_inspect = _collections.to_list(to_inspect)

    missing = object()

    pos_args = []
    kw_args = _collections.OrderedDict()
    vargs = None
    for i, insp in enumerate(to_inspect):
        try:
            (_args, _vargs, vkw, defaults) = \
                inspect.getargspec(insp.__init__)
        except TypeError:
            continue
        else:
            default_len = defaults and len(defaults) or 0
            if i == 0:
                if _vargs:
                    vargs = _vargs
                if default_len:
                    pos_args.extend(_args[1:-default_len])
                else:
                    pos_args.extend(_args[1:])
            else:
                kw_args.update([
                    (arg, missing) for arg in _args[1:-default_len]
                ])

            if default_len:
                kw_args.update([
                    (arg, default)
                    for arg, default
                    in zip(_args[-default_len:], defaults)
                ])
    output = []

    output.extend(repr(getattr(obj, arg, None)) for arg in pos_args)

    if vargs is not None and hasattr(obj, vargs):
        output.extend([repr(val) for val in getattr(obj, vargs)])

    for arg, defval in kw_args.items():
        if arg in omit_kwarg:
            continue
        try:
            val = getattr(obj, arg, missing)
            if val is not missing and val != defval:
                output.append('%s=%r' % (arg, val))
        except Exception:
            pass

    if additional_kw:
        for arg, defval in additional_kw:
            try:
                val = getattr(obj, arg, missing)
                if val is not missing and val != defval:
                    output.append('%s=%r' % (arg, val))
            except Exception:
                pass

    return "%s(%s)" % (obj.__class__.__name__, ", ".join(output))


class portable_instancemethod(object):
    """Turn an instancemethod into a (parent, name) pair
    to produce a serializable callable.

    """

    __slots__ = 'target', 'name', '__weakref__'

    def __getstate__(self):
        return {'target': self.target, 'name': self.name}

    def __setstate__(self, state):
        self.target = state['target']
        self.name = state['name']

    def __init__(self, meth):
        self.target = meth.__self__
        self.name = meth.__name__

    def __call__(self, *arg, **kw):
        return getattr(self.target, self.name)(*arg, **kw)


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


def iterate_attributes(cls):
    """iterate all the keys and attributes associated
       with a class, without using getattr().

       Does not use getattr() so that class-sensitive
       descriptors (i.e. property.__get__()) are not called.

    """
    keys = dir(cls)
    for key in keys:
        for c in cls.__mro__:
            if key in c.__dict__:
                yield (key, c.__dict__[key])
                break


def isdescriptor(x):
    """Check if the object is some kind of descriptor."""
    for item in '__get__', '__set__', '__delete__':
        if hasattr(safe_getattr(x, item, None), '__call__'):
            return True
    return False


def safe_getattr(obj, name, *defargs):
    """A getattr() that turns all exceptions into AttributeErrors."""
    try:
        return getattr(obj, name, *defargs)
    except Exception:
        # this is a catch-all for all the weird things that some modules do
        # with attribute access
        if defargs:
            return defargs[0]
        raise AttributeError(name)


def safe_getmembers(object, predicate=None, attr_getter=safe_getattr):
    """A version of inspect.getmembers() that uses safe_getattr()."""
    results = []
    for key in dir(object):
        try:
            value = attr_getter(object, key, None)
        except AttributeError:
            continue
        if not predicate or predicate(value):
            results.append((key, value))
    results.sort()
    return results


def object_description(object):
    """A repr() implementation that returns text safe to use in reST context."""
    try:
        s = repr(object)
    except Exception:
        raise ValueError
    if isinstance(s, binary_type):
        s = force_decode(s, None)
    # Strip non-deterministic memory addresses such as
    # ``<__main__.A at 0x7f68cb685710>``
    s = memory_address_re.sub('', s)
    return s.replace('\n', ' ')


def is_builtin_class_method(obj, attr_name):
    """If attr_name is implemented at builtin class, return True.

        >>> is_builtin_class_method(int, '__init__')
        True

    Why this function needed? CPython implements int.__init__ by Descriptor
    but PyPy implements it by pure Python code.
    """
    classes = [c for c in inspect.getmro(obj) if attr_name in c.__dict__]
    cls = classes[0] if classes else object

    if not hasattr(builtins, safe_getattr(cls, '__name__', '')):
        return False
    return getattr(builtins, safe_getattr(cls, '__name__', '')) is cls
