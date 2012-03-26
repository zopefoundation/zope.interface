##############################################################################
#
# Copyright (c) 2001, 2002, 2009 Zope Foundation and Contributors.
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
"""Component Registry Tests"""

import types
import unittest

from zope import interface
from zope.interface import implementedBy
from zope.interface.interfaces import ComponentLookupError
from zope.interface.registry import Components

import sys

# fixtures

if sys.version_info[0] == 3:
    _class_types = type
else:
    _class_types = (type, types.ClassType)

class adapter:

    def __init__(self, *interfaces):
        self.interfaces = interfaces

    def __call__(self, ob):
        if isinstance(ob, _class_types):
            ob.__component_adapts__ = _adapts_descr(self.interfaces)
        else:
            ob.__component_adapts__ = self.interfaces

        return ob


def adapts(*interfaces):
    frame = sys._getframe(1)
    locals = frame.f_locals

    # Try to make sure we were called from a class def. In 2.2.0 we can't
    # check for __module__ since it doesn't seem to be added to the locals
    # until later on.
    if (locals is frame.f_globals) or (
        ('__module__' not in locals) and sys.version_info[:3] > (2, 2, 0)):
        raise TypeError("adapts can be used only from a class definition.")

    if '__component_adapts__' in locals:
        raise TypeError("adapts can be used only once in a class definition.")

    locals['__component_adapts__'] = _adapts_descr(interfaces)

class _adapts_descr(object):
    def __init__(self, interfaces):
        self.interfaces = interfaces

    def __get__(self, inst, cls):
        if inst is None:
            return self.interfaces
        raise AttributeError('__component_adapts__')

class I1(interface.Interface):
    pass
class I2(interface.Interface):
    pass
class I2e(I2):
    pass
class I3(interface.Interface):
    pass
class IC(interface.Interface):
    pass

class ITestType(interface.interfaces.IInterface):
    pass

class U:

    def __init__(self, name):
        self.__name__ = name

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.__name__)

class U1(U):
    interface.implements(I1)

class U12(U):
    interface.implements(I1, I2)

class IA1(interface.Interface):
    pass

class IA2(interface.Interface):
    pass

class IA3(interface.Interface):
    pass

class A:

    def __init__(self, *context):
        self.context = context

    def __repr__(self):
        return "%s%r" % (self.__class__.__name__, self.context)

class A12_1(A):
    adapts(I1, I2)
    interface.implements(IA1)

class A12_(A):
    adapts(I1, I2)

class A_2(A):
    interface.implements(IA2)

class A_3(A):
    interface.implements(IA3)

class A1_12(U):
    adapts(I1)
    interface.implements(IA1, IA2)

class A1_2(U):
    adapts(I1)
    interface.implements(IA2)

class A1_23(U):
    adapts(I1)
    interface.implements(IA1, IA3)

def noop(*args):
    pass


# tests

