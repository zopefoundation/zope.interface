.. _adapter-registry:

==================
 Adapter Registry
==================

Adapter registries provide a way to register objects that depend on
one or more interface specifications and provide (perhaps indirectly)
some interface.  In addition, the registrations have names. (You can
think of the names as qualifiers of the provided interfaces.)

The term "interface specification" refers both to interfaces and to
interface declarations, such as declarations of interfaces implemented
by a class.


Single Adapters
===============

Let's look at a simple example, using a single required specification:

.. doctest::

  >>> from zope.interface.adapter import AdapterRegistry
  >>> import zope.interface

  >>> class IRequireBase(zope.interface.Interface):
  ...     pass
  >>> class IProvideBase(zope.interface.Interface):
  ...     pass
  >>> class IProvideChild(IProvideBase):
  ...     pass

  >>> registry = AdapterRegistry()

We'll register an object that depends on ``IRequireBase`` and "provides" ``IProvideChild``:

.. doctest::

  >>> registry.register([IRequireBase], IProvideChild, '', 'Base->Child')

Given the registration, we can look it up again:

.. doctest::

  >>> registry.lookup([IRequireBase], IProvideChild, '')
  'Base->Child'

Note that we used an integer in the example.  In real applications,
one would use some objects that actually depend on or provide
interfaces. The registry doesn't care about what gets registered, so
we'll use integers and strings to keep the examples simple. There is
one exception.  Registering a value of ``None`` unregisters any
previously-registered value.

If an object depends on a specification, it can be looked up with a
specification that extends the specification that it depends on:

.. doctest::

  >>> class IRequireChild(IRequireBase):
  ...     pass
  >>> registry.lookup([IRequireChild], IProvideChild, '')
  'Base->Child'

We can use a class implementation specification to look up the object:

.. doctest::

  >>> @zope.interface.implementer(IRequireChild)
  ... class C2:
  ...     pass

  >>> registry.lookup([zope.interface.implementedBy(C2)], IProvideChild, '')
  'Base->Child'


and it can be looked up for interfaces that its provided interface
extends:

.. doctest::

  >>> registry.lookup([IRequireBase], IProvideBase, '')
  'Base->Child'
  >>> registry.lookup([IRequireChild], IProvideBase, '')
  'Base->Child'

But if you require a specification that doesn't extend the specification the
object depends on, you won't get anything:

.. doctest::

  >>> registry.lookup([zope.interface.Interface], IProvideBase, '')

By the way, you can pass a default value to lookup:

.. doctest::

  >>> registry.lookup([zope.interface.Interface], IProvideBase, '', 42)
  42

If you try to get an interface the object doesn't provide, you also
won't get anything:

.. doctest::

  >>> class IProvideGrandchild(IProvideChild):
  ...     pass
  >>> registry.lookup([IRequireBase], IProvideGrandchild, '')

You also won't get anything if you use the wrong name:

.. doctest::

  >>> registry.lookup([IRequireBase], IProvideBase, 'bob')
  >>> registry.register([IRequireBase], IProvideChild, 'bob', "Bob's 12")
  >>> registry.lookup([IRequireBase], IProvideBase, 'bob')
  "Bob's 12"

You can leave the name off when doing a lookup:

.. doctest::

  >>> registry.lookup([IRequireBase], IProvideBase)
  'Base->Child'

If we register an object that provides ``IProvideBase``:

.. doctest::

  >>> registry.register([IRequireBase], IProvideBase, '', 'Base->Base')

then that object will be prefered over ``O('Base->Child')``:

.. doctest::

  >>> registry.lookup([IRequireBase], IProvideBase, '')
  'Base->Base'

Also, if we register an object for ``IRequireChild``, then that will be preferred
when using ``IRequireChild``:

.. doctest::

  >>> registry.register([IRequireChild], IProvideBase, '', 'Child->Base')
  >>> registry.lookup([IRequireChild], IProvideBase, '')
  'Child->Base'

Finding out what, if anything, is registered
--------------------------------------------

