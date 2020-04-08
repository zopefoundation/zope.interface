==================================================
 Declaring and Checking The Interfaces of Objects
==================================================

Declaring what interfaces an object implements or provides, and later
being able to check those, is an important part of this package.
Declaring interfaces, in particular, can be done both statically at
object definition time and dynamically later on.

The functionality that allows declaring and checking interfaces is
provided directly in the ``zope.interface`` module. It is described by
the interface ``zope.interface.interfaces.IInterfaceDeclaration``. We
will first look at that interface, and then we will look more
carefully at each object it documents, including providing examples.

.. autointerface:: zope.interface.interfaces.IInterfaceDeclaration


.. currentmodule:: zope.interface

Declaring Interfaces
====================

To declare an interface itself, extend the ``Interface`` base class.

.. autointerface:: Interface
   :noindex:

.. autofunction:: taggedValue
   :noindex:

   .. documented more thoroughly in README.rst

.. autofunction:: invariant
   :noindex:

   .. documented in README.rst

.. autofunction:: interfacemethod

Declaring The Interfaces of Objects
===================================


implementer
-----------

.. autoclass:: implementer


implementer_only
----------------

.. autoclass:: implementer_only


classImplementsOnly
-------------------

.. autofunction:: classImplementsOnly


Consider the following example:

.. doctest::

   >>> from zope.interface import implementedBy
   >>> from zope.interface import implementer
   >>> from zope.interface import classImplementsOnly
   >>> from zope.interface import Interface
   >>> class I1(Interface): pass
   ...
   >>> class I2(Interface): pass
   ...
   >>> class I3(Interface): pass
   ...
   >>> class I4(Interface): pass
   ...
   >>> @implementer(I3)
   ... class A(object):
   ...     pass
   >>> @implementer(I4)
   ... class B(object):
   ...     pass
   >>> class C(A, B):
   ...   pass
   >>> classImplementsOnly(C, I1, I2)
   >>> [i.getName() for i in implementedBy(C)]
   ['I1', 'I2']

Instances of ``C`` provide only ``I1``, ``I2``, and regardless of
whatever interfaces instances of ``A`` and ``B`` implement.


classImplements
---------------

.. autofunction:: classImplements

Consider the following example:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface import classImplements
   >>> from zope.interface.ro import is_consistent
   >>> class I1(Interface): pass
   ...
   >>> class I2(Interface): pass
   ...
   >>> class IA(Interface): pass
   ...
   >>> class IB(Interface): pass
   ...
   >>> class I5(Interface): pass
   ...
   >>> @implementer(IA)
   ... class A(object):
   ...     pass
   >>> @implementer(IB)
   ... class B(object):
   ...     pass
   >>> class C(A, B):
   ...   pass
   >>> classImplements(C, I1, I2)
   >>> [i.getName() for i in implementedBy(C)]
   ['I1', 'I2', 'IA', 'IB']

Instances of ``C`` provide ``I1`` and ``I2``, plus whatever
instances of ``A`` and ``B`` provide.

.. doctest::

   >>> classImplements(C, I5)
   >>> [i.getName() for i in implementedBy(C)]
   ['I1', 'I2', 'I5', 'IA', 'IB']

Instances of ``C`` now also provide ``I5``. Notice how ``I5`` was
added to the *end* of the list of things provided directly by ``C``.

If we ask a class to implement an interface that extends
an interface it already implements, that interface will go at the
*beginning* of the list, in order to preserve a consistent resolution
order.

.. doctest::

   >>> class I6(I5): pass
   >>> class I7(IA): pass
   >>> classImplements(C, I6, I7)
   >>> [i.getName() for i in implementedBy(C)]
   ['I6', 'I1', 'I2', 'I5', 'I7', 'IA', 'IB']
   >>> is_consistent(implementedBy(C))
   True

This cannot be used to introduce duplicates.

.. doctest::

   >>> classImplements(C, IA, IB, I1, I2)
   >>> [i.getName() for i in implementedBy(C)]
   ['I6', 'I1', 'I2', 'I5', 'I7', 'IA', 'IB']


classImplementsFirst
--------------------

.. autofunction:: classImplementsFirst

Consider the following example:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface import classImplements
   >>> from zope.interface import classImplementsFirst
   >>> class I1(Interface): pass
   ...
   >>> class I2(Interface): pass
   ...
   >>> class IA(Interface): pass
   ...
   >>> class IB(Interface): pass
   ...
   >>> class I5(Interface): pass
   ...
   >>> @implementer(IA)
   ... class A(object):
   ...     pass
   >>> @implementer(IB)
   ... class B(object):
   ...     pass
   >>> class C(A, B):
   ...   pass
   >>> classImplementsFirst(C, I2)
   >>> classImplementsFirst(C, I1)
   >>> [i.getName() for i in implementedBy(C)]
   ['I1', 'I2', 'IA', 'IB']

Instances of ``C`` provide ``I1``, ``I2``, ``I5``, and whatever
interfaces instances of ``A`` and ``B`` provide.

.. doctest::

   >>> classImplementsFirst(C, I5)
   >>> [i.getName() for i in implementedBy(C)]
   ['I5', 'I1', 'I2', 'IA', 'IB']

Instances of ``C`` now also provide ``I5``. Notice how ``I5`` was
added to the *beginning* of the list of things provided directly by
``C``. Unlike `classImplements`, this ignores interface inheritance
and does not attempt to ensure a consistent resolution order (except
that it continues to elide interfaces already implemented through
class inheritance)::

.. doctest::

   >>> class IBA(IB, IA):
   ...     pass
   >>> classImplementsFirst(C, IBA)
   >>> classImplementsFirst(C, IA)
   >>> [i.getName() for i in implementedBy(C)]
   ['IBA', 'I5', 'I1', 'I2', 'IA', 'IB']

This cannot be used to introduce duplicates.

.. doctest::

   >>> len(implementedBy(C).declared)
   4
   >>> classImplementsFirst(C, IA)
   >>> classImplementsFirst(C, IBA)
   >>> classImplementsFirst(C, IA)
   >>> classImplementsFirst(C, IBA)
   >>> [i.getName() for i in implementedBy(C)]
   ['IBA', 'I5', 'I1', 'I2', 'IA', 'IB']
   >>> len(implementedBy(C).declared)
   4


directlyProvides
----------------

.. autofunction:: directlyProvides


Consider the following example:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface import providedBy
   >>> from zope.interface import directlyProvides
   >>> class I1(Interface): pass
   ...
   >>> class I2(Interface): pass
   ...
   >>> class IA1(Interface): pass
   ...
   >>> class IA2(Interface): pass
   ...
   >>> class IB(Interface): pass
   ...
   >>> class IC(Interface): pass
   ...
   >>> @implementer(IA1, IA2)
   ... class A(object):
   ...     pass
   >>> @implementer(IB)
   ... class B(object):
   ...     pass
   >>> @implementer(IC)
   ... class C(A, B):
   ...     pass
   >>> ob = C()
   >>> directlyProvides(ob, I1, I2)
   >>> int(I1 in providedBy(ob))
   1
   >>> int(I2 in providedBy(ob))
   1
   >>> int(IA1 in providedBy(ob))
   1
   >>> int(IA2 in providedBy(ob))
   1
   >>> int(IB in providedBy(ob))
   1
   >>> int(IC in providedBy(ob))
   1

The object, ``ob`` provides ``I1``, ``I2``, and whatever interfaces
instances have been declared for instances of ``C``.

To remove directly provided interfaces, use ``directlyProvidedBy`` and
subtract the unwanted interfaces. For example:

.. doctest::

   >>> from zope.interface import directlyProvidedBy
   >>> directlyProvides(ob, directlyProvidedBy(ob)-I2)
   >>> int(I1 in providedBy(ob))
   1
   >>> int(I2 in providedBy(ob))
   0

removes ``I2`` from the interfaces directly provided by ``ob``. The object,
``ob`` no longer directly provides ``I2``, although it might still
provide ``I2`` if its class implements ``I2``.

To add directly provided interfaces, use ``directlyProvidedBy`` and
include additional interfaces.  For example:

.. doctest::

   >>> int(I2 in providedBy(ob))
   0
   >>> from zope.interface import directlyProvidedBy
   >>> directlyProvides(ob, directlyProvidedBy(ob), I2)

adds ``I2`` to the interfaces directly provided by ``ob``:

.. doctest::

   >>> int(I2 in providedBy(ob))
   1

We need to avoid setting this attribute on meta classes that
don't support descriptors.

We can do away with this check when we get rid of the old EC


alsoProvides
------------

.. autofunction:: alsoProvides


