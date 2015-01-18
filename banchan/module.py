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