We can ask if there is an adapter registered for a collection of
interfaces. This is different than lookup, because it looks for an
exact match:

.. doctest::

  >>> print(registry.registered([IRequireBase], IProvideBase))
  Base->Base

  >>> print(registry.registered([IRequireBase], IProvideChild))
  Base->Child

  >>> print(registry.registered([IRequireBase], IProvideChild, 'bob'))
  Bob's 12


  >>> print(registry.registered([IRequireChild], IProvideBase))
  Child->Base

  >>> print(registry.registered([IRequireChild], IProvideChild))
  None

In the last example, ``None`` was returned because nothing was registered
exactly for the given interfaces.

lookup1
-------

Lookup of single adapters is common enough that there is a specialized
version of lookup that takes a single required interface:

.. doctest::

  >>> registry.lookup1(IRequireChild, IProvideBase, '')
  'Child->Base'
  >>> registry.lookup1(IRequireChild, IProvideBase)
  'Child->Base'

Actual Adaptation
-----------------

The adapter registry is intended to support adaptation, where one
object that implements an interface is adapted to another object that
supports a different interface.  The adapter registry supports the
computation of adapters. In this case, we have to register adapter
factories:

.. doctest::

   >>> class IR(zope.interface.Interface):
   ...     pass

   >>> @zope.interface.implementer(IR)
   ... class X(object):
   ...     pass

   >>> @zope.interface.implementer(IProvideBase)
   ... class Y(object):
   ...     def __init__(self, context):
   ...         self.context = context

  >>> registry.register([IR], IProvideBase, '', Y)

In this case, we registered a class as the factory. Now we can call
``queryAdapter`` to get the adapted object:

.. doctest::

  >>> x = X()
  >>> y = registry.queryAdapter(x, IProvideBase)
  >>> y.__class__.__name__
  'Y'
  >>> y.context is x
  True

We can register and lookup by name too:

.. doctest::

  >>> class Y2(Y):
  ...     pass

  >>> registry.register([IR], IProvideBase, 'bob', Y2)
  >>> y = registry.queryAdapter(x, IProvideBase, 'bob')
  >>> y.__class__.__name__
  'Y2'
  >>> y.context is x
  True

Passing ``super`` objects works as expected to find less specific adapters:

.. doctest::

  >>> class IDerived(IR):
  ...     pass
  >>> @zope.interface.implementer(IDerived)
  ... class Derived(X):
  ...     pass
  >>> class DerivedAdapter(Y):
  ...     def query_next(self):
  ...        return registry.queryAdapter(
  ...            super(type(self.context), self.context),
  ...            IProvideBase)
  >>> registry.register([IDerived], IProvideBase, '', DerivedAdapter)
  >>> derived = Derived()
  >>> adapter = registry.queryAdapter(derived, IProvideBase)
  >>> adapter.__class__.__name__
  'DerivedAdapter'
  >>> adapter = adapter.query_next()
  >>> adapter.__class__.__name__
  'Y'

When the adapter factory produces ``None``, then this is treated as if no
adapter has been found. This allows us to prevent adaptation (when desired)
and let the adapter factory determine whether adaptation is possible based on
the state of the object being adapted:

.. doctest::

  >>> def factory(context):
  ...     if context.name == 'object':
  ...         return 'adapter'
  ...     return None

  >>> @zope.interface.implementer(IR)
  ... class Object(object):
  ...     name = 'object'

  >>> registry.register([IR], IProvideBase, 'conditional', factory)
  >>> obj = Object()
  >>> registry.queryAdapter(obj, IProvideBase, 'conditional')
  'adapter'
  >>> obj.name = 'no object'
  >>> registry.queryAdapter(obj, IProvideBase, 'conditional') is None
  True
  >>> registry.queryAdapter(obj, IProvideBase, 'conditional', 'default')
  'default'

An alternate method that provides the same function as ``queryAdapter()`` is
`adapter_hook()`:

