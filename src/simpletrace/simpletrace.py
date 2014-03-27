# the echo stuff is from http://wordaligned.org/articles/echo
# see also profilehooks

import inspect
import sys
import threading
from types import FunctionType

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

def method_name(method):
    """ Return a method's name.

    This function returns the name the method is accessed by from
    outside the class (i.e. it prefixes "private" methods appropriately).
    """
    mname = get_name(method)
    if is_class_private_name(mname):
        mname = "_%s%s" % (get_name(method.im_class), mname)
    return mname

def format_arg_value(arg_val):
    """ Return a string representing a (name, value) pair.

    >>> format_arg_value(('x', (1, 2, 3)))
    'x=(1, 2, 3)'
    """
    arg, val = arg_val
    return "%s = %r" % (arg, val)

def echo(fn, write=sys.stdout.write):
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
        # Collect function arguments by chaining together positional,
        # defaulted, extra positional and keyword arguments.
        global echo_indent
        positional = map(format_arg_value, zip(argnames, v))
        defaulted = [format_arg_value((a, argdefs[a]))
                     for a in argnames[len(v):] if a not in k]
        nameless = map(repr, v[argcount:])
        keyword = map(format_arg_value, k.items())
        args = positional + defaulted + nameless + keyword
        # we assume this always hold:
        classname = get_classname(fn)
        if not classname:
            if argnames[0] == 'self':
                instance = v[0]
                classname = instance.__class__.__name__

        indent = echo_indent.indent() * "    "
        write("%(indent)sTRACE: %(module)s.%(classname)s.\033[1m%(name)s\033[22m%(args)s\n\n" % (
                    {'indent': indent,
                     'module': get_modulename(fn),
                     'classname': classname,
                     'name': get_name(fn),
                     'args': ("\n" + indent + "    ").join(['']+args)
                    }))
        result = fn(*v, **k)
        echo_indent.dedent()
        return result
    return wrapped

def echo_instancemethod(klass, method, write=sys.stdout.write):
    """ Change an instancemethod so that calls to it are echoed.

    Replacing a classmethod is a little more tricky.
    See: http://www.python.org/doc/current/ref/types.html
    """
    mname = method_name(method)
    never_echo = "__str__", "__repr__", # Avoid recursion printing method calls
    if mname in never_echo:
        pass
    elif is_classmethod(method):
        if hasattr(method.im_func, 'func_code'):
            setattr(klass, mname, classmethod(echo(method.im_func, write)))
    else:
        if hasattr(method, 'func_code'):
            setattr(klass, mname, echo(method, write))

def echo_class(klass, write=sys.stdout.write):
    """ Echo calls to class methods and static functions
    """
    for _, method in inspect.getmembers(klass, inspect.ismethod):
        echo_instancemethod(klass, method, write)
    for _, fn in inspect.getmembers(klass, inspect.isfunction):
        setattr(klass, get_name(fn), staticmethod(echo(fn, write)))
    for _, prop in inspect.getmembers(klass, lambda member: type(member) == property):
        if type(prop.fget) == FunctionType and hasattr(prop.fget, '__name__'):
            setattr(klass, prop.fget.__name__, property(echo(prop.fget, write), prop.fset, prop.fdel))

def echo_module(mod, write=sys.stdout.write):
    """ Echo calls to functions and methods in a module.
    """
    for fname, fn in inspect.getmembers(mod, inspect.isfunction):
        setattr(mod, fname, echo(fn, write))
    for _, klass in inspect.getmembers(mod, inspect.isclass):
        echo_class(klass, write)