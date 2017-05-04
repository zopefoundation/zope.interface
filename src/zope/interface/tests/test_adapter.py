##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Adapter registry tests

$Id$
"""
import doctest
import unittest
import zope.interface
from zope.interface.adapter import AdapterRegistry


class IF0(zope.interface.Interface):
    pass
class IF1(IF0):
    pass

class IB0(zope.interface.Interface):
    pass
class IB1(IB0):
    pass

class IR0(zope.interface.Interface):
    pass
class IR1(IR0):
    pass

def test_multi_adapter_get_best_match():
    """
    >>> registry = AdapterRegistry()

    >>> class IB2(IB0):
    ...     pass
    >>> class IB3(IB2, IB1):
    ...     pass
    >>> class IB4(IB1, IB2):
    ...     pass

    >>> registry.register([None, IB1], IR0, '', 'A1')
    >>> registry.register([None, IB0], IR0, '', 'A0')
    >>> registry.register([None, IB2], IR0, '', 'A2')

    >>> registry.lookup((IF1, IB1), IR0, '')
    'A1'
    >>> registry.lookup((IF1, IB2), IR0, '')
    'A2'
    >>> registry.lookup((IF1, IB0), IR0, '')
    'A0'
    >>> registry.lookup((IF1, IB3), IR0, '')
    'A2'
    >>> registry.lookup((IF1, IB4), IR0, '')
    'A1'
    """

def test_multi_adapter_lookupAll_get_best_matches():
    """
    >>> registry = AdapterRegistry()

    >>> class IB2(IB0):
    ...     pass
    >>> class IB3(IB2, IB1):
    ...     pass
    >>> class IB4(IB1, IB2):
    ...     pass

    >>> registry.register([None, IB1], IR0, '', 'A1')
    >>> registry.register([None, IB0], IR0, '', 'A0')
    >>> registry.register([None, IB2], IR0, '', 'A2')

    >>> tuple(registry.lookupAll((IF1, IB1), IR0))[0][1]
    'A1'
    >>> tuple(registry.lookupAll((IF1, IB2), IR0))[0][1]
    'A2'
    >>> tuple(registry.lookupAll((IF1, IB0), IR0))[0][1]
    'A0'
    >>> tuple(registry.lookupAll((IF1, IB3), IR0))[0][1]
    'A2'
    >>> tuple(registry.lookupAll((IF1, IB4), IR0))[0][1]
    'A1'
    """


def test_multi_adapter_w_default():
    """
    >>> registry = AdapterRegistry()

    >>> registry.register([None, None], IB1, 'bob', 'A0')

    >>> registry.lookup((IF1, IR1), IB0, 'bob')
    'A0'

    >>> registry.register([None, IR0], IB1, 'bob', 'A1')

    >>> registry.lookup((IF1, IR1), IB0, 'bob')
    'A1'

    >>> registry.lookup((IF1, IR1), IB0, 'bruce')

    >>> registry.register([None, IR1], IB1, 'bob', 'A2')
    >>> registry.lookup((IF1, IR1), IB0, 'bob')
    'A2'
    """

def test_multi_adapter_w_inherited_and_multiple_registrations():
    """
    >>> registry = AdapterRegistry()

    >>> class IX(zope.interface.Interface):
    ...    pass

    >>> registry.register([IF0, IR0], IB1, 'bob', 'A1')
    >>> registry.register([IF1, IX], IB1, 'bob', 'AX')

    >>> registry.lookup((IF1, IR1), IB0, 'bob')
    'A1'
    """

def test_named_adapter_with_default():
    """Query a named simple adapter

    >>> registry = AdapterRegistry()

    If we ask for a named adapter, we won't get a result unless there
    is a named adapter, even if the object implements the interface:

    >>> registry.lookup([IF1], IF0, 'bob')

    >>> registry.register([None], IB1, 'bob', 'A1')
    >>> registry.lookup([IF1], IB0, 'bob')
    'A1'

    >>> registry.lookup([IF1], IB0, 'bruce')

    >>> registry.register([None], IB0, 'bob', 'A2')
    >>> registry.lookup([IF1], IB0, 'bob')
    'A2'
    """

def test_multi_adapter_gets_closest_provided():
    """
    >>> registry = AdapterRegistry()
    >>> registry.register([IF1, IR0], IB0, 'bob', 'A1')
    >>> registry.register((IF1, IR0), IB1, 'bob', 'A2')
    >>> registry.lookup((IF1, IR1), IB0, 'bob')
    'A1'

    >>> registry = AdapterRegistry()
    >>> registry.register([IF1, IR0], IB1, 'bob', 'A2')
    >>> registry.register([IF1, IR0], IB0, 'bob', 'A1')
    >>> registry.lookup([IF1, IR0], IB0, 'bob')
    'A1'

    >>> registry = AdapterRegistry()
    >>> registry.register([IF1, IR0], IB0, 'bob', 'A1')
    >>> registry.register([IF1, IR1], IB1, 'bob', 'A2')
    >>> registry.lookup([IF1, IR1], IB0, 'bob')
    'A2'

    >>> registry = AdapterRegistry()
    >>> registry.register([IF1, IR1], IB1, 'bob', 2)
    >>> registry.register([IF1, IR0], IB0, 'bob', 1)
    >>> registry.lookup([IF1, IR1], IB0, 'bob')
    2
    """

def test_multi_adapter_check_non_default_dont_hide_default():
    """
    >>> registry = AdapterRegistry()

    >>> class IX(zope.interface.Interface):
    ...     pass


    >>> registry.register([None, IR0], IB0, 'bob', 1)
    >>> registry.register([IF1,   IX], IB0, 'bob', 2)
    >>> registry.lookup([IF1, IR1], IB0, 'bob')
    1
    """

def test_adapter_hook_with_factory_producing_None():
    """
    >>> registry = AdapterRegistry()
    >>> default = object()

    >>> class Object1(object):
    ...     zope.interface.implements(IF0)
    >>> class Object2(object):
    ...     zope.interface.implements(IF0)

    >>> def factory(context):
    ...     if isinstance(context, Object1):
    ...         return 'adapter'
    ...     return None

    >>> registry.register([IF0], IB0, '', factory)

    >>> registry.adapter_hook(IB0, Object1())
    'adapter'
    >>> registry.adapter_hook(IB0, Object2()) is None
    True
    >>> registry.adapter_hook(IB0, Object2(), default=default) is default
    True
    """

def test_adapter_registry_update_upon_interface_bases_change():
    """
    Let's first create a adapter registry and a simple adaptation hook:

    >>> globalRegistry = AdapterRegistry()

    >>> def _hook(iface, ob, lookup=globalRegistry.lookup1):
    ...     factory = lookup(zope.interface.providedBy(ob), iface)
    ...     if factory is None:
    ...         return None
    ...     else:
    ...         return factory(ob)

    >>> zope.interface.interface.adapter_hooks.append(_hook)

    Now we create some interfaces and an implementation:

    >>> class IX(zope.interface.Interface):
    ...   pass

    >>> class IY(zope.interface.Interface):
    ...   pass

    >>> class X(object):
    ...  pass

    >>> class Y(object):
    ...  zope.interface.implements(IY)
    ...  def __init__(self, original):
    ...   self.original=original

    and register an adapter:

    >>> globalRegistry.register((IX,), IY, '', Y)

    at first, we still expect the adapter lookup from `X` to `IY` to fail:

    >>> IY(X()) #doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    Traceback (most recent call last):
    ...
    TypeError: ('Could not adapt',
                <zope.interface.tests.test_adapter.X object at ...>,
                <InterfaceClass zope.interface.tests.test_adapter.IY>)

    But after we declare an interface on the class `X`, it should pass:

    >>> zope.interface.classImplementsOnly(X, IX)

    >>> IY(X()) #doctest: +ELLIPSIS
    <zope.interface.tests.test_adapter.Y object at ...>

    >>> hook = zope.interface.interface.adapter_hooks.pop()
    """


def test_changing_declarations():
    """

    If we change declarations for a class, those adapter lookup should
    eflect the changes:

    >>> class I1(zope.interface.Interface):
    ...     pass
    >>> class I2(zope.interface.Interface):
    ...     pass

    >>> registry = AdapterRegistry()
    >>> registry.register([I1], I2, '', 42)

    >>> class C:
    ...     pass

    >>> registry.lookup([zope.interface.implementedBy(C)], I2, '')

    >>> zope.interface.classImplements(C, I1)

    >>> registry.lookup([zope.interface.implementedBy(C)], I2, '')
    42
    """

def test_lookup_failure():
    """
    >>> registry = AdapterRegistry()
    >>> registry.register((), IF0, '', 42)
    >>> def subsequent_lookup():
    ...     print registry.lookup((), IF0, None)
    ...     print registry.lookup((), IF0)
    >>> subsequent_lookup()
    None
    42
    """

def test_correct_multi_adapter_lookup():
    """
    >>> registry = AdapterRegistry()
    >>> registry.register([IF0, IB1], IR0, '', 'A01')
    >>> registry.register([IF1, IB0], IR0, '', 'A10')
    >>> registry.lookup((IF1, IB1), IR0, '')
    'A10'
    """

def test_duplicate_bases():
    """
