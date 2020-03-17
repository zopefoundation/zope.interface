===========================================
 Computing The Resolution Order (Priority)
===========================================

Just as Python classes have a method resolution order that determines
which implementation of a method gets used when inheritance is used,
interfaces have a resolution order that determines their ordering when
searching for adapters.

That order is computed by ``zope.interface.ro.ro``. This is an
internal module not generally needed by a user of ``zope.interface``,
but its documentation can be helpful to understand how orders are
computed.

``zope.interface.ro``
=====================

.. automodule:: zope.interface.ro
   :member-order: alphabetical
