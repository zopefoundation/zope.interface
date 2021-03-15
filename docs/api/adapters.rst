==================
 Adapter Registry
==================

Usage of the adapter registry is documented in :ref:`adapter-registry`.


The adapter registry's API is defined by
:class:`zope.interface.interfaces.IAdapterRegistry`:

.. autointerface:: zope.interface.interfaces.IAdapterRegistry
   :members:
   :member-order: bysource


The concrete implementations of ``IAdapterRegistry`` provided by this
package allows for some customization opportunities.

.. autoclass:: zope.interface.adapter.BaseAdapterRegistry
   :members:
   :private-members:

.. autoclass:: zope.interface.adapter.AdapterRegistry
   :members:

.. autoclass:: zope.interface.adapter.VerifyingAdapterRegistry
   :members:
