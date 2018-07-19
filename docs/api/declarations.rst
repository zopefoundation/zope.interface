=========================================
 API for ``zope.interface.declarations``
=========================================


``Declaration``
===============


API
---

Declaration objects implement the API defined by
:class:`zope.interface.interfaces.IDeclaration`:

.. autointerface:: zope.interface.interfaces.IDeclaration
   :members:
   :member-order: bysource

.. autoclass:: zope.interface.declarations.Declaration

Usage
-----

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
   ['I4', 'I2', 'I1', 'I3', 'Interface']
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



``implementedBy``
=================

API
---

.. autofunction:: zope.interface.declarations.implementedByFallback


Usage
-----

Consider the following example:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface import implements
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
   >>> class A(object):
   ...   implements(I3)
   >>> class B(object):
   ...   implements(I4)
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
   >>> class C1(object):
   ...   implements(I2)
   >>> class C2(C1):
   ...   implements(I3)
   >>> [i.getName() for i in implementedBy(C2)]
   ['I3', 'I2']

Really, any object should be able to receive a successful answer, even
an instance:

.. doctest::

   >>> class Callable(object):
   ...     def __call__(self):
   ...         return self
   >>> implementedBy(Callable())
   <implementedBy __builtin__.?>

Note that the name of the spec ends with a '?', because the ``Callable``
instance does not have a ``__name__`` attribute.

This also manages storage of implementation specifications.



``classImplementsOnly``
=======================

API
---

.. autofunction:: zope.interface.declarations.classImplementsOnly


Usage
-----

Consider the following example:

.. doctest::

   >>> from zope.interface import Interface
   >>> class I1(Interface): pass
   ...
   >>> class I2(Interface): pass
   ...
   >>> class I3(Interface): pass
   ...
   >>> class I4(Interface): pass
   ...
   >>> class A(object):
   ...   implements(I3)
   >>> class B(object):
   ...   implements(I4)
   >>> class C(A, B):
   ...   pass
   >>> classImplementsOnly(C, I1, I2)
   >>> [i.getName() for i in implementedBy(C)]
   ['I1', 'I2']

Instances of ``C`` provide only ``I1``, ``I2``, and regardless of
whatever interfaces instances of ``A`` and ``B`` implement.



``classImplements``
===================

API
---

.. autofunction:: zope.interface.declarations.classImplements


Usage
-----

Consider the following example:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface import classImplements
   >>> class I1(Interface): pass
   ...
   >>> class I2(Interface): pass
   ...
   >>> class I3(Interface): pass
   ...
   >>> class I4(Interface): pass
   ...
   >>> class I5(Interface): pass
   ...
   >>> class A(object):
   ...   implements(I3)
   >>> class B(object):
   ...   implements(I4)
   >>> class C(A, B):
   ...   pass
   >>> classImplements(C, I1, I2)
   >>> [i.getName() for i in implementedBy(C)]
   ['I1', 'I2', 'I3', 'I4']
   >>> classImplements(C, I5)
   >>> [i.getName() for i in implementedBy(C)]
   ['I1', 'I2', 'I5', 'I3', 'I4']

Instances of ``C`` provide ``I1``, ``I2``, ``I5``, and whatever
interfaces instances of ``A`` and ``B`` provide.



``implementer``
===============

API
---

.. autoclass:: zope.interface.declarations.implementer
   :members:
   :member-order: bysource



``implementer_only``
====================

API
---

.. autoclass:: zope.interface.declarations.implementer_only
   :members:
   :member-order: bysource



``implements``
==============

API
---

.. autofunction:: zope.interface.declarations.implements


``implementsOnly``
==================

API
---

.. autofunction:: zope.interface.declarations.implementsOnly




``ProvidesClass``
=================

API
---

.. autoclass:: zope.interface.declarations.ProvidesClass
   :members:
   :member-order: bysource


Usage
-----

Descriptor semantics (via ``Provides.__get__``):

.. doctest::

   >>> from zope.interface import Interface
   >>> class IFooFactory(Interface): pass
   ...
   >>> class C(object):
   ...   pass
   >>> from zope.interface.declarations import ProvidesClass
   >>> C.__provides__ = ProvidesClass(C, IFooFactory)
   >>> [i.getName() for i in C.__provides__]
   ['IFooFactory']
   >>> getattr(C(), '__provides__', 0)
   0




``Provides``
============

API
---

.. autofunction:: zope.interface.declarations.Provides


Usage
-----

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
   ...    pass
   >>> from zope.interface import Interface
   >>> class I(Interface):
   ...    pass
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



``directlyProvides``
====================

API
---

.. autofunction:: zope.interface.declarations.directlyProvides


Usage
-----

Consider the following example:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface import providedBy
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
   >>> class A(object):
   ...     implements(IA1, IA2)
   >>> class B(object):
   ...     implements(IB)
   >>> class C(A, B):
   ...    implements(IC)
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



``alsoProvides``
================

API
---

.. autofunction:: zope.interface.declarations.alsoProvides


Usage
-----

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
   >>> class A(object):
   ...     implements(IA1, IA2)
   >>> class B(object):
   ...     implements(IB)
   >>> class C(A, B):
   ...    implements(IC)
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



``noLongerProvides``
====================

API
---

.. autofunction:: zope.interface.declarations.noLongerProvides


Usage
-----

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

   >>> class C(object):
   ...    implements(I1)
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



``directlyProvidedBy``
======================

API
---

.. autofunction:: zope.interface.declarations.directlyProvidedBy



``classProvides``
=================

API
---

.. autofunction:: zope.interface.declarations.classProvides


Usage
-----

For example:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface.declarations import implementer
   >>> from zope.interface import classProvides
   >>> class IFooFactory(Interface):
   ...     pass
   >>> class IFoo(Interface):
   ...     pass
   >>> @implementer(IFoo)
   ... class C(object):
   ...     classProvides(IFooFactory)
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



``provider``
============

API
---

.. autoclass:: zope.interface.declarations.provider
   :members:
   :member-order: bysource


``moduleProvides``
==================

API
---

.. autofunction:: zope.interface.declarations.moduleProvides




``ObjectSpecification``
=======================

API
---

.. autofunction:: zope.interface.declarations.ObjectSpecification


Usage
-----

For example:

.. doctest::

   >>> from zope.interface import Interface
   >>> from zope.interface import implementsOnly
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
   >>> class A(object):
   ...     implements(I1)
   >>> class B(object): __implemented__ = I2
   ...
   >>> class C(A, B):
   ...     implements(I31)
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
   >>> class COnly(A, B):
   ...     implementsOnly(I31)
   >>> class D(COnly):
   ...     implements(I5)
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



``providedBy``
==============

API
---

.. autofunction:: zope.interface.declarations.providedBy



``ObjectSpecificationDescriptor``
=================================

API
---

.. autoclass:: zope.interface.declarations.ObjectSpecificationDescriptor
   :members:
   :member-order: bysource

Usage
-----

For example:

.. doctest::

   >>> from zope.interface import Interface
   >>> class IFoo(Interface): pass
   ...
   >>> class IFooFactory(Interface): pass
   ...
   >>> @implementer(IFoo)
   ... class C(object):
   ...   classProvides(IFooFactory)
   >>> [i.getName() for i in C.__providedBy__]
   ['IFooFactory']
   >>> [i.getName() for i in C().__providedBy__]
   ['IFoo']

Get an ObjectSpecification bound to either an instance or a class,
depending on how we were accessed.


``named``
=========

API
---

.. autoclass:: zope.interface.declarations.named
   :members:
   :member-order: bysource

Usage
-----

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