class TestAdapter(unittest.TestCase):

    def setUp(self):
        self.components = Components('comps')

    def test_register_and_unregister_adapter(self):
        self.components.registerAdapter(A12_1)

        multi_adapter = self.components.getMultiAdapter(
            (U1(1), U12(2)), IA1)
        self.assertEqual(multi_adapter.__class__, A12_1)
        self.assertEqual(repr(multi_adapter), 'A12_1(U1(1), U12(2))')

        self.assertTrue(self.components.unregisterAdapter(A12_1))
        self.assertRaises(
            ComponentLookupError,
            self.components.getMultiAdapter,
            (U1(1), U12(2)),
            IA1
            )

    def test_register_and_unregister_adapter_with_two_interfaces(self):
        self.assertRaises(TypeError, self.components.registerAdapter,
                          A1_12)
        self.components.registerAdapter(A1_12,
                                        provided=IA2)

        multi_adapter = self.components.getMultiAdapter((U1(1),), IA2)
        self.assertEqual(multi_adapter.__class__, A1_12)
        self.assertEqual(repr(multi_adapter), 'A1_12(U1(1))')

        self.assertRaises(TypeError, self.components.unregisterAdapter, A1_12)
        self.assertTrue(self.components.unregisterAdapter(A1_12, provided=IA2))
        self.assertRaises(ComponentLookupError,
                          self.components.getMultiAdapter, (U1(1),), IA2)

    def test_register_and_unregister_adapter_with_no_interfaces(self):
        self.assertRaises(TypeError, self.components.registerAdapter, A12_)

        self.components.registerAdapter(A12_, provided=IA2)
        multi_adapter = self.components.getMultiAdapter((U1(1), U12(2)), IA2)
        self.assertEqual(multi_adapter.__class__, A12_)
        self.assertEqual(repr(multi_adapter), 'A12_(U1(1), U12(2))')

        self.assertRaises(TypeError, self.components.unregisterAdapter, A12_)
        self.assertTrue(self.components.unregisterAdapter(A12_, provided=IA2))
        self.assertRaises(ComponentLookupError,
                          self.components.getMultiAdapter, (U1(1), U12(2)), IA2)

    def test_reg_and_unreg_adp_with_no___component_adapts___attribute(self):
        self.assertRaises(TypeError, self.components.registerAdapter, A_2)
        self.components.registerAdapter(A_2, required=[I3])
        self.assertTrue(self.components.unregisterAdapter(A_2, required=[I3]))

    def test_register_and_unregister_class_specific(self):
        self.components.registerAdapter(A_3, required=[U],
                                        info=u'Really class specific')
        self.assertTrue(self.components.unregisterAdapter(required=[U],
                                                          provided=IA3))
      
    def test_registered_adapters_and_sorting(self):
        self.components.registerAdapter(A12_1)
        self.components.registerAdapter(A1_12, provided=IA2)
        self.components.registerAdapter(A12_, provided=IA2)
        self.components.registerAdapter(A_2, required=[I3])
        self.components.registerAdapter(A_3, required=[U],
                                        info=u'Really class specific')

        sorted_adapters = sorted(self.components.registeredAdapters())
        sorted_adapters_name = map(lambda x: getattr(x, 'name'),
                                   sorted_adapters)
        sorted_adapters_provided = map(lambda x: getattr(x, 'provided'),
                                       sorted_adapters) 
        sorted_adapters_required = map(lambda x: getattr(x, 'required'),
                                       sorted_adapters)
        sorted_adapters_info = map(lambda x: getattr(x, 'info'),
                                   sorted_adapters)

        self.assertEqual(len(sorted_adapters), 5)
        self.assertEqual(sorted_adapters_name, [u'', u'', u'', u'', u''])
        self.assertEqual(sorted_adapters_provided, [IA1,
                                                    IA2,
                                                    IA2,
                                                    IA2,
                                                    IA3])

        self.assertEqual(sorted_adapters_required, [(I1, I2),
                                                    (I1, I2),
                                                    (I1,),
                                                    (I3,),
                                                    (implementedBy(U),)])
        self.assertEqual(sorted_adapters_info,
                         [u'', u'', u'', u'', u'Really class specific'])

    def test_get_none_existing_adapter(self):
        self.assertRaises(ComponentLookupError,
                          self.components.getMultiAdapter, (U(1),), IA1)

    def test_query_none_existing_adapter(self):
        self.assertTrue(self.components.queryMultiAdapter((U(1),), IA1) is None)
        self.assertEqual(self.components.queryMultiAdapter((U(1),), IA1,
                                                           default=42), 42)

    def test_unregister_none_existing_adapter(self):
        self.assertFalse(self.components.unregisterAdapter(A_2, required=[I3]))
        self.assertFalse(self.components.unregisterAdapter(A12_1, required=[U]))

    def test_unregister_adapter(self):
        self.components.registerAdapter(A12_1)
        self.components.registerAdapter(A1_12, provided=IA2)
        self.components.registerAdapter(A12_, provided=IA2)
        self.components.registerAdapter(A_2, required=[I3])
        self.components.registerAdapter(A_3, required=[U],
                                        info=u'Really class specific')

        self.assertTrue(self.components.unregisterAdapter(A12_1))
        self.assertTrue(self.components.unregisterAdapter(
            required=[U], provided=IA3))

        sorted_adapters = sorted(self.components.registeredAdapters())
        sorted_adapters_name = map(lambda x: getattr(x, 'name'),
                                   sorted_adapters)
        sorted_adapters_provided = map(lambda x: getattr(x, 'provided'),
                                       sorted_adapters) 
        sorted_adapters_required = map(lambda x: getattr(x, 'required'),
                                       sorted_adapters)
        sorted_adapters_info = map(lambda x: getattr(x, 'info'),
                                   sorted_adapters)

        self.assertEqual(len(sorted_adapters), 3)
        self.assertEqual(sorted_adapters_name, [u'', u'', u''])
        self.assertEqual(sorted_adapters_provided, [IA2,
                                                    IA2,
                                                    IA2])
        self.assertEqual(sorted_adapters_required, [(I1, I2),
                                                    (I1,),
                                                    (I3,)])
        self.assertEqual(sorted_adapters_info, [u'', u'', u''])

    def test_register_named_adapter(self):
        self.components.registerAdapter(A1_12, provided=IA2, name=u'test')
        self.assertTrue(
            self.components.queryMultiAdapter((U1(1),), IA2) is None)
        self.assertEqual(
            repr(self.components.queryMultiAdapter((U1(1),),IA2,name=u'test')),
            'A1_12(U1(1))')

        self.assertTrue(self.components.queryAdapter(U1(1), IA2) is None)
        self.assertEqual(
            repr(self.components.queryAdapter(U1(1), IA2, name=u'test')),
            'A1_12(U1(1))')
        self.assertEqual(
            repr(self.components.getAdapter(U1(1), IA2, name=u'test')),
            'A1_12(U1(1))')

    def test_get_adapters(self):
        self.components.registerAdapter(A1_12, provided=IA1, name=u'test 1')
        self.components.registerAdapter(A1_23, provided=IA2, name=u'test 2')
        self.components.registerAdapter(A1_12, provided=IA2)
        self.components.registerAdapter(A1_12, provided=IA2)

        adapters = list(self.components.getAdapters((U1(1),), IA2))
        self.assertEqual(len(adapters), 2)
        self.assertEqual(adapters[0][0], u'test 2')
        self.assertEqual(adapters[1][0], u'')
        self.assertEqual(repr(adapters[0][1]), 'A1_23(U1(1))')
        self.assertEqual(repr(adapters[1][1]), 'A1_12(U1(1))')

    def test_register_no_factory(self):
        self.components.registerAdapter(A1_12, provided=IA2)
        self.components.registerAdapter(noop, 
                                        required=[IA1], provided=IA2, 
                                        name=u'test noop')

        self.assertTrue(
            self.components.queryAdapter(U1(9), IA2, name=u'test noop') is None)
        adapters = list(self.components.getAdapters((U1(1),), IA2))
        self.assertEqual(len(adapters), 1)
        self.assertEqual(adapters[0][0], u'')
        self.assertEqual(repr(adapters[0][1]), 'A1_12(U1(1))')

        self.assertTrue(self.components.unregisterAdapter(A1_12, provided=IA2))

        sorted_adapters = sorted(self.components.registeredAdapters())
        sorted_adapters_name = map(lambda x: getattr(x, 'name'),
                                   sorted_adapters)
        sorted_adapters_provided = map(lambda x: getattr(x, 'provided'),
                                       sorted_adapters) 
        sorted_adapters_required = map(lambda x: getattr(x, 'required'),
                                       sorted_adapters)
        sorted_adapters_info = map(lambda x: getattr(x, 'info'),
                                   sorted_adapters)

        self.assertEqual(len(sorted_adapters), 1)
        self.assertEqual(sorted_adapters_name, [u'test noop'])
        self.assertEqual(sorted_adapters_provided, [IA2])
        self.assertEqual(sorted_adapters_required, [(IA1,)])
        self.assertEqual(sorted_adapters_info, [u''])