.. doctest::

  >>> y = registry.adapter_hook(IProvideBase, x)
  >>> y.__class__.__name__
  'Y'
  >>> y.context is x
  True
  >>> y = registry.adapter_hook(IProvideBase, x, 'bob')
  >>> y.__class__.__name__
  'Y2'
  >>> y.context is x
  True

The ``adapter_hook()`` simply switches the order of the object and
interface arguments.  It is used to hook into the interface call
mechanism.


Default Adapters
----------------

Sometimes, you want to provide an adapter that will adapt anything.
For that, provide ``None`` as the required interface:

.. doctest::

  >>> registry.register([None], IProvideBase, '', 1)

then we can use that adapter for interfaces we don't have specific
adapters for:

.. doctest::

  >>> class IQ(zope.interface.Interface):
  ...     pass
  >>> registry.lookup([IQ], IProvideBase, '')
  1

Of course, specific adapters are still used when applicable:

.. doctest::

  >>> registry.lookup([IRequireChild], IProvideBase, '')
  'Child->Base'


Class adapters
--------------

You can register adapters for class declarations, which is almost the
same as registering them for a class:

.. doctest::

  >>> registry.register([zope.interface.implementedBy(C2)], IProvideBase, '', 'C21')
  >>> registry.lookup([zope.interface.implementedBy(C2)], IProvideBase, '')
  'C21'

Dict adapters
-------------

At some point it was impossible to register dictionary-based adapters due a
bug. Let's make sure this works now:

.. doctest::

  >>> adapter = {}
  >>> registry.register((), IQ, '', adapter)
  >>> registry.lookup((), IQ, '') is adapter
  True

Unregistering
-------------

You can unregister by registering ``None``, rather than an object:

.. doctest::

  >>> registry.register([zope.interface.implementedBy(C2)], IProvideBase, '', None)
  >>> registry.lookup([zope.interface.implementedBy(C2)], IProvideBase, '')
  'Child->Base'

Of course, this means that ``None`` can't be registered. This is an
exception to the statement, made earlier, that the registry doesn't
care what gets registered.

Multi-adapters
==============

You can adapt multiple specifications:

.. doctest::

  >>> registry.register([IRequireBase, IQ], IProvideChild, '', '1q2')
  >>> registry.lookup([IRequireBase, IQ], IProvideChild, '')
  '1q2'
  >>> registry.lookup([IRequireChild, IQ], IProvideBase, '')
  '1q2'

  >>> class IS(zope.interface.Interface):
  ...     pass
  >>> registry.lookup([IRequireChild, IS], IProvideBase, '')

  >>> class IQ2(IQ):
  ...     pass

  >>> registry.lookup([IRequireChild, IQ2], IProvideBase, '')
  '1q2'

  >>> registry.register([IRequireBase, IQ2], IProvideChild, '', '(Base,Q2)->Child')
  >>> registry.lookup([IRequireChild, IQ2], IProvideBase, '')
  '(Base,Q2)->Child'

Multi-adaptation
----------------

You can adapt multiple objects:

.. doctest::

  >>> @zope.interface.implementer(IQ)
  ... class Q:
  ...     pass

As with single adapters, we register a factory, which is often a class:

.. doctest::

  >>> class IM(zope.interface.Interface):
  ...     pass
  >>> @zope.interface.implementer(IM)
  ... class M:
  ...     def __init__(self, x, q):
  ...         self.x, self.q = x, q
  >>> registry.register([IR, IQ], IM, '', M)

And then we can call ``queryMultiAdapter`` to compute an adapter:

.. doctest::

  >>> q = Q()
  >>> m = registry.queryMultiAdapter((x, q), IM)
  >>> m.__class__.__name__
  'M'
  >>> m.x is x and m.q is q
  True

and, of course, we can use names:

.. doctest::

  >>> class M2(M):
  ...     pass
  >>> registry.register([IR, IQ], IM, 'bob', M2)
  >>> m = registry.queryMultiAdapter((x, q), IM, 'bob')
  >>> m.__class__.__name__
  'M2'
  >>> m.x is x and m.q is q
  True

Default Adapters
----------------

