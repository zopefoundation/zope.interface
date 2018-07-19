==========================
 Interface Specifications
==========================


``zope.interface.interface.Specification``
==========================================

API
---

Specification objects implement the API defined by
:class:`zope.interface.interfaces.ISpecification`:

.. autointerface:: zope.interface.interfaces.ISpecification
   :members:
   :member-order: bysource

.. autoclass:: zope.interface.interface.Specification

Usage
-----

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

Exmples for :meth:`Specification.providedBy`:

.. doctest::

   >>> from zope.interface import *
   >>> class I1(Interface):
   ...     pass
   >>> class C(object):
   ...     implements(I1)
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

Examples for :meth:`Specification.isOrExtends`:

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

Examples for :meth:`Specification.interfaces`:

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

Exmples for :meth:`Specification.extends`:

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


``zope.interface.Interface``
============================

API
---

Interfaces are a specilization of `ISpecification` and implement the
API defined by :class:`zope.interface.interfaces.IInterface`:

.. autointerface:: zope.interface.interfaces.IInterface
   :members:
   :member-order: bysource

.. autoclass:: zope.interface.Interface

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
