import imp
import sys
from importlib import import_module


def import_by_path(dotted_path, error_prefix=''):
    """Import a dotted module path and return the attribute/class designated
    by the last name in the path. Raise ImproperlyConfigured if something goes
    wrong.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        raise Exception('%s%s doesn\'t look like a module path' % (
            error_prefix, dotted_path))
    try:
        module = import_module(module_path)
    except ImportError:
        raise Exception('Failed to import %s' % (module_path,))

    try:
        attr = getattr(module, class_name)
    except AttributeError:
        raise Exception('%sModule "%s" does not define a "%s" attribute/class'
                        % (error_prefix, module_path, class_name))
    return attr


# TODO: file-version


def import_temporary_module_by_code(code, name='_dynamic', add_to_sys=False):
    """Tentatively import source code as a module."""
    module = imp.new_module(name)

    exec code in module.__dict__

    if add_to_sys:
        sys.modules[name] = module

    return module


def find_class(module_name, class_name=None):
    if class_name:
        module_name = "%s.%s" % (module_name, class_name)
    modules = module_name.split('.')
    c = None

    try:
        for m in modules[1:]:
            if c:
                c = getattr(c, m)
            else:
                c = getattr(__import__(".".join(modules[0:-1])), m)
        return c
    except:
        return None


def import_string(import_name, silent=False):
    """Imports an object based on a string.  This is useful if you want to
    use import paths as endpoints or something similar.  An import path can
    be specified either in dotted notation (``xml.sax.saxutils.escape``)
    or with a colon as object delimiter (``xml.sax.saxutils:escape``).

    If the `silent` is True the return value will be `None` if the import
    fails.

    :return: imported object
    """
    try:
        if ':' in import_name:
            module, obj = import_name.split(':', 1)
        elif '.' in import_name:
            items = import_name.split('.')
            module = '.'.join(items[:-1])
            obj = items[-1]
        else:
            return __import__(import_name)
        return getattr(__import__(module, None, None, [obj]), obj)
    except (ImportError, AttributeError):
        if not silent:
            raise


def import_or_raise(pkg_or_module_string, ExceptionType, *args, **kwargs):
    try:
        return __import__(pkg_or_module_string)
    except ImportError:
        raise ExceptionType(*args, **kwargs)


def import_object(name):
    """Imports an object by name.

    import_object('x') is equivalent to 'import x'.
    import_object('x.y.z') is equivalent to 'from x.y import z'.

    >>> import tornado.escape
    >>> import_object('tornado.escape') is tornado.escape
    True
    >>> import_object('tornado.escape.utf8') is tornado.escape.utf8
    True
    >>> import_object('tornado') is tornado
    True
    >>> import_object('tornado.missing_module')
    Traceback (most recent call last):
        ...
    ImportError: No module named missing_module
    """
    if isinstance(name, unicode_type) and str is not unicode_type:
        # On python 2 a byte string is required.
        name = name.encode('utf-8')
    if name.count('.') == 0:
        return __import__(name, None, None)

    parts = name.split('.')
    obj = __import__('.'.join(parts[:-1]), None, None, [parts[-1]], 0)
    try:
        return getattr(obj, parts[-1])
    except AttributeError:
        raise ImportError("No module named %s" % parts[-1])
