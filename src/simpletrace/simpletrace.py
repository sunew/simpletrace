# the echo stuff is from http://wordaligned.org/articles/echo
# see also profilehooks

import inspect
import sys
import threading
from types import FunctionType

blacklist = ['__parent__', '__str__', '__repr__']

# the global counter stuff is from:
# http://stackoverflow.com/questions/12479574/python-global-counter
class IndentCounter(object):
    def __init__(self):
        self.cur_indentation = 0
        self.lock = threading.Lock()
    def indent(self):
        with self.lock:
            result = self.cur_indentation
            self.cur_indentation += 1
        return result
    def dedent(self):
        with self.lock:
            result = self.cur_indentation
            self.cur_indentation -= 1
        return result

echo_indent = IndentCounter()

def get_name(item):
    ""
    return item.__name__

def get_modulename(item):
    ""
    if hasattr(item, 'im_class'):
        return item.im_class.__module__
    elif hasattr(item, '__module__'):
        return item.__module__
    else:
        # unknown module - todo: expand.
        return ''

def get_classname(item):
    ""
    if hasattr(item, 'im_class'):
        return item.im_class.__name__
    else:
        return ''

def is_classmethod(instancemethod):
    " Determine if an instancemethod is a classmethod. "
    return instancemethod.im_self is not None

def is_class_private_name(name):
    " Determine if a name is a class private name. "
    # Exclude system defined names such as __init__, __add__ etc
    return name.startswith("__") and not name.endswith("__")

def format_arg_value(arg_val):
    """ Return a string representing a (name, value) pair.

    >>> format_arg_value(('x', (1, 2, 3)))
    'x=(1, 2, 3)'
    """
    arg, val = arg_val
    return "%s = %r" % (arg, val)

def echo(fn, name=None, class_name=None, write=sys.stdout.write):
    """ Echo calls to a function.

    Returns a decorated version of the input function which "echoes" calls
    made to it by writing out the function's name and the arguments it was
    called with.
    """
    import functools
    # Unpack function's arg count, arg names, arg defaults
    code = fn.func_code
    argcount = code.co_argcount
    argnames = code.co_varnames[:argcount]
    fn_defaults = fn.func_defaults or list()
    argdefs = dict(zip(argnames[-len(fn_defaults):], fn_defaults))

    @functools.wraps(fn)
    def wrapped(*v, **k):
        global echo_indent

        # Collect function arguments by chaining together positional,
        # defaulted, extra positional and keyword arguments.
        positional = map(format_arg_value, zip(argnames, v))
        defaulted = [format_arg_value((a, argdefs[a]))
                     for a in argnames[len(v):] if a not in k]
        nameless = map(repr, v[argcount:])
        keyword = map(format_arg_value, k.items())
        args = positional + defaulted + nameless + keyword

        indent = echo_indent.indent() * "    "
        write("%(indent)sTRACE: %(module)s.%(classname)s.\033[1m%(name)s\033[22m (%(actual_name)s)%(args)s\n\n" % (
                    {'indent': indent,
                     'module': get_modulename(fn),
                     'classname': class_name or get_classname(fn),
                     'name': name or get_name(fn),
                     'actual_name': get_name(fn),
                     'args': ("\n" + indent + "    ").join(['']+args)
                    }))
        result = fn(*v, **k)
        echo_indent.dedent()
        return result
    return wrapped

def echo_instancemethod(klass, method, name, write=sys.stdout.write):
    """ Change an instancemethod so that calls to it are echoed.

    Replacing a classmethod is a little more tricky.
    See: http://www.python.org/doc/current/ref/types.html
    """
    class_name = klass.__name__
    if name in blacklist:
        pass
    elif is_classmethod(method):
        if hasattr(method.im_func, 'func_code'):
            setattr(klass, name, classmethod(
                    echo(method.im_func, name, class_name, write)))
    else:
        if hasattr(method, 'func_code'):
            setattr(klass, name,
                    echo(method, name, class_name, write))

def echo_class(klass, write=sys.stdout.write):
    """ Echo calls to class methods and static functions
    """
    class_name = klass.__name__
    for name, method in inspect.getmembers(klass, inspect.ismethod):
        echo_instancemethod(klass, method, name, write)
    for name, fn in inspect.getmembers(klass, inspect.isfunction):
        if name not in blacklist:
            setattr(klass, name, staticmethod(
                    echo(fn, name, class_name, write)))
    for name, prop in inspect.getmembers(klass, lambda member: type(member) == property):
        if type(prop.fget) == FunctionType and \
           name not in blacklist:
            setattr(klass, name,
                    property(echo(prop.fget, name, class_name, write),
                             prop.fset, prop.fdel))

def echo_module(mod, write=sys.stdout.write):
    """ Echo calls to functions and methods in a module.
    """
    # todo: exclude imports somehow?
    for fname, fn in inspect.getmembers(mod, inspect.isfunction):
        setattr(mod, fname, echo(fn, fname, write=write))
    for _, klass in inspect.getmembers(mod, inspect.isclass):
        echo_class(klass, write=write)