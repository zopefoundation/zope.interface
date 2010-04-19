##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
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
"""Test Interface implementation
"""
import unittest
import doctest

class InterfaceTests(unittest.TestCase):

    def test_attributes_link_to_interface(self):
        from zope.interface import Interface
        from zope.interface import Attribute

        class I1(Interface):
            attr = Attribute("My attr")

        self.failUnless(I1['attr'].interface is I1)

    def test_methods_link_to_interface(self):
        from zope.interface import Interface

        class I1(Interface):

            def method(foo, bar, bingo):
                pass

        self.failUnless(I1['method'].interface is I1)

    def test_classImplements_simple(self):
        from zope.interface import Interface
        from zope.interface import implementedBy
        from zope.interface import providedBy

        class ICurrent(Interface):
            def method1(a, b):
                pass
            def method2(a, b):
                pass

        class IOther(Interface):
            pass

        class Current(object):
            __implemented__ = ICurrent
            def method1(self, a, b):
                return 1
            def method2(self, a, b):
                return 2

        current = Current()

        self.failUnless(ICurrent.implementedBy(Current))
        self.failIf(IOther.implementedBy(Current))
        self.failUnless(ICurrent in implementedBy(Current))
        self.failIf(IOther in implementedBy(Current))
        self.failUnless(ICurrent in providedBy(current))
        self.failIf(IOther in providedBy(current))

    def test_classImplements_base_not_derived(self):
        from zope.interface import Interface
        from zope.interface import implementedBy
        from zope.interface import providedBy
        class IBase(Interface):
            def method():
                pass
        class IDerived(IBase):
            pass
        class Current():
            __implemented__ = IBase
            def method(self):
                pass
        current = Current()

        self.failUnless(IBase.implementedBy(Current))
        self.failIf(IDerived.implementedBy(Current))
        self.failUnless(IBase in implementedBy(Current))
        self.failIf(IDerived in implementedBy(Current))
        self.failUnless(IBase in providedBy(current))
        self.failIf(IDerived in providedBy(current))

    def test_classImplements_base_and_derived(self):
        from zope.interface import Interface
        from zope.interface import implementedBy
        from zope.interface import providedBy

        class IBase(Interface):
            def method():
                pass

        class IDerived(IBase):
            pass

        class Current(object):
            __implemented__ = IDerived
            def method(self):
                pass

        current = Current()

        self.failUnless(IBase.implementedBy(Current))
        self.failUnless(IDerived.implementedBy(Current))
        self.failIf(IBase in implementedBy(Current))
        self.failUnless(IBase in implementedBy(Current).flattened())
        self.failUnless(IDerived in implementedBy(Current))
        self.failIf(IBase in providedBy(current))
        self.failUnless(IBase in providedBy(current).flattened())
        self.failUnless(IDerived in providedBy(current))

    def test_classImplements_multiple(self):
        from zope.interface import Interface
        from zope.interface import implementedBy
        from zope.interface import providedBy

        class ILeft(Interface):
            def method():
                pass

        class IRight(ILeft):
            pass

        class Left(object):
            __implemented__ = ILeft

            def method(self):
                pass

        class Right(object):
            __implemented__ = IRight

        class Ambi(Left, Right):
            pass

        ambi = Ambi()

        self.failUnless(ILeft.implementedBy(Ambi))
        self.failUnless(IRight.implementedBy(Ambi))
        self.failUnless(ILeft in implementedBy(Ambi))
        self.failUnless(IRight in implementedBy(Ambi))
        self.failUnless(ILeft in providedBy(ambi))
        self.failUnless(IRight in providedBy(ambi))

    def test_classImplements_multiple_w_explict_implements(self):
        from zope.interface import Interface
        from zope.interface import implementedBy
        from zope.interface import providedBy

        class ILeft(Interface):

            def method():
                pass

        class IRight(ILeft):
            pass

        class IOther(Interface):
            pass

        class Left():
            __implemented__ = ILeft

            def method(self):
                pass

        class Right(object):
            __implemented__ = IRight

        class Other(object):
            __implemented__ = IOther

        class Mixed(Left, Right):
            __implemented__ = Left.__implemented__, Other.__implemented__

        mixed = Mixed()

        self.failUnless(ILeft.implementedBy(Mixed))
        self.failIf(IRight.implementedBy(Mixed))
        self.failUnless(IOther.implementedBy(Mixed))
        self.failUnless(ILeft in implementedBy(Mixed))
        self.failIf(IRight in implementedBy(Mixed))
        self.failUnless(IOther in implementedBy(Mixed))
        self.failUnless(ILeft in providedBy(mixed))
        self.failIf(IRight in providedBy(mixed))
        self.failUnless(IOther in providedBy(mixed))

    def test_interface_deferred_class_method_broken(self):
        from zope.interface import Interface
        from zope.interface.exceptions import BrokenImplementation

        class IDeferring(Interface):
            def method():
                pass

        class Deferring(IDeferring.deferred()):
            __implemented__ = IDeferring

        deferring = Deferring()

        self.assertRaises(BrokenImplementation, deferring.method)

    def testInterfaceExtendsInterface(self):
        from zope.interface import Interface

        new = Interface.__class__
        FunInterface = new('FunInterface')
        BarInterface = new('BarInterface', [FunInterface])
        BobInterface = new('BobInterface')
        BazInterface = new('BazInterface', [BobInterface, BarInterface])

        self.failUnless(BazInterface.extends(BobInterface))
        self.failUnless(BazInterface.extends(BarInterface))
        self.failUnless(BazInterface.extends(FunInterface))
        self.failIf(BobInterface.extends(FunInterface))
        self.failIf(BobInterface.extends(BarInterface))
        self.failUnless(BarInterface.extends(FunInterface))
        self.failIf(BarInterface.extends(BazInterface))

    def test_verifyClass(self):
        from zope.interface import Attribute
        from zope.interface import Interface
        from zope.interface.verify import verifyClass

        class ICheckMe(Interface):
            attr = Attribute(u'My attr')

            def method():
                pass

        class CheckMe(object):
            __implemented__ = ICheckMe
            attr = 'value'

            def method(self):
                pass

        self.failUnless(verifyClass(ICheckMe, CheckMe))

    def test_verifyObject(self):
        from zope.interface import Attribute
        from zope.interface import Interface
        from zope.interface.verify import verifyObject

        class ICheckMe(Interface):
            attr = Attribute(u'My attr')

            def method():
                pass

        class CheckMe(object):
            __implemented__ = ICheckMe
            attr = 'value'

            def method(self):
                pass

        check_me = CheckMe()

        self.failUnless(verifyObject(ICheckMe, check_me))

    def test_interface_object_provides_Interface(self):
        from zope.interface import Interface

        class AnInterface(Interface):
            pass

        self.assert_(Interface.providedBy(AnInterface))

    def test_names_simple(self):
        from zope.interface import Attribute
        from zope.interface import Interface

        class ISimple(Interface):
            attr = Attribute(u'My attr')

            def method():
                pass

        self.assertEqual(sorted(ISimple.names()), ['attr', 'method'])

    def test_names_derived(self):
        from zope.interface import Attribute
        from zope.interface import Interface

        class IBase(Interface):
            attr = Attribute(u'My attr')

            def method():
                pass

        class IDerived(IBase):
            attr2 = Attribute(u'My attr')

            def method():
                pass

            def method2():
                pass

        self.assertEqual(sorted(IDerived.names()),
                         ['attr2', 'method', 'method2'])
        self.assertEqual(sorted(IDerived.names(all=True)),
                         ['attr', 'attr2', 'method', 'method2'])

    def test_namesAndDescriptions_simple(self):
        from zope.interface import Attribute
        from zope.interface.interface import Method
        from zope.interface import Interface

        class ISimple(Interface):
            attr = Attribute(u'My attr')

            def method():
                "My method"

        name_values = sorted(ISimple.namesAndDescriptions())

        self.assertEqual(len(name_values), 2)
        self.assertEqual(name_values[0][0], 'attr')
        self.failUnless(isinstance(name_values[0][1], Attribute))
        self.assertEqual(name_values[0][1].__name__, 'attr')
        self.assertEqual(name_values[0][1].__doc__, 'My attr')
        self.assertEqual(name_values[1][0], 'method')
        self.failUnless(isinstance(name_values[1][1], Method))
        self.assertEqual(name_values[1][1].__name__, 'method')
        self.assertEqual(name_values[1][1].__doc__, 'My method')

    def test_namesAndDescriptions_derived(self):
        from zope.interface import Attribute
        from zope.interface import Interface
        from zope.interface.interface import Method

        class IBase(Interface):
            attr = Attribute(u'My attr')

            def method():
                "My method"

        class IDerived(IBase):
            attr2 = Attribute(u'My attr2')

            def method():
                "My method, overridden"

            def method2():
                "My method2"

        name_values = sorted(IDerived.namesAndDescriptions())

        self.assertEqual(len(name_values), 3)
        self.assertEqual(name_values[0][0], 'attr2')
        self.failUnless(isinstance(name_values[0][1], Attribute))
        self.assertEqual(name_values[0][1].__name__, 'attr2')
        self.assertEqual(name_values[0][1].__doc__, 'My attr2')
        self.assertEqual(name_values[1][0], 'method')
        self.failUnless(isinstance(name_values[1][1], Method))
        self.assertEqual(name_values[1][1].__name__, 'method')
        self.assertEqual(name_values[1][1].__doc__, 'My method, overridden')
        self.assertEqual(name_values[2][0], 'method2')
        self.failUnless(isinstance(name_values[2][1], Method))
        self.assertEqual(name_values[2][1].__name__, 'method2')
        self.assertEqual(name_values[2][1].__doc__, 'My method2')

        name_values = sorted(IDerived.namesAndDescriptions(all=True))

        self.assertEqual(len(name_values), 4)
        self.assertEqual(name_values[0][0], 'attr')
        self.failUnless(isinstance(name_values[0][1], Attribute))
        self.assertEqual(name_values[0][1].__name__, 'attr')
        self.assertEqual(name_values[0][1].__doc__, 'My attr')
        self.assertEqual(name_values[1][0], 'attr2')
        self.failUnless(isinstance(name_values[1][1], Attribute))
        self.assertEqual(name_values[1][1].__name__, 'attr2')
        self.assertEqual(name_values[1][1].__doc__, 'My attr2')
        self.assertEqual(name_values[2][0], 'method')
        self.failUnless(isinstance(name_values[2][1], Method))
        self.assertEqual(name_values[2][1].__name__, 'method')
        self.assertEqual(name_values[2][1].__doc__, 'My method, overridden')
        self.assertEqual(name_values[3][0], 'method2')
        self.failUnless(isinstance(name_values[3][1], Method))
        self.assertEqual(name_values[3][1].__name__, 'method2')
        self.assertEqual(name_values[3][1].__doc__, 'My method2')

    def test_getDescriptionFor_nonesuch_no_default(self):
        from zope.interface import Interface

        class IEmpty(Interface):
            pass

        self.assertRaises(KeyError, IEmpty.getDescriptionFor, 'nonesuch')

    def test_getDescriptionFor_simple(self):
        from zope.interface import Attribute
        from zope.interface.interface import Method
        from zope.interface import Interface

        class ISimple(Interface):
            attr = Attribute(u'My attr')

            def method():
                "My method"

        a_desc = ISimple.getDescriptionFor('attr')
        self.failUnless(isinstance(a_desc, Attribute))
        self.assertEqual(a_desc.__name__, 'attr')
        self.assertEqual(a_desc.__doc__, 'My attr')

        m_desc = ISimple.getDescriptionFor('method')
        self.failUnless(isinstance(m_desc, Method))
        self.assertEqual(m_desc.__name__, 'method')
        self.assertEqual(m_desc.__doc__, 'My method')

    def test_getDescriptionFor_derived(self):
        from zope.interface import Attribute
        from zope.interface.interface import Method
        from zope.interface import Interface

        class IBase(Interface):
            attr = Attribute(u'My attr')

            def method():
                "My method"

        class IDerived(IBase):
            attr2 = Attribute(u'My attr2')

            def method():
                "My method, overridden"

            def method2():
                "My method2"

        a_desc = IDerived.getDescriptionFor('attr')
        self.failUnless(isinstance(a_desc, Attribute))
        self.assertEqual(a_desc.__name__, 'attr')
        self.assertEqual(a_desc.__doc__, 'My attr')

        m_desc = IDerived.getDescriptionFor('method')
        self.failUnless(isinstance(m_desc, Method))
        self.assertEqual(m_desc.__name__, 'method')
        self.assertEqual(m_desc.__doc__, 'My method, overridden')

        a2_desc = IDerived.getDescriptionFor('attr2')
        self.failUnless(isinstance(a2_desc, Attribute))
        self.assertEqual(a2_desc.__name__, 'attr2')
        self.assertEqual(a2_desc.__doc__, 'My attr2')

        m2_desc = IDerived.getDescriptionFor('method2')
        self.failUnless(isinstance(m2_desc, Method))
        self.assertEqual(m2_desc.__name__, 'method2')
        self.assertEqual(m2_desc.__doc__, 'My method2')

    def test___getitem__nonesuch(self):
        from zope.interface import Interface

        class IEmpty(Interface):
            pass

        self.assertRaises(KeyError, IEmpty.__getitem__, 'nonesuch')

    def test___getitem__simple(self):
        from zope.interface import Attribute
        from zope.interface.interface import Method
        from zope.interface import Interface

        class ISimple(Interface):
            attr = Attribute(u'My attr')

            def method():
                "My method"

        a_desc = ISimple['attr']
        self.failUnless(isinstance(a_desc, Attribute))
        self.assertEqual(a_desc.__name__, 'attr')
        self.assertEqual(a_desc.__doc__, 'My attr')

        m_desc = ISimple['method']
        self.failUnless(isinstance(m_desc, Method))
        self.assertEqual(m_desc.__name__, 'method')
        self.assertEqual(m_desc.__doc__, 'My method')

    def test___getitem___derived(self):
        from zope.interface import Attribute
        from zope.interface.interface import Method
        from zope.interface import Interface

        class IBase(Interface):
            attr = Attribute(u'My attr')

            def method():
                "My method"

        class IDerived(IBase):
            attr2 = Attribute(u'My attr2')

            def method():
                "My method, overridden"

            def method2():
                "My method2"

        a_desc = IDerived['attr']
        self.failUnless(isinstance(a_desc, Attribute))
        self.assertEqual(a_desc.__name__, 'attr')
        self.assertEqual(a_desc.__doc__, 'My attr')

        m_desc = IDerived['method']
        self.failUnless(isinstance(m_desc, Method))
        self.assertEqual(m_desc.__name__, 'method')
        self.assertEqual(m_desc.__doc__, 'My method, overridden')

        a2_desc = IDerived['attr2']
        self.failUnless(isinstance(a2_desc, Attribute))
        self.assertEqual(a2_desc.__name__, 'attr2')
        self.assertEqual(a2_desc.__doc__, 'My attr2')

        m2_desc = IDerived['method2']
        self.failUnless(isinstance(m2_desc, Method))
        self.assertEqual(m2_desc.__name__, 'method2')
        self.assertEqual(m2_desc.__doc__, 'My method2')

    def test___contains__nonesuch(self):
        from zope.interface import Interface

        class IEmpty(Interface):
            pass

        self.failIf('nonesuch' in IEmpty)

    def test___contains__simple(self):
        from zope.interface import Attribute
        from zope.interface import Interface

        class ISimple(Interface):
            attr = Attribute(u'My attr')

            def method():
                "My method"

        self.failUnless('attr' in ISimple)
        self.failUnless('method' in ISimple)

    def test___contains__derived(self):
        from zope.interface import Attribute
        from zope.interface import Interface

        class IBase(Interface):
            attr = Attribute(u'My attr')

            def method():
                "My method"

        class IDerived(IBase):
            attr2 = Attribute(u'My attr2')

            def method():
                "My method, overridden"

            def method2():
                "My method2"

        self.failUnless('attr' in IDerived)
        self.failUnless('method' in IDerived)
        self.failUnless('attr2' in IDerived)
        self.failUnless('method2' in IDerived)

    def test___iter__empty(self):
        from zope.interface import Interface

        class IEmpty(Interface):
            pass

        self.assertEqual(list(IEmpty), [])

    def test___iter__simple(self):
        from zope.interface import Attribute
        from zope.interface import Interface

        class ISimple(Interface):
            attr = Attribute(u'My attr')

            def method():
                "My method"

        self.assertEqual(sorted(list(ISimple)), ['attr', 'method'])

    def test___iter__derived(self):
        from zope.interface import Attribute
        from zope.interface import Interface

        class IBase(Interface):
            attr = Attribute(u'My attr')

            def method():
                "My method"

        class IDerived(IBase):
            attr2 = Attribute(u'My attr2')

            def method():
                "My method, overridden"

            def method2():
                "My method2"

        self.assertEqual(sorted(list(IDerived)),
                         ['attr', 'attr2', 'method', 'method2'])

    def test_function_attributes_become_tagged_values(self):
        from zope.interface import Interface

        class ITagMe(Interface):
            def method():
                pass
            method.optional = 1

        method = ITagMe['method']
        self.assertEqual(method.getTaggedValue('optional'), 1)

    def test___doc___non_element(self):
        from zope.interface import Interface

        class IHaveADocString(Interface):
            "xxx"

        self.assertEqual(IHaveADocString.__doc__, "xxx")
        self.assertEqual(list(IHaveADocString), [])

    def test___doc___as_element(self):
        from zope.interface import Attribute
        from zope.interface import Interface

        class IHaveADocString(Interface):
            "xxx"
            __doc__ = Attribute('the doc')

        self.assertEqual(IHaveADocString.__doc__, "")
        self.assertEqual(list(IHaveADocString), ['__doc__'])

    def _errorsEqual(self, has_invariant, error_len, error_msgs, iface):
        from zope.interface.exceptions import Invalid
        self.assertRaises(Invalid, iface.validateInvariants, has_invariant)
        e = []
        try:
            iface.validateInvariants(has_invariant, e)
        except Invalid, error:
            self.assertEquals(error.args[0], e)
        else:
            self._assert(0) # validateInvariants should always raise
            # Invalid
        self.assertEquals(len(e), error_len)
        msgs = [error.args[0] for error in e]
        msgs.sort()
        for msg in msgs:
            self.assertEquals(msg, error_msgs.pop(0))

    def test_invariant_simple(self):
        from zope.interface import Attribute
        from zope.interface import Interface
        from zope.interface import directlyProvides
        from zope.interface import invariant

        class IInvariant(Interface):
            foo = Attribute('foo')
            bar = Attribute('bar; must eval to Boolean True if foo does')
            invariant(_ifFooThenBar)

        class HasInvariant(object):
            pass

        # set up
        has_invariant = HasInvariant()
        directlyProvides(has_invariant, IInvariant)
        # the tests
        self.assertEquals(IInvariant.getTaggedValue('invariants'),
                          [_ifFooThenBar])
        self.assertEquals(IInvariant.validateInvariants(has_invariant), None)
        has_invariant.bar = 27
        self.assertEquals(IInvariant.validateInvariants(has_invariant), None)
        has_invariant.foo = 42
        self.assertEquals(IInvariant.validateInvariants(has_invariant), None)
        del has_invariant.bar
        self._errorsEqual(has_invariant, 1, ['If Foo, then Bar!'],
                          IInvariant)

    def test_invariant_nested(self):
        from zope.interface import Attribute
        from zope.interface import Interface
        from zope.interface import directlyProvides
        from zope.interface import invariant

        class IInvariant(Interface):
            foo = Attribute('foo')
            bar = Attribute('bar; must eval to Boolean True if foo does')
            invariant(_ifFooThenBar)

        class ISubInvariant(IInvariant):
            invariant(_barGreaterThanFoo)

        class HasInvariant(object):
            pass

        # nested interfaces with invariants:
        self.assertEquals(ISubInvariant.getTaggedValue('invariants'),
                          [_barGreaterThanFoo])
        has_invariant = HasInvariant()
        directlyProvides(has_invariant, ISubInvariant)
        has_invariant.foo = 42
        # even though the interface has changed, we should still only have one
        # error.
        self._errorsEqual(has_invariant, 1, ['If Foo, then Bar!'],
                          ISubInvariant)
        # however, if we set foo to 0 (Boolean False) and bar to a negative
        # number then we'll get the new error
        has_invariant.foo = 2
        has_invariant.bar = 1
        self._errorsEqual(has_invariant, 1,
                          ['Please, Boo MUST be greater than Foo!'],
                          ISubInvariant)
        # and if we set foo to a positive number and boo to 0, we'll
        # get both errors!
        has_invariant.foo = 1
        has_invariant.bar = 0
        self._errorsEqual(has_invariant, 2,
                          ['If Foo, then Bar!',
                           'Please, Boo MUST be greater than Foo!'],
                          ISubInvariant)
        # for a happy ending, we'll make the invariants happy
        has_invariant.foo = 1
        has_invariant.bar = 2
        self.assertEquals(IInvariant.validateInvariants(has_invariant), None)

    def test_invariant_mutandis(self):
        from zope.interface import Attribute
        from zope.interface import Interface
        from zope.interface import directlyProvides
        from zope.interface import invariant

        class IInvariant(Interface):
            foo = Attribute('foo')
            bar = Attribute('bar; must eval to Boolean True if foo does')
            invariant(_ifFooThenBar)

        class HasInvariant(object):
            pass

        # now we'll do two invariants on the same interface,
        # just to make sure that a small
        # multi-invariant interface is at least minimally tested.
        has_invariant = HasInvariant()
        directlyProvides(has_invariant, IInvariant)
        has_invariant.foo = 42

        # if you really need to mutate, then this would be the way to do it.
        # Probably a bad idea, though. :-)
        old_invariants = IInvariant.getTaggedValue('invariants')
        invariants = old_invariants[:]
        invariants.append(_barGreaterThanFoo)
        IInvariant.setTaggedValue('invariants', invariants)

        # even though the interface has changed, we should still only have one
        # error.
        self._errorsEqual(has_invariant, 1, ['If Foo, then Bar!'],
                          IInvariant)
        # however, if we set foo to 0 (Boolean False) and bar to a negative
        # number then we'll get the new error
        has_invariant.foo = 2
        has_invariant.bar = 1
        self._errorsEqual(has_invariant, 1,
                         ['Please, Boo MUST be greater than Foo!'], IInvariant)
        # and if we set foo to a positive number and boo to 0, we'll
        # get both errors!
        has_invariant.foo = 1
        has_invariant.bar = 0
        self._errorsEqual(has_invariant, 2,
                          ['If Foo, then Bar!',
                           'Please, Boo MUST be greater than Foo!'],
                          IInvariant)
        # for another happy ending, we'll make the invariants happy again
        has_invariant.foo = 1
        has_invariant.bar = 2
        self.assertEquals(IInvariant.validateInvariants(has_invariant), None)

    def testIssue228(self):
        # Test for http://collector.zope.org/Zope3-dev/228
        # Old style classes don't have a '__class__' attribute
        import sys
        if sys.version[0] < '3':
            # No old style classes in Python 3, so the test becomes moot.
            from zope.interface import Interface

            class I(Interface):
                "xxx"

            class OldStyle:
                __providedBy__ = None

            self.assertRaises(AttributeError, I.providedBy, OldStyle)

    def test_invariant_as_decorator(self):
        from zope.interface import Interface
        from zope.interface import Attribute
        from zope.interface import implements
        from zope.interface import invariant
        from zope.interface.exceptions import Invalid

        class IRange(Interface):
            min = Attribute("Lower bound")
            max = Attribute("Upper bound")
            
            @invariant
            def range_invariant(ob):
                if ob.max < ob.min:
                    raise Invalid('max < min')

        class Range(object):
            implements(IRange)

            def __init__(self, min, max):
                self.min, self.max = min, max

        IRange.validateInvariants(Range(1,2))
        IRange.validateInvariants(Range(1,1))
        try:
            IRange.validateInvariants(Range(2,1))
        except Invalid, e:
            self.assertEqual(str(e), 'max < min')

    def test_description_cache_management(self):
        # See https://bugs.launchpad.net/zope.interface/+bug/185974
        # There was a bug where the cache used by Specification.get() was not
        # cleared when the bases were changed.
        from zope.interface import Interface
        from zope.interface import Attribute

        class I1(Interface):
            a = Attribute('a')

        class I2(I1):
            pass

        class I3(I2):
            pass

        self.failUnless(I3.get('a') is I1.get('a'))

        I2.__bases__ = (Interface,)
        self.failUnless(I3.get('a') is None)

def _barGreaterThanFoo(obj):
    from zope.interface.exceptions import Invalid
    foo = getattr(obj, 'foo', None)
    bar = getattr(obj, 'bar', None)
    if foo is not None and isinstance(foo, type(bar)):
        # type checking should be handled elsewhere (like, say, 
        # schema); these invariants should be intra-interface 
        # constraints.  This is a hacky way to do it, maybe, but you
        # get the idea
        if not bar > foo:
            raise Invalid('Please, Boo MUST be greater than Foo!')

def _ifFooThenBar(obj):
    from zope.interface.exceptions import Invalid
    if getattr(obj, 'foo', None) and not getattr(obj, 'bar', None):
        raise Invalid('If Foo, then Bar!')




def test_suite():
    suite = unittest.makeSuite(InterfaceTests)
    suite.addTest(doctest.DocTestSuite())
    suite.addTest(doctest.DocTestSuite("zope.interface.interface"))
    return suite
