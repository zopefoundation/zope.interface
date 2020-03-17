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

Let's demonstrate. We'll begin by defining a simple interface hierarchy
requiring two attributes, and a helper method that will instantiate and verify
that an object provides this interface.

.. doctest::

   >>> from zope.interface import Interface, Attribute, implementer
   >>> from zope.interface import Invalid
   >>> from zope.interface.verify import verifyObject
   >>> oname, __name__ = __name__, 'base' # Pretend we're in a module, not a doctest
   >>> class IBase(Interface):
   ...     x = Attribute("The X attribute")
   >>> __name__ = 'module' # Pretend to be a different module.
   >>> class IFoo(IBase):
   ...     y = Attribute("The Y attribute")
   >>> __name__ = oname; del oname
   >>> class Foo(object):
   ...     pass
   >>> def verify_foo(**kwargs):
   ...    foo = Foo()
   ...    try:
   ...        return verifyObject(IFoo, foo, **kwargs)
   ...    except Invalid as e:
   ...        print(e)

If we try to verify an instance of this ``Foo`` class, three errors
will be reported. The declarations (does the object provide ``IFoo``)
are checked, as are the attributes specified in the interface being
validated (and its ancestors). Notice that the interface being
verified is shown, as is the interface where the attribute was
defined.

.. doctest::

   >>> verify_foo()
   The object <Foo...> has failed to implement interface <...IFoo>:
       Does not declaratively implement the interface
       The base.IBase.x attribute was not provided
       The module.IFoo.y attribute was not provided

If we add the two missing attributes, we still have the error about not
declaring the correct interface.

.. doctest::

   >>> Foo.x = Foo.y = 42
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <...IFoo>: Does not declaratively implement the interface.

If we want to only check the structure of the object, without examining
its declarations, we can use the ``tentative`` argument.

.. doctest::

   >>> verify_foo(tentative=True)
   True

Of course, we can always mark a particular instance as providing the
desired interface.

.. doctest::

   >>> from zope.interface import alsoProvides
   >>> foo = Foo()
   >>> alsoProvides(foo, IFoo)
   >>> verifyObject(IFoo, foo)
   True

If all instances will provide the interface, we can
mark the class as implementing it.

.. doctest::

   >>> from zope.interface import classImplements
   >>> classImplements(Foo, IFoo)
   >>> verify_foo()
   True


Testing for attributes
----------------------

Attributes of the object, be they defined by its class or added by its
``__init__`` method, will be recognized:

.. doctest::

   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     x = 1
   ...     def __init__(self):
   ...         self.y = 2

   >>> verifyObject(IFoo, Foo())
   True

If either attribute is missing, verification will fail by raising an
exception.

.. doctest::

   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     x = 1
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <...IFoo>: The module.IFoo.y attribute was not provided.
   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     def __init__(self):
   ...         self.y = 2
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <...IFoo>: The base.IBase.x attribute was not provided.

If both attributes are missing, an exception is raised reporting
both errors.

.. doctest::

    >>> @implementer(IFoo)
    ... class Foo(object):
    ...     pass
    >>> verify_foo()
    The object <Foo ...> has failed to implement interface <...IFoo>:
        The base.IBase.x attribute was not provided
        The module.IFoo.y attribute was not provided

If an attribute is implemented as a property that raises an ``AttributeError``
when trying to get its value, the attribute is considered missing:

.. doctest::

   >>> oname, __name__ = __name__, 'module'
   >>> class IFoo(Interface):
   ...     x = Attribute('The X attribute')
   >>> __name__ = oname; del oname
   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     @property
   ...     def x(self):
   ...         raise AttributeError
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <...IFoo>: The module.IFoo.x attribute was not provided.


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

   >>> oname, __name__ = __name__, 'module'
   >>> class IFoo(Interface):
   ...    def simple(arg1): "Takes one positional argument"
   >>> __name__ = oname; del oname
   >>> @implementer(IFoo)
   ... class Foo(object):
   ...    pass
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <...IFoo>: The module.IFoo.simple(arg1) attribute was not provided.

Once they exist, they are checked to be callable, and for compatible signatures.

Not being callable is an error.

.. doctest::

   >>> Foo.simple = 42
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <...IFoo>: The contract of module.IFoo.simple(arg1) is violated because '42' is not a method.

Taking too few arguments is an error. (Recall that the ``self``
argument is implicit.)

.. doctest::

   >>> Foo.simple = lambda self: "I take no arguments"
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <...IFoo>: The contract of module.IFoo.simple(arg1) is violated because '<lambda>()' doesn't allow enough arguments.

Requiring too many arguments is an error.

.. doctest::

   >>> Foo.simple = lambda self, a, b: "I require two arguments"
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <...IFoo>: The contract of module.IFoo.simple(arg1) is violated because '<lambda>(a, b)' requires too many arguments.

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

   >>> oname, __name__ = __name__, 'module'
   >>> class IFoo(Interface):
   ...    def needs_kwargs(**kwargs): pass
   >>> __name__ = oname; del oname
   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     def needs_kwargs(self, a=1, b=2): pass
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <...IFoo>: The contract of module.IFoo.needs_kwargs(**kwargs) is violated because 'Foo.needs_kwargs(a=1, b=2)' doesn't support keyword arguments.

   >>> oname, __name__ = __name__, 'module'
   >>> class IFoo(Interface):
   ...    def needs_varargs(*args): pass
   >>> __name__ = oname; del oname
   >>> @implementer(IFoo)
   ... class Foo(object):
   ...     def needs_varargs(self, **kwargs): pass
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <...IFoo>: The contract of module.IFoo.needs_varargs(*args) is violated because 'Foo.needs_varargs(**kwargs)' doesn't support variable arguments.

Of course, missing attributes are also found and reported, and the
source interface of the missing attribute is included. Similarly, when
the failing method is from a parent class, that is also reported.

.. doctest::

   >>> oname, __name__ = __name__, 'base'
   >>> class IBase(Interface):
   ...    def method(arg1): "Takes one positional argument"
   >>> __name__ = 'module'
   >>> class IFoo(IBase):
   ...    x = Attribute('The X attribute')
   >>> __name__ = oname; del oname
   >>> class Base(object):
   ...    def method(self): "I don't have enough arguments"
   >>> @implementer(IFoo)
   ... class Foo(Base):
   ...    pass
   >>> verify_foo()
   The object <Foo...> has failed to implement interface <...IFoo>:
       The contract of base.IBase.method(arg1) is violated because 'Base.method()' doesn't allow enough arguments
       The module.IFoo.x attribute was not provided

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
    The object <class 'Foo'> has failed to implement interface <...IFoo>: The contract of base.IBase.method(arg1) is violated because 'Base.method(self)' doesn't allow enough arguments.
