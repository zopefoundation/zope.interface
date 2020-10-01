==========================
 Interface Specifications
==========================

.. currentmodule:: zope.interface.interfaces


This document discusses the actual interface objects themselves. We
begin with a basic concept of specifying an object's behaviour (with
an `ISpecification`), and then we describe the way we write such a
specification (`IInterface`). Combinations of specifications (e.g., an
object that provides multiple interfaces) are covered by
`IDeclaration`.

Specification
=============

Specification objects implement the API defined by
:class:`ISpecification`:

.. autointerface:: ISpecification
   :members:
   :member-order: bysource

.. autoclass:: zope.interface.interface.Specification
   :no-members:

For example:

.. doctest::

   >>> from zope.interface.interface import Specification
   >>> from zope.interface import Interface
   >>> class I1(Interface):
   ...     pass
   >>> class I2(I1):
   ...     pass
   >>> class I3(I2):
   ...     pass
   >>> [i.__name__ for i in I1.__bases__]
   ['Interface']
   >>> [i.__name__ for i in I2.__bases__]
   ['I1']
   >>> I3.extends(I1)
   True
   >>> I2.__bases__ = (Interface, )
   >>> [i.__name__ for i in I2.__bases__]
   ['Interface']
   >>> I3.extends(I1)
   False

Exmples for :meth:`.Specification.providedBy`:

.. doctest::

   >>> from zope.interface import *
   >>> class I1(Interface):
   ...     pass
   >>> @implementer(I1)
   ... class C(object):
   ...     pass
   >>> c = C()
   >>> class X(object):
   ...     pass
   >>> x = X()
   >>> I1.providedBy(x)
   False
   >>> I1.providedBy(C)
   False
   >>> I1.providedBy(c)
   True
   >>> directlyProvides(x, I1)
   >>> I1.providedBy(x)
   True
   >>> directlyProvides(C, I1)
   >>> I1.providedBy(C)
   True

Examples for :meth:`.Specification.isOrExtends`:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface.declarations import Declaration
   >>> class I1(Interface): pass
   ...
   >>> class I2(I1): pass
   ...
   >>> class I3(Interface): pass
   ...
   >>> class I4(I3): pass
   ...
   >>> spec = Declaration()
   >>> int(spec.extends(Interface))
   1
   >>> spec = Declaration(I2)
   >>> int(spec.extends(Interface))
   1
   >>> int(spec.extends(I1))
   1
   >>> int(spec.extends(I2))
   1
   >>> int(spec.extends(I3))
   0
   >>> int(spec.extends(I4))
   0

Examples for :meth:`.Specification.interfaces`:

.. doctest::

   >>> from zope.interface import Interface
   >>> class I1(Interface): pass
   ...
   >>> class I2(I1): pass
   ...
   >>> class I3(Interface): pass
   ...
   >>> class I4(I3): pass
   ...
   >>> spec = Specification((I2, I3))
   >>> spec = Specification((I4, spec))
   >>> i = spec.interfaces()
   >>> [x.getName() for x in i]
   ['I4', 'I2', 'I3']
   >>> list(i)
   []

Exmples for :meth:`.Specification.extends`:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface.declarations import Declaration
   >>> class I1(Interface): pass
   ...
   >>> class I2(I1): pass
   ...
   >>> class I3(Interface): pass
   ...
   >>> class I4(I3): pass
   ...
   >>> spec = Declaration()
   >>> int(spec.extends(Interface))
   1
   >>> spec = Declaration(I2)
   >>> int(spec.extends(Interface))
   1
   >>> int(spec.extends(I1))
   1
   >>> int(spec.extends(I2))
   1
   >>> int(spec.extends(I3))
   0
   >>> int(spec.extends(I4))
   0
   >>> I2.extends(I2)
   False
   >>> I2.extends(I2, False)
   True
   >>> I2.extends(I2, strict=False)
   True

Equality, Hashing, and Comparisons
----------------------------------

Specifications (including their notable subclass `Interface`), are
hashed and compared based solely on their ``__name__`` and
``__module__``, not including any information about their enclosing
scope, if any (e.g., their ``__qualname__``). This means that any two
objects created with the same name and module are considered equal and
map to the same value in a dictionary.

.. doctest::

   >>> from zope.interface import Interface
   >>> class I1(Interface): pass
   >>> orig_I1 = I1
   >>> class I1(Interface): pass
   >>> I1 is orig_I1
   False
   >>> I1 == orig_I1
   True
   >>> d = {I1: 42}
   >>> d[orig_I1]
   42
   >>> def make_nested():
   ...     class I1(Interface): pass
   ...     return I1
   >>> nested_I1 = make_nested()
   >>> I1 == orig_I1 == nested_I1
   True

Because weak references hash the same as their underlying object,
this can lead to surprising results when weak references are involved,
especially if there are cycles involved or if the garbage collector is
not based on reference counting (e.g., PyPy). For example, if you
redefine an interface named the same as an interface being used in a
``WeakKeyDictionary``, you can get a ``KeyError``, even if you put the
new interface into the dictionary.


.. doctest::

   >>> from zope.interface import Interface
   >>> import gc
   >>> from weakref import WeakKeyDictionary
   >>> wr_dict = WeakKeyDictionary()
   >>> class I1(Interface): pass
   >>> wr_dict[I1] = 42
   >>> orig_I1 = I1 # Make sure it stays alive
   >>> class I1(Interface): pass
   >>> wr_dict[I1] = 2020
   >>> del orig_I1
   >>> _ = gc.collect() # Sometime later, gc runs and makes sure the original is gone
   >>> wr_dict[I1] # Cleaning up the original weakref removed the new one
   Traceback (most recent call last):
   ...
   KeyError: ...

This is mostly likely a problem in test cases where it is tempting to
use the same named interfaces in different test methods. If references
to them escape, especially if they are used as the bases of other
interfaces, you may find surprising ``KeyError`` exceptions. For this
reason, it is best to use distinct names for local interfaces within
the same test module.


Interface
=========

Interfaces are a particular type of `ISpecification` and implement the
API defined by :class:`IInterface`.

Before we get there, we need to discuss two related concepts. The
first is that of an "element", which provides us a simple way to query
for information generically (this is important because we'll see that
``IInterface`` implements this interface):

..
  IElement defines __doc__ to be an Attribute, so the docstring
  in the class isn't used._

.. autointerface:: IElement

   Objects that have basic documentation and tagged values.

   Known derivatives include :class:`IAttribute` and its derivative
   :class:`IMethod`; these have no notion of inheritance.
   :class:`IInterface` is also a derivative, and it does have a
   notion of inheritance, expressed through its ``__bases__`` and
   ordered in its ``__iro__`` (both defined by
   :class:`ISpecification`).


.. autoclass:: zope.interface.interface.Element
   :no-members:

Next, we look at ``IAttribute`` and ``IMethod``. These make up the
content, or body, of an ``Interface``.

.. autointerface:: zope.interface.interfaces.IAttribute
.. autoclass:: zope.interface.interface.Attribute
   :no-members:

.. autointerface:: IMethod
.. autoclass:: zope.interface.interface.Method
   :no-members:

Finally we can look at the definition of ``IInterface``.

.. autointerface:: IInterface

.. autointerface:: zope.interface.Interface

Usage
-----

Exmples for :meth:`InterfaceClass.extends`:

.. doctest::

   >>> from zope.interface import Interface
   >>> class I1(Interface): pass
   ...
   >>>
   >>> i = I1.interfaces()
   >>> [x.getName() for x in i]
   ['I1']
   >>> list(i)
   []