class TestExtending(unittest.TestCase):

    def test_extendning(self):
        c1 = Components('1')
        self.assertEqual(c1.__bases__, ())

        c2 = Components('2', (c1, ))
        self.assertTrue(c2.__bases__ == (c1, ))

        test_object1 = U1(1)
        test_object2 = U1(2)
        test_object3 = U12(1)
        test_object4 = U12(3)

        self.assertEqual(len(list(c1.registeredUtilities())), 0)
        self.assertEqual(len(list(c2.registeredUtilities())), 0)

        c1.registerUtility(test_object1)
        self.assertEqual(len(list(c1.registeredUtilities())), 1)
        self.assertEqual(len(list(c2.registeredUtilities())), 0)
        self.assertEqual(c1.queryUtility(I1), test_object1)
        self.assertEqual(c2.queryUtility(I1), test_object1)

        c1.registerUtility(test_object2)
        self.assertEqual(len(list(c1.registeredUtilities())), 1)
        self.assertEqual(len(list(c2.registeredUtilities())), 0)
        self.assertEqual(c1.queryUtility(I1), test_object2)
        self.assertEqual(c2.queryUtility(I1), test_object2)


        c3 = Components('3', (c1, ))
        c4 = Components('4', (c2, c3))
        self.assertEqual(c4.queryUtility(I1), test_object2)
    
        c1.registerUtility(test_object3, I2)
        self.assertEqual(c4.queryUtility(I2), test_object3)

        c3.registerUtility(test_object4, I2)
        self.assertEqual(c4.queryUtility(I2), test_object4)

        @adapter(I1)
        def handle1(x):
            self.assertEqual(x, test_object1)

        def handle(*objects):
            self.assertEqual(objects, (test_object1,))

        @adapter(I1)
        def handle3(x):
            self.assertEqual(x, test_object1)

        @adapter(I1)
        def handle4(x):
            self.assertEqual(x, test_object1)

        c1.registerHandler(handle1, info=u'First handler')
        c2.registerHandler(handle, required=[U])
        c3.registerHandler(handle3)
        c4.registerHandler(handle4)

        c4.handle(test_object1)