Consider the following example:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface import alsoProvides
   >>> class I1(Interface): pass
   ...
   >>> class I2(Interface): pass
   ...
   >>> class IA1(Interface): pass
   ...
   >>> class IA2(Interface): pass
   ...
   >>> class IB(Interface): pass
   ...
   >>> class IC(Interface): pass
   ...
   >>> @implementer(IA1, IA2)
   ... class A(object):
   ...     pass
   >>> @implementer(IB)
   ... class B(object):
   ...     pass
   >>> @implementer(IC)
   ... class C(A, B):
   ...     pass
   >>> ob = C()
   >>> directlyProvides(ob, I1)
   >>> int(I1 in providedBy(ob))
   1
   >>> int(I2 in providedBy(ob))
   0
   >>> int(IA1 in providedBy(ob))
   1
   >>> int(IA2 in providedBy(ob))
   1
   >>> int(IB in providedBy(ob))
   1
   >>> int(IC in providedBy(ob))
   1
   >>> alsoProvides(ob, I2)
   >>> int(I1 in providedBy(ob))
   1
   >>> int(I2 in providedBy(ob))
   1
   >>> int(IA1 in providedBy(ob))
   1
   >>> int(IA2 in providedBy(ob))
   1
   >>> int(IB in providedBy(ob))
   1
   >>> int(IC in providedBy(ob))
   1

The object, ``ob`` provides ``I1``, ``I2``, and whatever interfaces
instances have been declared for instances of ``C``. Notice that the
``alsoProvides`` just extends the provided interfaces.


noLongerProvides
----------------

.. autofunction:: noLongerProvides

Consider the following two interfaces:

.. doctest::

   >>> from zope.interface import Interface
   >>> class I1(Interface): pass
   ...
   >>> class I2(Interface): pass
   ...

``I1`` is provided through the class, ``I2`` is directly provided
by the object:

.. doctest::

   >>> @implementer(I1)
   ... class C(object):
   ...     pass
   >>> c = C()
   >>> alsoProvides(c, I2)
   >>> I2.providedBy(c)
   True

Remove ``I2`` from ``c`` again:

.. doctest::

   >>> from zope.interface import noLongerProvides
   >>> noLongerProvides(c, I2)
   >>> I2.providedBy(c)
   False

Removing an interface that is provided through the class is not possible:

.. doctest::

   >>> noLongerProvides(c, I1)
   Traceback (most recent call last):
   ...
   ValueError: Can only remove directly provided interfaces.


provider
--------

.. autoclass:: provider

For example:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface import implementer
   >>> from zope.interface import provider
   >>> class IFooFactory(Interface):
   ...     pass
   >>> class IFoo(Interface):
   ...     pass
   >>> @implementer(IFoo)
   ... @provider(IFooFactory)
   ... class C(object):
   ...     pass
   >>> [i.getName() for i in C.__provides__]
   ['IFooFactory']
   >>> [i.getName() for i in C().__provides__]
   ['IFoo']

Which is equivalent to:

.. doctest::

   >>> from zope.interface import Interface
   >>> class IFoo(Interface): pass
   ...
   >>> class IFooFactory(Interface): pass
   ...
   >>> @implementer(IFoo)
   ... class C(object):
   ...   pass
   >>> directlyProvides(C, IFooFactory)
   >>> [i.getName() for i in C.__providedBy__]
   ['IFooFactory']
   >>> [i.getName() for i in C().__providedBy__]
   ['IFoo']


moduleProvides
--------------

.. autofunction:: moduleProvides


named
-----

.. autoclass:: zope.interface.declarations.named

For example:

.. doctest::

   >>> from zope.interface.declarations import named

   >>> @named('foo')
   ... class Foo(object):
   ...     pass

   >>> Foo.__component_name__
   'foo'

When registering an adapter or utility component, the registry looks for the
``__component_name__`` attribute and uses it, if no name was explicitly
provided.


Deprecated Functions
--------------------

implements
~~~~~~~~~~

.. caution:: Does not work on Python 3.  Use the `implementer` decorator instead.

.. autofunction:: implements


implementsOnly
~~~~~~~~~~~~~~

.. caution:: Does not work on Python 3.  Use the `implementer_only` decorator instead.

.. autofunction:: implementsOnly


classProvides
~~~~~~~~~~~~~

.. caution:: Does not work on Python 3.  Use the `provider` decorator instead.

.. autofunction:: classProvides


Querying The Interfaces Of Objects
==================================

All of these functions return an
`~zope.interface.interfaces.IDeclaration`.
You'll notice that an ``IDeclaration`` is a type of
`~zope.interface.interfaces.ISpecification`, as is
``zope.interface.Interface``, so they share some common behaviour.

.. autointerface:: zope.interface.interfaces.IDeclaration
   :members:
   :member-order: bysource


implementedBy
-------------

.. autofunction:: implementedBy


