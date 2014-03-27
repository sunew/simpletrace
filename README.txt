.. contents::

simpletrace
===========

Decorators and function for tracing individual function/method calls, or all methods of a class / functions of a module.

To trace the calls of a mehod or function:

    from simpletrace import echo

    @echo
    def myfunc(self):
        ...

To trace all methods of a class, put the following in your own module:

    from mymodule import MyClass
    from simpletrace import echo_class
    echo_class(MyClass)

Likewise for tracing an entire module (todo: but we need to filter away imports...):

    import mymodule
    from simpletrace import echo_module
    echo_module(mymodule)

Also works with properties:

    @property
    @echo
    def placesAvailable(self):
        ...