class TestHandler(unittest.TestCase):

    def setUp(self):
        self.components = Components('comps')

    def test_register_handler(self):
        test_object1 = U1(1)
        test_object2 = U12(2)

        @adapter(I1)
        def handle1(x):
            self.assertEqual(x, test_object1)

        self.components.registerHandler(handle1, info=u'First handler')
        self.components.handle(test_object1)

        @adapter(I1, I2)
        def handle12(x, y):
            self.assertEqual(x, test_object1)
            self.assertEqual(y, test_object2)

        self.components.registerHandler(handle12)
        self.components.handle(test_object1, test_object2)

    def test_register_noncompliant_handler(self):
        handle_calls = []
        def handle(*objects):
            handle_calls.append(objects)

        self.assertRaises(TypeError, self.components.registerHandler, handle)
        self.components.registerHandler(
            handle, required=[I1], info=u'a comment')
        self.components.registerHandler(
            handle, required=[U], info=u'handle a class')

        test_object = U1(1)
        self.components.handle(test_object)
        self.assertEqual(len(handle_calls), 2)
        map(self.assertEqual, handle_calls, [(test_object,), (test_object,)])

    def test_list_handlers(self):
        test_object1 = U1(1)
        test_object2 = U12(2)

        @adapter(I1)
        def handle1(x):
            self.assertEqual(x, test_object1)

        @adapter(I1, I2)
        def handle12(x, y):
            self.assertEqual(x, test_object1)
            self.assertEqual(y, test_object2)

        handle_calls = []
        def handle(*objects):
            handle_calls.append(objects)

        self.components.registerHandler(handle1, info=u'First handler')
        self.components.registerHandler(handle12)
        self.components.registerHandler(
            handle, required=[I1], info=u'a comment')
        self.components.registerHandler(
            handle, required=[U], info=u'handle a class')

        handlers = list(self.components.registeredHandlers())
        handlers_required = map(lambda x: getattr(x, 'required'), handlers)
        handlers_handler = map(lambda x: getattr(x, 'handler'), handlers)
        handlers_info = map(lambda x: getattr(x, 'info'), handlers)

        self.assertEqual(len(handlers), 4)
        self.assertEqual(handlers_required,
                         [(I1,), (I1, I2), (I1,), (implementedBy(U),)])
        self.assertEqual(handlers_handler,
                         [handle1, handle12, handle, handle])
        self.assertEqual(
            handlers_info,
            [u'First handler', u'', u'a comment', u'handle a class'])

    def test_unregister_handler(self):
        test_object1 = U1(1)
        test_object2 = U12(2)

        @adapter(I1)
        def handle1(x):
            self.assertEqual(x, test_object1)

        @adapter(I1, I2)
        def handle12(x, y):
            self.assertEqual(x, test_object1)
            self.assertEqual(y, test_object2)

        handle_calls = []
        def handle(*objects):
            handle_calls.append(objects)

        self.components.registerHandler(handle1, info=u'First handler')
        self.components.registerHandler(handle12)
        self.components.registerHandler(
            handle, required=[I1], info=u'a comment')
        self.components.registerHandler(
            handle, required=[U], info=u'handle a class')

        self.assertEqual(len(list(self.components.registeredHandlers())), 4)
        self.assertTrue(self.components.unregisterHandler(handle12))
        self.assertEqual(len(list(self.components.registeredHandlers())), 3)
        self.assertFalse(self.components.unregisterHandler(handle12))
        self.assertEqual(len(list(self.components.registeredHandlers())), 3)
        self.assertRaises(TypeError, self.components.unregisterHandler)
        self.assertEqual(len(list(self.components.registeredHandlers())), 3)
        self.assertTrue(
            self.components.unregisterHandler(handle, required=[I1]))
        self.assertEqual(len(list(self.components.registeredHandlers())), 2)
        self.assertTrue(self.components.unregisterHandler(handle, required=[U]))
        self.assertEqual(len(list(self.components.registeredHandlers())), 1)

    def test_multi_handler_unregistration(self):
        """
        There was a bug where multiple handlers for the same required
        specification would all be removed when one of them was
        unregistered.

        """
        from zope import interface

        calls = []

        class I(interface.Interface):
            pass

        def factory1(event):
            calls.append(2)

        def factory2(event):
            calls.append(3)

        class Event(object):
            interface.implements(I)

        self.components.registerHandler(factory1, [I,])
        self.components.registerHandler(factory2, [I,])
        self.components.handle(Event())
        self.assertEqual(sum(calls), 5)
        self.assertTrue(self.components.unregisterHandler(factory1, [I,]))
        calls = []
        self.components.handle(Event())
        self.assertEqual(sum(calls), 3)

