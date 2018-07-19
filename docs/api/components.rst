======================
 Component Registries
======================

The component registry's API is defined by
``zope.interface.interfaces.IComponents``:

.. autointerface:: zope.interface.interfaces.IComponentLookup
   :members:
   :member-order: bysource


.. autointerface:: zope.interface.interfaces.IComponentRegistry
   :members:
   :member-order: bysource

.. autointerface:: zope.interface.interfaces.IComponents
   :members:
   :member-order: bysource

One default implementation of `~zope.interface.interfaces.IComponents` is provided.

.. autoclass:: zope.interface.registry.Components

Events
======

Adding and removing components from the component registry create
registration and unregistration events. Like most things, they are
defined by an interface and a default implementation is provided.

Registration
------------

.. autointerface:: zope.interface.interfaces.IObjectEvent
.. autointerface:: zope.interface.interfaces.IRegistrationEvent

.. autointerface:: zope.interface.interfaces.IRegistered
.. autoclass:: zope.interface.interfaces.Registered

.. autointerface:: zope.interface.interfaces.IUnregistered
.. autoclass:: zope.interface.interfaces.Unregistered


Details
-------

These are all types of ``IObjectEvent``, meaning they have an object
that provides specific details about the event. Component registries
create detail objects for four types of components they manage.

All four share a common base interface.

.. autointerface:: zope.interface.interfaces.IRegistration

* Utilties

  .. autointerface:: zope.interface.interfaces.IUtilityRegistration
  .. autoclass:: zope.interface.registry.UtilityRegistration

* Handlers

  .. autointerface:: zope.interface.interfaces.IHandlerRegistration
  .. autoclass:: zope.interface.registry.HandlerRegistration

* Adapters

  For ease of implementation, a shared base class is used for these
  events. It should not be referenced by clients, but it is documented
  to show the common attributes.

  .. autointerface:: zope.interface.interfaces._IBaseAdapterRegistration

  .. autointerface:: zope.interface.interfaces.IAdapterRegistration
  .. autoclass:: zope.interface.registry.AdapterRegistration

  .. autointerface:: zope.interface.interfaces.ISubscriptionAdapterRegistration
  .. autoclass:: zope.interface.registry.SubscriptionRegistration

Exceptions
==========

.. autoclass:: zope.interface.interfaces.ComponentLookupError
.. autoclass:: zope.interface.interfaces.Invalid