As with single adapters, you can define default adapters by specifying
``None`` for the *first* specification:

.. doctest::

  >>> registry.register([None, IQ], IProvideChild, '', '(None,Q)->Child')
  >>> registry.lookup([IS, IQ], IProvideChild, '')
  '(None,Q)->Child'

Null Adapters
=============

You can also adapt **no** specification:

.. doctest::

  >>> registry.register([], IProvideChild, '', '[]->Child')
  >>> registry.lookup([], IProvideChild, '')
  '[]->Child'
  >>> registry.lookup([], IProvideBase, '')
  '[]->Child'

Listing named adapters
----------------------

Adapters are named. Sometimes, it's useful to get all of the named
adapters for given interfaces:

.. doctest::

  >>> adapters = list(registry.lookupAll([IRequireBase], IProvideBase))
  >>> adapters.sort()
  >>> assert adapters == [(u'', 'Base->Base'), (u'bob', "Bob's 12")]

This works for multi-adapters too:

.. doctest::

  >>> registry.register([IRequireBase, IQ2], IProvideChild, 'bob', '(Base,Q2)->Child for bob')
  >>> adapters = list(registry.lookupAll([IRequireChild, IQ2], IProvideBase))
  >>> adapters.sort()
  >>> assert adapters == [(u'', '(Base,Q2)->Child'), (u'bob', '(Base,Q2)->Child for bob')]

And even null adapters:

.. doctest::

  >>> registry.register([], IProvideChild, 'bob', 3)
  >>> adapters = list(registry.lookupAll([], IProvideBase))
  >>> adapters.sort()
  >>> assert adapters == [(u'', '[]->Child'), (u'bob', 3)]

Subscriptions
=============

Normally, we want to look up an object that most closely matches a
specification.  Sometimes, we want to get all of the objects that
match some specification.  We use *subscriptions* for this.  We
subscribe objects against specifications and then later find all of
the subscribed objects:

.. doctest::

  >>> registry.subscribe([IRequireBase], IProvideChild, 'Base->Child (1)')
  >>> registry.subscriptions([IRequireBase], IProvideChild)
  ['Base->Child (1)']

Note that, unlike regular adapters, subscriptions are unnamed.

You can have multiple subscribers for the same specification:

.. doctest::

  >>> registry.subscribe([IRequireBase], IProvideChild, 'Base->Child (2)')
  >>> registry.subscriptions([IRequireBase], IProvideChild)
  ['Base->Child (1)', 'Base->Child (2)']

If subscribers are registered for the same required interfaces, they
are returned in the order of definition.

You can register subscribers for all specifications using ``None``:

.. doctest::

  >>> registry.subscribe([None], IProvideBase, 'None->Base')
  >>> registry.subscriptions([IRequireChild], IProvideBase)
  ['None->Base', 'Base->Child (1)', 'Base->Child (2)']

Note that the new subscriber is returned first.

Subscribers defined for less specific required interfaces are returned
before subscribers for more specific interfaces:

.. doctest::

  >>> class IRequireGrandchild(IRequireChild):
  ...     pass
  >>> registry.subscribe([IRequireChild], IProvideBase, 'Child->Base')
  >>> registry.subscribe([IRequireGrandchild], IProvideBase, 'Grandchild->Base')
  >>> registry.subscriptions([IRequireGrandchild], IProvideBase)
  ['None->Base', 'Base->Child (1)', 'Base->Child (2)', 'Child->Base', 'Grandchild->Base']

Subscriptions may be combined over multiple compatible specifications:

.. doctest::

  >>> registry.subscriptions([IRequireChild], IProvideBase)
  ['None->Base', 'Base->Child (1)', 'Base->Child (2)', 'Child->Base']
  >>> registry.subscribe([IRequireBase], IProvideBase, 'Base->Base')
  >>> registry.subscriptions([IRequireChild], IProvideBase)
  ['None->Base', 'Base->Child (1)', 'Base->Child (2)', 'Base->Base', 'Child->Base']
  >>> registry.subscribe([IRequireChild], IProvideChild, 'Child->Child')
  >>> registry.subscriptions([IRequireChild], IProvideBase)
  ['None->Base', 'Base->Child (1)', 'Base->Child (2)', 'Base->Base', 'Child->Child', 'Child->Base']
  >>> registry.subscriptions([IRequireChild], IProvideChild)
  ['Base->Child (1)', 'Base->Child (2)', 'Child->Child']

