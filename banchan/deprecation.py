def warn(msg, stacklevel=3):
    """Issue a warning."""
    if isinstance(msg, string_type):
        warnings.warn(msg, exceptions.BeakerWarning, stacklevel=stacklevel)
    else:
        warnings.warn(msg, stacklevel=stacklevel)


def deprecated(message):
    def wrapper(fn):
        def deprecated_method(*args, **kargs):
            warnings.warn(message, DeprecationWarning, 2)
            return fn(*args, **kargs)
        # TODO: use decorator ?  functools.wrapper ?
        deprecated_method.__name__ = fn.__name__
        deprecated_method.__doc__ = "%s\n\n%s" % (message, fn.__doc__)
        return deprecated_method
    return wrapper

##


def warn_deprecated(description=None, deprecation=None,
                    removal=None, alternative=None, stacklevel=2):
    ctx = {'description': description,
           'deprecation': deprecation, 'removal': removal,
           'alternative': alternative}
    if deprecation is not None:
        w = CPendingDeprecationWarning(PENDING_DEPRECATION_FMT.format(**ctx))
    else:
        w = CDeprecationWarning(DEPRECATION_FMT.format(**ctx))
    warnings.warn(w, stacklevel=stacklevel)


def deprecated(deprecation=None, removal=None,
               alternative=None, description=None):
    """Decorator for deprecated functions.

    A deprecation warning will be emitted when the function is called.

    :keyword deprecation: Version that marks first deprecation, if this
      argument is not set a ``PendingDeprecationWarning`` will be emitted
      instead.
    :keyword removal:  Future version when this feature will be removed.
    :keyword alternative:  Instructions for an alternative solution (if any).
    :keyword description: Description of what is being deprecated.

    """
    def _inner(fun):

        @wraps(fun)
        def __inner(*args, **kwargs):
            from .imports import qualname
            warn_deprecated(description=description or qualname(fun),
                            deprecation=deprecation,
                            removal=removal,
                            alternative=alternative,
                            stacklevel=3)
            return fun(*args, **kwargs)
        return __inner
    return _inner


def deprecated_property(deprecation=None, removal=None,
                        alternative=None, description=None):
    def _inner(fun):
        return _deprecated_property(
            fun, deprecation=deprecation, removal=removal,
            alternative=alternative, description=description or fun.__name__)
    return _inner


class _deprecated_property(object):

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, **depreinfo):
        self.__get = fget
        self.__set = fset
        self.__del = fdel
        self.__name__, self.__module__, self.__doc__ = (
            fget.__name__, fget.__module__, fget.__doc__,
        )
        self.depreinfo = depreinfo
        self.depreinfo.setdefault('stacklevel', 3)

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        warn_deprecated(**self.depreinfo)
        return self.__get(obj)

    def __set__(self, obj, value):
        if obj is None:
            return self
        if self.__set is None:
            raise AttributeError('cannot set attribute')
        warn_deprecated(**self.depreinfo)
        self.__set(obj, value)

    def __delete__(self, obj):
        if obj is None:
            return self
        if self.__del is None:
            raise AttributeError('cannot delete attribute')
        warn_deprecated(**self.depreinfo)
        self.__del(obj)

    def setter(self, fset):
        return self.__class__(self.__get, fset, self.__del, **self.depreinfo)

    def deleter(self, fdel):
        return self.__class__(self.__get, self.__set, fdel, **self.depreinfo)


##


# util/deprecations.py
# Copyright (C) 2005-2015 the SQLAlchemy authors and contributors
# <see AUTHORS file>
#
# This module is part of SQLAlchemy and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""Helpers related to deprecation of functions, methods, classes, other
functionality."""

from .. import exc
import warnings
import re
from .langhelpers import decorator


def warn_deprecated(msg, stacklevel=3):
    warnings.warn(msg, exc.SADeprecationWarning, stacklevel=stacklevel)


def warn_pending_deprecation(msg, stacklevel=3):
    warnings.warn(msg, exc.SAPendingDeprecationWarning, stacklevel=stacklevel)


def deprecated(version, message=None, add_deprecation_to_docstring=True):
    """Decorates a function and issues a deprecation warning on use.

    :param message:
      If provided, issue message in the warning.  A sensible default
      is used if not provided.

    :param add_deprecation_to_docstring:
      Default True.  If False, the wrapped function's __doc__ is left
      as-is.  If True, the 'message' is prepended to the docs if
      provided, or sensible default if message is omitted.

    """

    if add_deprecation_to_docstring:
        header = ".. deprecated:: %s %s" % \
            (version, (message or ''))
    else:
        header = None

    if message is None:
        message = "Call to deprecated function %(func)s"

    def decorate(fn):
        return _decorate_with_warning(
            fn, exc.SADeprecationWarning,
            message % dict(func=fn.__name__), header)
    return decorate


def pending_deprecation(version, message=None,
                        add_deprecation_to_docstring=True):
    """Decorates a function and issues a pending deprecation warning on use.

    :param version:
      An approximate future version at which point the pending deprecation
      will become deprecated.  Not used in messaging.

    :param message:
      If provided, issue message in the warning.  A sensible default
      is used if not provided.

    :param add_deprecation_to_docstring:
      Default True.  If False, the wrapped function's __doc__ is left
      as-is.  If True, the 'message' is prepended to the docs if
      provided, or sensible default if message is omitted.
    """

    if add_deprecation_to_docstring:
        header = ".. deprecated:: %s (pending) %s" % \
            (version, (message or ''))
    else:
        header = None

    if message is None:
        message = "Call to deprecated function %(func)s"

    def decorate(fn):
        return _decorate_with_warning(
            fn, exc.SAPendingDeprecationWarning,
            message % dict(func=fn.__name__), header)
    return decorate


def _sanitize_restructured_text(text):
    def repl(m):
        type_, name = m.group(1, 2)
        if type_ in ("func", "meth"):
            name += "()"
        return name
    return re.sub(r'\:(\w+)\:`~?\.?(.+?)`', repl, text)


def _decorate_with_warning(func, wtype, message, docstring_header=None):
    """Wrap a function with a warnings.warn and augmented docstring."""

    message = _sanitize_restructured_text(message)

    @decorator
    def warned(fn, *args, **kwargs):
        warnings.warn(message, wtype, stacklevel=3)
        return fn(*args, **kwargs)

    doc = func.__doc__ is not None and func.__doc__ or ''
    if docstring_header is not None:
        docstring_header %= dict(func=func.__name__)

        doc = inject_docstring_text(doc, docstring_header, 1)

    decorated = warned(func)
    decorated.__doc__ = doc
    return decorated

import textwrap


def _dedent_docstring(text):
    split_text = text.split("\n", 1)
    if len(split_text) == 1:
        return text
    else:
        firstline, remaining = split_text
    if not firstline.startswith(" "):
        return firstline + "\n" + textwrap.dedent(remaining)
    else:
        return textwrap.dedent(text)


def inject_docstring_text(doctext, injecttext, pos):
    doctext = _dedent_docstring(doctext or "")
    lines = doctext.split('\n')
    injectlines = textwrap.dedent(injecttext).split("\n")
    if injectlines[0]:
        injectlines.insert(0, "")

    blanks = [num for num, line in enumerate(lines) if not line.strip()]
    blanks.insert(0, 0)

    inject_pos = blanks[min(pos, len(blanks) - 1)]

    lines = lines[0:inject_pos] + injectlines + lines[inject_pos:]
    return "\n".join(lines)