class TestSubscriber(unittest.TestCase):

    def setUp(self):
        self.components = Components('comps')

    def test_register_subscriber(self):
        self.components.registerSubscriptionAdapter(A1_2)
        self.components.registerSubscriptionAdapter(A1_12, provided=IA2)
        self.components.registerSubscriptionAdapter(
            A, [I1], IA2, info='a sample comment')
        subscribers = self.components.subscribers((U1(1),), IA2)
        self.assertEqual(len(subscribers), 3)
        self.assertEqual(repr(subscribers[0]), 'A1_2(U1(1))')
        self.assertEqual(repr(subscribers[1]), 'A1_12(U1(1))')
        self.assertEqual(repr(subscribers[2]), 'A(U1(1),)') 

    def test_register_noncompliant_subscriber(self):
        self.assertRaises(TypeError,
                          self.components.registerSubscriptionAdapter, A1_12)
        self.assertRaises(TypeError,
                          self.components.registerSubscriptionAdapter, A)
        self.assertRaises(
            TypeError,
            self.components.registerSubscriptionAdapter, A, required=[IA1])

    def test_register_named_subscriber(self):
        self.components.registerSubscriptionAdapter(
            A, [I1], IA2, u'', u'a sample comment')
        self.assertRaises(TypeError,
                          self.components.registerSubscriptionAdapter, 
                          A, [I1], IA2, u'oops', u'a sample comment')
        subscribers = self.components.subscribers((U1(1),), IA2)
        self.assertEqual(len(subscribers), 1)
        self.assertEqual(repr(subscribers[0]), 'A(U1(1),)')

    def test_register_no_factory(self):
        self.components.registerSubscriptionAdapter(noop, [I1], IA2)
        subscribers = self.components.subscribers((U1(1),), IA2)
        self.assertEqual(len(subscribers), 0)

    def test_sorting_registered_subscription_adapters(self):
        self.components.registerSubscriptionAdapter(A1_2)
        self.components.registerSubscriptionAdapter(A1_12, provided=IA2)
        self.components.registerSubscriptionAdapter(
            A, [I1], IA2, info=u'a sample comment')
        self.components.registerSubscriptionAdapter(
            A, [I1], IA2, u'', u'a sample comment')
        self.components.registerSubscriptionAdapter(noop, [I1], IA2)

        sorted_subscribers = sorted(
            self.components.registeredSubscriptionAdapters())
        sorted_subscribers_name = map(lambda x: getattr(x, 'name'),
                                      sorted_subscribers)
        sorted_subscribers_provided = map(lambda x: getattr(x, 'provided'),
                                          sorted_subscribers) 
        sorted_subscribers_required = map(lambda x: getattr(x, 'required'),
                                          sorted_subscribers)
        sorted_subscribers_factory = map(lambda x: getattr(x, 'factory'),
                                         sorted_subscribers)
        sorted_subscribers_info = map(lambda x: getattr(x, 'info'),
                                      sorted_subscribers)

        self.assertEqual(len(sorted_subscribers), 5)
        self.assertEqual(sorted_subscribers_name, [u'', u'', u'', u'', u''])
        self.assertEqual(sorted_subscribers_provided,
                         [IA2, IA2, IA2, IA2, IA2])
        self.assertEqual(sorted_subscribers_required,
                         [(I1,), (I1,), (I1,),(I1,), (I1,)])
        self.assertEqual(sorted_subscribers_factory,
                         [A, A, A1_12, A1_2, noop])
        self.assertEqual(
            sorted_subscribers_info,
            [u'a sample comment', u'a sample comment', u'', u'', u''])

    def test_unregister(self):
        self.components.registerSubscriptionAdapter(A1_2)
        self.assertEqual(len(self.components.subscribers((U1(1),), IA2)), 1)
        self.assertTrue(self.components.unregisterSubscriptionAdapter(A1_2))
        self.assertEqual(len(self.components.subscribers((U1(1),), IA2)), 0)

    def test_unregister_multiple(self):
        self.components.registerSubscriptionAdapter(A1_2)
        self.components.registerSubscriptionAdapter(A1_12, provided=IA2)
        self.components.registerSubscriptionAdapter(
            A, [I1], IA2, info=u'a sample comment')
        self.components.registerSubscriptionAdapter(
            A, [I1], IA2, u'', u'a sample comment')
        self.components.registerSubscriptionAdapter(noop, [I1], IA2)
        self.assertEqual(len(self.components.subscribers((U1(1),), IA2)), 4)
        self.assertEqual(
            len(list(self.components.registeredSubscriptionAdapters())), 5)

        self.assertTrue(
            self.components.unregisterSubscriptionAdapter(A, [I1], IA2))
        self.assertEqual(len(self.components.subscribers((U1(1),), IA2)), 2)
        self.assertEqual(
            len(list(self.components.registeredSubscriptionAdapters())), 3)

    def test_unregister_no_factory(self):
        self.components.registerSubscriptionAdapter(A1_2)
        self.components.registerSubscriptionAdapter(A1_12, provided=IA2)
        self.components.registerSubscriptionAdapter(noop, [I1], IA2)
        self.assertEqual(len(self.components.subscribers((U1(1),), IA2)), 2)
        self.assertEqual(
            len(list(self.components.registeredSubscriptionAdapters())), 3)

        self.assertRaises(
            TypeError,
            self.components.unregisterSubscriptionAdapter, required=[I1])
        self.assertRaises(
            TypeError,
            self.components.unregisterSubscriptionAdapter, provided=IA2)
        self.assertTrue(
            self.components.unregisterSubscriptionAdapter(
                required=[I1], provided=IA2))
        self.assertEqual(len(self.components.subscribers((U1(1),), IA2)), 0)
        self.assertEqual(
            len(list(self.components.registeredSubscriptionAdapters())), 0)

    def test_unregister_noncompliant_subscriber(self):
        self.assertRaises(
            TypeError,
            self.components.unregisterSubscriptionAdapter, A1_12)
        self.assertRaises(
            TypeError,
            self.components.unregisterSubscriptionAdapter, A)
        self.assertRaises(
            TypeError,
            self.components.unregisterSubscriptionAdapter, A, required=[IA1])

    def test_unregister_nonexistent_subscriber(self):
        self.assertFalse(
            self.components.unregisterSubscriptionAdapter(required=[I1],
                                                          provided=IA2))