Subscriptions can be on multiple specifications:

.. doctest::

  >>> registry.subscribe([IRequireBase, IQ], IProvideChild, '(Base,Q)->Child')
  >>> registry.subscriptions([IRequireBase, IQ], IProvideChild)
  ['(Base,Q)->Child']

As with single subscriptions and non-subscription adapters, you can
specify ``None`` for the first required interface, to specify a default:

.. doctest::

  >>> registry.subscribe([None, IQ], IProvideChild, '(None,Q)->Child')
  >>> registry.subscriptions([IS, IQ], IProvideChild)
  ['(None,Q)->Child']
  >>> registry.subscriptions([IRequireBase, IQ], IProvideChild)
  ['(None,Q)->Child', '(Base,Q)->Child']

You can have subscriptions that are independent of any specifications:

.. doctest::

  >>> list(registry.subscriptions([], IProvideBase))
  []

  >>> registry.subscribe([], IProvideChild, 'sub2')
  >>> registry.subscriptions([], IProvideBase)
  ['sub2']
  >>> registry.subscribe([], IProvideBase, 'sub1')
  >>> registry.subscriptions([], IProvideBase)
  ['sub2', 'sub1']
  >>> registry.subscriptions([], IProvideChild)
  ['sub2']

Unregistering subscribers
-------------------------

We can unregister subscribers.  When unregistering a subscriber, we
can unregister a *specific* subscriber:

.. doctest::

  >>> registry.unsubscribe([IRequireBase], IProvideBase, 'Base->Base')
  >>> registry.subscriptions([IRequireBase], IProvideBase)
  ['None->Base', 'Base->Child (1)', 'Base->Child (2)']

If we don't specify a value, then *all* subscribers matching the given
interfaces will be unsubscribed:

.. doctest::

  >>> registry.unsubscribe([IRequireBase], IProvideChild)
  >>> registry.subscriptions([IRequireBase], IProvideBase)
  ['None->Base']


Subscription adapters
---------------------

We normally register adapter factories, which then allow us to compute
adapters, but with subscriptions, we get multiple adapters.  Here's an
example of multiple-object subscribers:

.. doctest::

  >>> registry.subscribe([IR, IQ], IM, M)
  >>> registry.subscribe([IR, IQ], IM, M2)

  >>> subscribers = registry.subscribers((x, q), IM)
  >>> len(subscribers)
  2
  >>> class_names = [s.__class__.__name__ for s in subscribers]
  >>> class_names.sort()
  >>> class_names
  ['M', 'M2']
  >>> [(s.x is x and s.q is q) for s in subscribers]
  [True, True]

Adapter factory subscribers can't return ``None`` values:

.. doctest::

  >>> def M3(x, y):
  ...     return None

  >>> registry.subscribe([IR, IQ], IM, M3)
  >>> subscribers = registry.subscribers((x, q), IM)
  >>> len(subscribers)
  2

Handlers
--------

A handler is a subscriber factory that doesn't produce any normal
output.  It returns ``None``.  A handler is unlike adapters in that it does
all of its work when the factory is called.

To register a handler, simply provide ``None`` as the provided interface:

.. doctest::

  >>> def handler(event):
  ...     print('handler', event)

  >>> registry.subscribe([IRequireBase], None, handler)
  >>> registry.subscriptions([IRequireBase], None) == [handler]
  True


Components
==========

A :class:`zope.interface.registry.Components` object implements the
:class:`zope.interface.interfaces.IComponents` interface. This
interface uses multiple adapter registries to implement multiple
higher-level concerns (utilities, adapters and handlers), while also
providing event notifications and query capabilities.