Consider the following example:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface import implementer
   >>> from zope.interface import classImplementsOnly
   >>> from zope.interface import implementedBy
   >>> class I1(Interface): pass
   ...
   >>> class I2(Interface): pass
   ...
   >>> class I3(Interface): pass
   ...
   >>> class I4(Interface): pass
   ...
   >>> @implementer(I3)
   ... class A(object):
   ...     pass
   >>> @implementer(I4)
   ... class B(object):
   ...     pass
   >>> class C(A, B):
   ...   pass
   >>> classImplementsOnly(C, I1, I2)
   >>> [i.getName() for i in implementedBy(C)]
   ['I1', 'I2']

Instances of ``C`` provide only ``I1``, ``I2``, and regardless of
whatever interfaces instances of ``A`` and ``B`` implement.

Another example:

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
   >>> @implementer(I2)
   ... class C1(object):
   ...     pass
   >>> @implementer(I3)
   ... class C2(C1):
   ...     pass
   >>> [i.getName() for i in implementedBy(C2)]
   ['I3', 'I2']

Really, any object should be able to receive a successful answer, even
an instance:

.. doctest::

   >>> class Callable(object):
   ...     def __call__(self):
   ...         return self
   >>> implementedBy(Callable())
   <implementedBy builtins.?>

Note that the name of the spec ends with a '?', because the ``Callable``
instance does not have a ``__name__`` attribute.

This also manages storage of implementation specifications.


providedBy
----------

.. autofunction:: providedBy


directlyProvidedBy
------------------

.. autofunction:: directlyProvidedBy


Classes
=======


Declarations
------------

Declaration objects implement the API defined by
:class:`~zope.interface.interfaces.IDeclaration`.


.. autoclass:: Declaration


Exmples for :meth:`Declaration.__contains__`:

.. doctest::

   >>> from zope.interface.declarations import Declaration
   >>> from zope.interface import Interface
   >>> class I1(Interface): pass
   ...
   >>> class I2(I1): pass
   ...
   >>> class I3(Interface): pass
   ...
   >>> class I4(I3): pass
   ...
   >>> spec = Declaration(I2, I3)
   >>> spec = Declaration(I4, spec)
   >>> int(I1 in spec)
   0
   >>> int(I2 in spec)
   1
   >>> int(I3 in spec)
   1
   >>> int(I4 in spec)
   1

Exmples for :meth:`Declaration.__iter__`:

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
   >>> spec = Declaration(I2, I3)
   >>> spec = Declaration(I4, spec)
   >>> i = iter(spec)
   >>> [x.getName() for x in i]
   ['I4', 'I2', 'I3']
   >>> list(i)
   []

Exmples for :meth:`Declaration.flattened`:

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
   >>> spec = Declaration(I2, I3)
   >>> spec = Declaration(I4, spec)
   >>> i = spec.flattened()
   >>> [x.getName() for x in i]
   ['I4', 'I2', 'I3', 'I1', 'Interface']
   >>> list(i)
   []

Exmples for :meth:`Declaration.__sub__`:

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
   >>> spec = Declaration()
   >>> [iface.getName() for iface in spec]
   []
   >>> spec -= I1
   >>> [iface.getName() for iface in spec]
   []
   >>> spec -= Declaration(I1, I2)
   >>> [iface.getName() for iface in spec]
   []
   >>> spec = Declaration(I2, I4)
   >>> [iface.getName() for iface in spec]
   ['I2', 'I4']
   >>> [iface.getName() for iface in spec - I4]
   ['I2']
   >>> [iface.getName() for iface in spec - I1]
   ['I4']
   >>> [iface.getName() for iface
   ...  in spec - Declaration(I3, I4)]
   ['I2']

Exmples for :meth:`Declaration.__add__`:

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
   >>> spec = Declaration()
   >>> [iface.getName() for iface in spec]
   []
   >>> [iface.getName() for iface in spec+I1]
   ['I1']
   >>> [iface.getName() for iface in I1+spec]
   ['I1']
   >>> spec2 = spec
   >>> spec += I1
   >>> [iface.getName() for iface in spec]
   ['I1']
   >>> [iface.getName() for iface in spec2]
   []
   >>> spec2 += Declaration(I3, I4)
   >>> [iface.getName() for iface in spec2]
   ['I3', 'I4']
   >>> [iface.getName() for iface in spec+spec2]
   ['I1', 'I3', 'I4']
   >>> [iface.getName() for iface in spec2+spec]
   ['I3', 'I4', 'I1']



ProvidesClass
-------------

.. autoclass:: zope.interface.declarations.ProvidesClass


Descriptor semantics (via ``Provides.__get__``):

.. doctest::

   >>> from zope.interface import Interface
   >>> class IFooFactory(Interface):
   ...     pass
   >>> class C(object):
   ...     pass
   >>> from zope.interface.declarations import ProvidesClass
   >>> C.__provides__ = ProvidesClass(C, IFooFactory)
   >>> [i.getName() for i in C.__provides__]
   ['IFooFactory']
   >>> getattr(C(), '__provides__', 0)
   0


Implementation Details
======================

The following section discusses some implementation details and
demonstrates their use. You'll notice that they are all demonstrated
using the previously-defined functions.

Provides
--------

.. autofunction:: Provides

In the examples below, we are going to make assertions about
the size of the weakvalue dictionary.  For the assertions to be
meaningful, we need to force garbage collection to make sure garbage
objects are, indeed, removed from the system. Depending on how Python
is run, we may need to make multiple calls to be sure.  We provide a
collect function to help with this:

.. doctest::

   >>> import gc
   >>> def collect():
   ...     for i in range(4):
   ...         gc.collect()
   >>> collect()
   >>> from zope.interface import directlyProvides
   >>> from zope.interface.declarations import InstanceDeclarations
   >>> before = len(InstanceDeclarations)
   >>> class C(object):
   ...     pass
   >>> from zope.interface import Interface
   >>> class I(Interface):
   ...     pass
   >>> c1 = C()
   >>> c2 = C()
   >>> len(InstanceDeclarations) == before
   True
   >>> directlyProvides(c1, I)
   >>> len(InstanceDeclarations) == before + 1
   True
   >>> directlyProvides(c2, I)
   >>> len(InstanceDeclarations) == before + 1
   True
   >>> del c1
   >>> collect()
   >>> len(InstanceDeclarations) == before + 1
   True
   >>> del c2
   >>> collect()
   >>> len(InstanceDeclarations) == before
   True


ObjectSpecification
-------------------

.. autofunction:: zope.interface.declarations.ObjectSpecification


For example:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface import implementer_only
   >>> class I1(Interface): pass
   ...
   >>> class I2(Interface): pass
   ...
   >>> class I3(Interface): pass
   ...
   >>> class I31(I3): pass
   ...
   >>> class I4(Interface): pass
   ...
   >>> class I5(Interface): pass
   ...
   >>> @implementer(I1)
   ... class A(object):
   ...     pass
   >>> class B(object):
   ...     __implemented__ = I2
   >>> @implementer(I31)
   ... class C(A, B):
   ...     pass
   >>> c = C()
   >>> directlyProvides(c, I4)
   >>> [i.getName() for i in providedBy(c)]
   ['I4', 'I31', 'I1', 'I2']
   >>> [i.getName() for i in providedBy(c).flattened()]
   ['I4', 'I31', 'I3', 'I1', 'I2', 'Interface']
   >>> int(I1 in providedBy(c))
   1
   >>> int(I3 in providedBy(c))
   0
   >>> int(providedBy(c).extends(I3))
   1
   >>> int(providedBy(c).extends(I31))
   1
   >>> int(providedBy(c).extends(I5))
   0
   >>> @implementer_only(I31)
   ... class COnly(A, B):
   ...     pass
   >>> @implementer(I5)
   ... class D(COnly):
   ...     pass
   >>> c = D()
   >>> directlyProvides(c, I4)
   >>> [i.getName() for i in providedBy(c)]
   ['I4', 'I5', 'I31']
   >>> [i.getName() for i in providedBy(c).flattened()]
   ['I4', 'I5', 'I31', 'I3', 'Interface']
   >>> int(I1 in providedBy(c))
   0
   >>> int(I3 in providedBy(c))
   0
   >>> int(providedBy(c).extends(I3))
   1
   >>> int(providedBy(c).extends(I1))
   0
   >>> int(providedBy(c).extends(I31))
   1
   >>> int(providedBy(c).extends(I5))
   1

ObjectSpecificationDescriptor
-----------------------------

.. autoclass:: zope.interface.declarations.ObjectSpecificationDescriptor

For example:

.. doctest::

   >>> from zope.interface import Interface
   >>> class IFoo(Interface): pass
   ...
   >>> class IFooFactory(Interface): pass
   ...
   >>> @implementer(IFoo)
   ... @provider(IFooFactory)
   ... class C(object):
   ...     pass
   >>> [i.getName() for i in C.__providedBy__]
   ['IFooFactory']
   >>> [i.getName() for i in C().__providedBy__]
   ['IFoo']

Get an ObjectSpecification bound to either an instance or a class,
depending on how we were accessed.