class TestUtility(unittest.TestCase):

    def setUp(self):
        self.components = Components('comps')

    def test_register_utility(self):
        test_object = U1(1)
        self.components.registerUtility(test_object)
        self.assertEqual(self.components.getUtility(I1), test_object)

    def test_register_utility_with_factory(self):
        test_object = U1(1)
        def factory():
           return test_object
        self.components.registerUtility(factory=factory)
        self.assertEqual(self.components.getUtility(I1), test_object)
        self.assertTrue(self.components.unregisterUtility(factory=factory))

    def test_register_utility_with_component_and_factory(self):
        def factory():
            return U1(1)
        self.assertRaises(
            TypeError,
            self.components.registerUtility, U1(1), factory=factory)

    def test_unregister_utility_with_and_without_component_and_factory(self):
        def factory():
            return U1(1)
        self.assertRaises(
            TypeError,
            self.components.unregisterUtility, U1(1), factory=factory)
        self.assertRaises(TypeError, self.components.unregisterUtility)

    def test_register_utility_with_no_interfaces(self):
        self.assertRaises(TypeError, self.components.registerUtility, A)

    def test_register_utility_with_two_interfaces(self):
        self.assertRaises(TypeError, self.components.registerUtility, U12(1))

    def test_register_utility_with_arguments(self):
        test_object1 = U12(1)
        test_object2 = U12(2)
        self.components.registerUtility(test_object1, I2)
        self.components.registerUtility(test_object2, I2, 'name')
        self.assertEqual(self.components.getUtility(I2), test_object1)
        self.assertEqual(self.components.getUtility(I2, 'name'), test_object2)

    def test_get_none_existing_utility(self):
        from zope.interface.interfaces import ComponentLookupError
        self.assertRaises(ComponentLookupError, self.components.getUtility, I3)

    def test_query_none_existing_utility(self):
        self.assertTrue(self.components.queryUtility(I3) is None)
        self.assertEqual(self.components.queryUtility(I3, default=42), 42)

    def test_registered_utilities_and_sorting(self):
        test_object1 = U1(1)
        test_object2 = U12(2)
        test_object3 = U12(3)
        self.components.registerUtility(test_object1)
        self.components.registerUtility(test_object3, I2, u'name')
        self.components.registerUtility(test_object2, I2)

        sorted_utilities = sorted(self.components.registeredUtilities())
        sorted_utilities_name = map(lambda x: getattr(x, 'name'),
                                    sorted_utilities)
        sorted_utilities_component = map(lambda x: getattr(x, 'component'),
                                         sorted_utilities)
        sorted_utilities_provided = map(lambda x: getattr(x, 'provided'),
                                        sorted_utilities)

        self.assertEqual(len(sorted_utilities), 3)
        self.assertEqual(sorted_utilities_name, [u'', u'', u'name'])
        self.assertEqual(
            sorted_utilities_component,
            [test_object1, test_object2, test_object3])
        self.assertEqual(sorted_utilities_provided, [I1, I2, I2])

    def test_duplicate_utility(self):
        test_object1 = U1(1)
        test_object2 = U12(2)
        test_object3 = U12(3)
        test_object4 = U1(4)
        self.components.registerUtility(test_object1)
        self.components.registerUtility(test_object2, I2)
        self.components.registerUtility(test_object3, I2, u'name')
        self.assertEqual(self.components.getUtility(I1), test_object1)

        self.components.registerUtility(test_object4, info=u'use 4 now')
        self.assertEqual(self.components.getUtility(I1), test_object4)

    def test_unregister_utility(self):
        test_object = U1(1)
        self.components.registerUtility(test_object)
        self.assertEqual(self.components.getUtility(I1), test_object)
        self.assertTrue(self.components.unregisterUtility(provided=I1))
        self.assertFalse(self.components.unregisterUtility(provided=I1))

    def test_unregister_utility_extended(self):
        test_object = U1(1)
        self.components.registerUtility(test_object)
        self.assertFalse(self.components.unregisterUtility(U1(1)))
        self.assertEqual(self.components.queryUtility(I1), test_object)
        self.assertTrue(self.components.unregisterUtility(test_object))
        self.assertTrue(self.components.queryUtility(I1) is None)

    def test_get_utilities_for(self):
        test_object1 = U1(1)
        test_object2 = U12(2)
        test_object3 = U12(3)
        self.components.registerUtility(test_object1)
        self.components.registerUtility(test_object2, I2)
        self.components.registerUtility(test_object3, I2, u'name')

        sorted_utilities = sorted(self.components.getUtilitiesFor(I2))
        self.assertEqual(len(sorted_utilities), 2)
        self.assertEqual(sorted_utilities[0], (u'', test_object2))
        self.assertEqual(sorted_utilities[1], (u'name', test_object3))

    def test_get_all_utilities_registered_for(self):
        test_object1 = U1(1)
        test_object2 = U12(2)
        test_object3 = U12(3)
        test_object4 = U('ext')
        self.components.registerUtility(test_object1)
        self.components.registerUtility(test_object2, I2)
        self.components.registerUtility(test_object3, I2, u'name')
        self.components.registerUtility(test_object4, I2e)

        sorted_utilities = sorted(self.components.getUtilitiesFor(I2))
        self.assertEqual(len(sorted_utilities), 2)
        self.assertEqual(sorted_utilities[0], (u'', test_object2))
        self.assertEqual(sorted_utilities[1], (u'name', test_object3))

        all_utilities = self.components.getAllUtilitiesRegisteredFor(I2)
        self.assertEqual(len(all_utilities), 3)
        self.assertTrue(test_object2 in all_utilities)
        self.assertTrue(test_object3 in all_utilities)
        self.assertTrue(test_object4 in all_utilities)

        self.assertTrue(self.components.unregisterUtility(test_object4, I2e))
        self.assertEqual(self.components.getAllUtilitiesRegisteredFor(I2e), [])

    def test_utility_events(self):
        from zope.event import subscribers
        old_subscribers = subscribers[:]
        subscribers[:] = []

        test_object = U1(1)
        def log_event(event):
            self.assertEqual(event.object.component, test_object)
        subscribers.append(log_event)
        self.components.registerUtility(test_object)

        subscribers[:] = old_subscribers

    def test_dont_leak_utility_registrations_in__subscribers(self):
        """
        We've observed utilities getting left in _subscribers when they
        get unregistered.

        """
        class C:
            def __init__(self, name):
                self.name = name
            def __repr__(self):
                return "C(%s)" % self.name

        c1 = C(1)
        c2 = C(2)

        self.components.registerUtility(c1, I1)
        self.components.registerUtility(c1, I1)
        utilities = list(self.components.getAllUtilitiesRegisteredFor(I1))
        self.assertEqual(len(utilities), 1)
        self.assertEqual(utilities[0], c1)

        self.assertTrue(self.components.unregisterUtility(provided=I1))
        utilities = list(self.components.getAllUtilitiesRegisteredFor(I1))
        self.assertEqual(len(utilities), 0)

        self.components.registerUtility(c1, I1)
        self.components.registerUtility(c2, I1)

        utilities = list(self.components.getAllUtilitiesRegisteredFor(I1))
        self.assertEqual(len(utilities), 1)
        self.assertEqual(utilities[0], c2)


