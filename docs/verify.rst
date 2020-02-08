=====================================
 Verifying interface implementations
=====================================

The ``zope.interface.verify`` module provides functions that test whether a
given interface is implemented by a class or provided by an object.

.. currentmodule:: zope.interface.verify

Verifying objects
=================

.. autofunction:: verifyObject

.. autoexception:: zope.interface.Invalid

Testing for attributes
----------------------

Attributes of the object, be they defined by its class or added by its
``__init__`` method, will be recognized:

.. doctest::

   >>> from zope.interface import Interface, Attribute, implementer
   >>> from zope.interface import Invalid
   >>> class IFoo(Interface):
   ...     x = Attribute("The X attribute")
   ...     y = Attribute("The Y attribute")

   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     x = 1
   ...     def __init__(self):
   ...         self.y = 2

   >>> from zope.interface.verify import verifyObject
   >>> verifyObject(IFoo, Foo())
   True

If either attribute is missing, verification will fail by raising an
exception. (We'll define a helper to make this easier to show.)

.. doctest::

   >>> def verify_foo():
   ...    foo = Foo()
   ...    try:
   ...        return verifyObject(IFoo, foo)
   ...    except Invalid as e:
   ...        print(e)

   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     x = 1
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <InterfaceClass ...IFoo>: The IFoo.y attribute was not provided.
   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     def __init__(self):
   ...         self.y = 2
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <InterfaceClass ...IFoo>: The IFoo.x attribute was not provided.

If both attributes are missing, an exception is raised reporting
both errors.

.. doctest::

    >>> @implementer(IFoo)
    ... class Foo(object):
    ...     pass
    >>> verify_foo()
    The object <Foo ...> has failed to implement interface <InterfaceClass ...IFoo>:
        The IFoo.x attribute was not provided
        The IFoo.y attribute was not provided

If an attribute is implemented as a property that raises an ``AttributeError``
when trying to get its value, the attribute is considered missing:

.. doctest::

   >>> class IFoo(Interface):
   ...     x = Attribute('The X attribute')
   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     @property
   ...     def x(self):
   ...         raise AttributeError
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <InterfaceClass ...IFoo>: The IFoo.x attribute was not provided.


Any other exception raised by a property will propagate to the caller of
``verifyObject``:

.. doctest::

   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     @property
   ...     def x(self):
   ...         raise Exception
   >>> verify_foo()
   Traceback (most recent call last):
   Exception

Of course, broken properties that are not required by the interface don't do
any harm:

.. doctest::

   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     x = 1
   ...     @property
   ...     def y(self):
   ...         raise Exception
   >>> verify_foo()
   True


Testing For Methods
-------------------

Methods are also validated to exist. We'll start by defining a method
that takes one argument. If we don't provide it, we get an error.

.. doctest::

   >>> class IFoo(Interface):
   ...    def simple(arg1): "Takes one positional argument"
   >>> @implementer(IFoo)
   ... class Foo(object):
   ...    pass
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <InterfaceClass builtins.IFoo>: The IFoo.simple(arg1) attribute was not provided.

Once they exist, they are checked to be callable, and for compatible signatures.

Not being callable is an error.

.. doctest::

   >>> Foo.simple = 42
   >>> verify_foo()
   The object <Foo...> violates the contract of IFoo.simple(arg1) because implementation is not a method.

Taking too few arguments is an error.

.. doctest::

   >>> Foo.simple = lambda: "I take no arguments"
   >>> verify_foo()
   The object <Foo...> violates the contract of IFoo.simple(arg1) because implementation doesn't allow enough arguments.

Requiring too many arguments is an error. (Recall that the ``self``
argument is implicit.)

.. doctest::

   >>> Foo.simple = lambda self, a, b: "I require two arguments"
   >>> verify_foo()
   The object <Foo...> violates the contract of IFoo.simple(arg1) because implementation requires too many arguments.

Variable arguments can be used to implement the required number, as
can arguments with defaults.

.. doctest::

   >>> Foo.simple = lambda self, *args: "Varargs work."
   >>> verify_foo()
   True
   >>> Foo.simple = lambda self, a=1, b=2: "Default args work."
   >>> verify_foo()
   True

If our interface defines a method that uses variable positional or
variable keyword arguments, the implementation must also accept them.

.. doctest::

   >>> class IFoo(Interface):
   ...    def needs_kwargs(**kwargs): pass
   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     def needs_kwargs(self, a=1, b=2): pass
   >>> verify_foo()
   The object <Foo...> violates the contract of IFoo.needs_kwargs(**kwargs) because implementation doesn't support keyword arguments.

   >>> class IFoo(Interface):
   ...    def needs_varargs(*args): pass
   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     def needs_varargs(self, **kwargs): pass
   >>> verify_foo()
   The object <Foo...> violates the contract of IFoo.needs_varargs(*args) because implementation doesn't support variable arguments.


Of course, missing attributes are also found and reported.

.. doctest::

   >>> class IFoo(Interface):
   ...    x = Attribute('The X attribute')
   ...    def method(arg1): "Takes one positional argument"
   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     def method(self): "I don't have enough arguments"
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <InterfaceClass ...IFoo>:
       The IFoo.x attribute was not provided
       violates the contract of IFoo.method(arg1) because implementation doesn't allow enough arguments

Verifying Classes
=================

The function `verifyClass` is used to check that a class implements
an interface properly, meaning that its instances properly provide the
interface. Many of the same things that `verifyObject` checks can be
checked for classes, but certain conditions, such as the presence of
attributes, cannot be verified.

.. autofunction:: verifyClass

.. doctest::

    >>> from zope.interface.verify import verifyClass
    >>> def verify_foo_class():
    ...    try:
    ...        return verifyClass(IFoo, Foo)
    ...    except Invalid as e:
    ...        print(e)

    >>> verify_foo_class()
    The object <class 'Foo'> violates the contract of IFoo.method(arg1) because implementation doesn't allow enough arguments.