There was a bug that caused problems if a spec had multiple bases:

    >>> class I(zope.interface.Interface):
    ...     pass
    >>> class I2(I, I):
    ...     pass
    >>> registry = AdapterRegistry()
    >>> registry.register([I2], IR0, 'x', 'X')
    >>> registry.lookup((I2, ), IR0, 'x')
    'X'
    >>> registry.register([I2], IR0, 'y', 'Y')
    >>> registry.lookup((I2, ), IR0, 'x')
    'X'
    >>> registry.lookup((I2, ), IR0, 'y')
    'Y'
"""

def test_register_objects_with_cmp():
    """
    The registry should never use == as that will tend to fail when
    objects are picky about what they are compared with:

    >>> class Picky:
    ...     def __cmp__(self, other):
    ...         raise TypeError("I\'m too picky for comparison!")
    >>> class I(zope.interface.Interface):
    ...     pass
    >>> class I2(I, I):
    ...     pass

    >>> registry = AdapterRegistry()
    >>> picky = Picky()
    >>> registry.register([I2], IR0, '', picky)
    >>> registry.unregister([I2], IR0, '', picky)

    >>> registry.subscribe([I2], IR0, picky)
    >>> registry.unsubscribe([I2], IR0, picky)

    """

def test_unregister_cleans_up_empties():
    """
    >>> class I(zope.interface.Interface):
    ...     pass
    >>> class IP(zope.interface.Interface):
    ...     pass
    >>> class C(object):
    ...     pass

    >>> registry = AdapterRegistry()

    >>> registry.register([], IP, '', C)
    >>> registry.register([I], IP, '', C)
    >>> registry.register([I], IP, 'name', C)
    >>> registry.register([I, I], IP, '', C)
    >>> len(registry._adapters)
    3
    >>> map(len, registry._adapters)
    [1, 1, 1]

    >>> registry.unregister([], IP, '', C)
    >>> registry.unregister([I], IP, '', C)
    >>> registry.unregister([I], IP, 'name', C)
    >>> registry.unregister([I, I], IP, '', C)
    >>> registry._adapters
    []

    """

def test_unsubscribe_cleans_up_empties():
    """
    >>> class I1(zope.interface.Interface):
    ...     pass
    >>> class I2(zope.interface.Interface):
    ...     pass
    >>> class IP(zope.interface.Interface):
    ...     pass

    >>> registry = AdapterRegistry()
    >>> def handler(event):
    ...     pass

    >>> registry.subscribe([I1], I1, handler)
    >>> registry.subscribe([I2], I1, handler)
    >>> len(registry._subscribers)
    2
    >>> map(len, registry._subscribers)
    [0, 2]

    >>> registry.unsubscribe([I1], I1, handler)
    >>> registry.unsubscribe([I2], I1, handler)
    >>> registry._subscribers
    []

    """


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('../adapter.txt', '../adapter.ru.txt',
                                 '../human.txt', '../human.ru.txt',
                                 'foodforthought.txt',
                                 globs={'__name__': '__main__'}),
        doctest.DocTestSuite(),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