class TestExtending(unittest.TestCase):

    def test_extendning(self):
        c1 = Components('1')
        self.assertEqual(c1.__bases__, ())

        c2 = Components('2', (c1, ))
        self.assertTrue(c2.__bases__ == (c1, ))

        test_object1 = U1(1)
        test_object2 = U1(2)
        test_object3 = U12(1)
        test_object4 = U12(3)

        self.assertEqual(len(list(c1.registeredUtilities())), 0)
        self.assertEqual(len(list(c2.registeredUtilities())), 0)

        c1.registerUtility(test_object1)
        self.assertEqual(len(list(c1.registeredUtilities())), 1)
        self.assertEqual(len(list(c2.registeredUtilities())), 0)
        self.assertEqual(c1.queryUtility(I1), test_object1)
        self.assertEqual(c2.queryUtility(I1), test_object1)

        c1.registerUtility(test_object2)
        self.assertEqual(len(list(c1.registeredUtilities())), 1)
        self.assertEqual(len(list(c2.registeredUtilities())), 0)
        self.assertEqual(c1.queryUtility(I1), test_object2)
        self.assertEqual(c2.queryUtility(I1), test_object2)


        c3 = Components('3', (c1, ))
        c4 = Components('4', (c2, c3))
        self.assertEqual(c4.queryUtility(I1), test_object2)
    
        c1.registerUtility(test_object3, I2)
        self.assertEqual(c4.queryUtility(I2), test_object3)

        c3.registerUtility(test_object4, I2)
        self.assertEqual(c4.queryUtility(I2), test_object4)

        @adapter(I1)
        def handle1(x):
            self.assertEqual(x, test_object1)

        def handle(*objects):
            self.assertEqual(objects, (test_object1,))

        @adapter(I1)
        def handle3(x):
            self.assertEqual(x, test_object1)

        @adapter(I1)
        def handle4(x):
            self.assertEqual(x, test_object1)

        c1.registerHandler(handle1, info=u'First handler')
        c2.registerHandler(handle, required=[U])
        c3.registerHandler(handle3)
        c4.registerHandler(handle4)

        c4.handle(test_object1)

def test_suite():
    return unittest.TestSuite((
            unittest.makeSuite(TestUtility),
            unittest.makeSuite(TestAdapter),
            unittest.makeSuite(TestSubscriber),
            unittest.makeSuite(TestHandler),
            unittest.makeSuite(TestExtending)
        ))
