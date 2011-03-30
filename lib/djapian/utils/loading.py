# Module taken from Turbion blog engine

import os
import imp

from django.utils.importlib import import_module

class NoModuleError(Exception):
    """
    Custom exception class indicates that given module does not exit at all
    """
    pass

def get_module(base, module_name):
    try:
        base_path = __import__(base, {}, {}, [base.split('.')[-1]]).__path__
    except AttributeError:
        raise NoModuleError("Cannot load base `%s`" % base)

    try:
        imp.find_module(module_name, base_path)
    except ImportError:
        raise NoModuleError("Cannot find module `%s` in base `%s`" % (module_name, base))

    return import_module('.%s' % module_name, base)
