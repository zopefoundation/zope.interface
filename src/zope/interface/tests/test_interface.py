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
import doctest
import unittest
import sys

class InterfaceTests(unittest.TestCase):

    def _makeDerivedInterface(self):
        from zope.interface import Interface
        from zope.interface import Attribute
        class _I1(Interface):

            a1 = Attribute("This is an attribute")

            def f11():
                pass
            def f12():
                pass
            f12.optional = 1

        class _I1_(_I1):
            pass

        class _I1__(_I1_):
            pass

        class _I2(_I1__):
            def f21():
                pass
            def f22():
                pass
            f23 = f22

        return _I2

    def testInterfaceSetOnAttributes(self):
        from zope.interface.tests.unitfixtures import FooInterface
        self.assertEqual(FooInterface['foobar'].interface,
                         FooInterface)
        self.assertEqual(FooInterface['aMethod'].interface,
                         FooInterface)

    def testClassImplements(self):
        from zope.interface.tests.unitfixtures import A
        from zope.interface.tests.unitfixtures import B
        from zope.interface.tests.unitfixtures import C
        from zope.interface.tests.unitfixtures import D
        from zope.interface.tests.unitfixtures import E
        from zope.interface.tests.unitfixtures import I1
        from zope.interface.tests.unitfixtures import I2
        from zope.interface.tests.unitfixtures import IC
        self.assert_(IC.implementedBy(C))

        self.assert_(I1.implementedBy(A))
        self.assert_(I1.implementedBy(B))
        self.assert_(not I1.implementedBy(C))
        self.assert_(I1.implementedBy(D))
        self.assert_(I1.implementedBy(E))

        self.assert_(not I2.implementedBy(A))
        self.assert_(I2.implementedBy(B))
        self.assert_(not I2.implementedBy(C))

        # No longer after interfacegeddon
        # self.assert_(not I2.implementedBy(D))

        self.assert_(not I2.implementedBy(E))

    def testUtil(self):
        from zope.interface import implementedBy
        from zope.interface import providedBy
        from zope.interface.tests.unitfixtures import A
        from zope.interface.tests.unitfixtures import B
        from zope.interface.tests.unitfixtures import C
        from zope.interface.tests.unitfixtures import I1
        from zope.interface.tests.unitfixtures import I2
        from zope.interface.tests.unitfixtures import IC
        self.assert_(IC in implementedBy(C))
        self.assert_(I1 in implementedBy(A))
        self.assert_(not I1 in implementedBy(C))
        self.assert_(I2 in implementedBy(B))
        self.assert_(not I2 in implementedBy(C))

        self.assert_(IC in providedBy(C()))
        self.assert_(I1 in providedBy(A()))
        self.assert_(not I1 in providedBy(C()))
        self.assert_(I2 in providedBy(B()))
        self.assert_(not I2 in providedBy(C()))


    def testObjectImplements(self):
        from zope.interface.tests.unitfixtures import A
        from zope.interface.tests.unitfixtures import B
        from zope.interface.tests.unitfixtures import C
        from zope.interface.tests.unitfixtures import D
        from zope.interface.tests.unitfixtures import E
        from zope.interface.tests.unitfixtures import I1
        from zope.interface.tests.unitfixtures import I2
        from zope.interface.tests.unitfixtures import IC
        self.assert_(IC.providedBy(C()))

        self.assert_(I1.providedBy(A()))
        self.assert_(I1.providedBy(B()))
        self.assert_(not I1.providedBy(C()))
        self.assert_(I1.providedBy(D()))
        self.assert_(I1.providedBy(E()))

        self.assert_(not I2.providedBy(A()))
        self.assert_(I2.providedBy(B()))
        self.assert_(not I2.providedBy(C()))

        # Not after interface geddon
        # self.assert_(not I2.providedBy(D()))

        self.assert_(not I2.providedBy(E()))

    def testDeferredClass(self):
        from zope.interface.tests.unitfixtures import A
        from zope.interface.exceptions import BrokenImplementation
        a = A()
        self.assertRaises(BrokenImplementation, a.ma)


    def testInterfaceExtendsInterface(self):
        from zope.interface.tests.unitfixtures import BazInterface
        from zope.interface.tests.unitfixtures import BarInterface
        from zope.interface.tests.unitfixtures import BobInterface
        from zope.interface.tests.unitfixtures import FunInterface
        self.assert_(BazInterface.extends(BobInterface))
        self.assert_(BazInterface.extends(BarInterface))
        self.assert_(BazInterface.extends(FunInterface))
        self.assert_(not BobInterface.extends(FunInterface))
        self.assert_(not BobInterface.extends(BarInterface))
        self.assert_(BarInterface.extends(FunInterface))
        self.assert_(not BarInterface.extends(BazInterface))

    def testVerifyImplementation(self):
        from zope.interface.verify import verifyClass
        from zope.interface import Interface
        from zope.interface.tests.unitfixtures import Foo
        from zope.interface.tests.unitfixtures import FooInterface
        from zope.interface.tests.unitfixtures import I1
        self.assert_(verifyClass(FooInterface, Foo))
        self.assert_(Interface.providedBy(I1))

    def test_names(self):
        iface = self._makeDerivedInterface()
        names = list(iface.names())
        names.sort()
        self.assertEqual(names, ['f21', 'f22', 'f23'])
        all = list(iface.names(all=True))
        all.sort()
        self.assertEqual(all, ['a1', 'f11', 'f12', 'f21', 'f22', 'f23'])

    def test_namesAndDescriptions(self):
        iface = self._makeDerivedInterface()
        names = [nd[0] for nd in iface.namesAndDescriptions()]
        names.sort()
        self.assertEqual(names, ['f21', 'f22', 'f23'])
        names = [nd[0] for nd in iface.namesAndDescriptions(1)]
        names.sort()
        self.assertEqual(names, ['a1', 'f11', 'f12', 'f21', 'f22', 'f23'])

        for name, d in iface.namesAndDescriptions(1):
            self.assertEqual(name, d.__name__)

    def test_getDescriptionFor(self):
        iface = self._makeDerivedInterface()
        self.assertEqual(iface.getDescriptionFor('f11').__name__, 'f11')
        self.assertEqual(iface.getDescriptionFor('f22').__name__, 'f22')
        self.assertEqual(iface.queryDescriptionFor('f33', self), self)
        self.assertRaises(KeyError, iface.getDescriptionFor, 'f33')

    def test___getitem__(self):
        iface = self._makeDerivedInterface()
        self.assertEqual(iface['f11'].__name__, 'f11')
        self.assertEqual(iface['f22'].__name__, 'f22')
        self.assertEqual(iface.get('f33', self), self)
        self.assertRaises(KeyError, iface.__getitem__, 'f33')

    def test___contains__(self):
        iface = self._makeDerivedInterface()
        self.failUnless('f11' in iface)
        self.failIf('f33' in iface)

    def test___iter__(self):
        iface = self._makeDerivedInterface()
        names = list(iter(iface))
        names.sort()
        self.assertEqual(names, ['a1', 'f11', 'f12', 'f21', 'f22', 'f23'])

    def testAttr(self):
        iface = self._makeDerivedInterface()
        description = iface.getDescriptionFor('a1')
        self.assertEqual(description.__name__, 'a1')
        self.assertEqual(description.__doc__, 'This is an attribute')

    def testFunctionAttributes(self):
        # Make sure function attributes become tagged values.
        from zope.interface import Interface
        class ITest(Interface):
            def method():
                pass
            method.optional = 1

        method = ITest['method']
        self.assertEqual(method.getTaggedValue('optional'), 1)

    def testInvariant(self):
        from zope.interface.exceptions import Invalid
        from zope.interface import directlyProvides
        from zope.interface.tests.unitfixtures import BarGreaterThanFoo
        from zope.interface.tests.unitfixtures import ifFooThenBar
        from zope.interface.tests.unitfixtures import IInvariant
        from zope.interface.tests.unitfixtures import InvariantC
        from zope.interface.tests.unitfixtures import ISubInvariant
        # set up
        o = InvariantC()
        directlyProvides(o, IInvariant)
        # a helper
        def errorsEqual(self, o, error_len, error_msgs, iface=None):
            if iface is None:
                iface = IInvariant
            self.assertRaises(Invalid, iface.validateInvariants, o)
            e = []
            try:
                iface.validateInvariants(o, e)
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
        # the tests
        self.assertEquals(IInvariant.getTaggedValue('invariants'),
                          [ifFooThenBar])
        self.assertEquals(IInvariant.validateInvariants(o), None)
        o.bar = 27
        self.assertEquals(IInvariant.validateInvariants(o), None)
        o.foo = 42
        self.assertEquals(IInvariant.validateInvariants(o), None)
        del o.bar
        errorsEqual(self, o, 1, ['If Foo, then Bar!'])
        # nested interfaces with invariants:
        self.assertEquals(ISubInvariant.getTaggedValue('invariants'),
                          [BarGreaterThanFoo])
        o = InvariantC()
        directlyProvides(o, ISubInvariant)
        o.foo = 42
        # even though the interface has changed, we should still only have one
        # error.
        errorsEqual(self, o, 1, ['If Foo, then Bar!'], ISubInvariant)
        # however, if we set foo to 0 (Boolean False) and bar to a negative
        # number then we'll get the new error
        o.foo = 2
        o.bar = 1
        errorsEqual(self, o, 1, ['Please, Boo MUST be greater than Foo!'],
                    ISubInvariant)
        # and if we set foo to a positive number and boo to 0, we'll
        # get both errors!
        o.foo = 1
        o.bar = 0
        errorsEqual(self, o, 2, ['If Foo, then Bar!',
                                 'Please, Boo MUST be greater than Foo!'],
                    ISubInvariant)
        # for a happy ending, we'll make the invariants happy
        o.foo = 1
        o.bar = 2
        self.assertEquals(IInvariant.validateInvariants(o), None) # woohoo
        # now we'll do two invariants on the same interface,
        # just to make sure that a small
        # multi-invariant interface is at least minimally tested.
        o = InvariantC()
        directlyProvides(o, IInvariant)
        o.foo = 42
        old_invariants = IInvariant.getTaggedValue('invariants')
        invariants = old_invariants[:]
        invariants.append(BarGreaterThanFoo) # if you really need to mutate,
        # then this would be the way to do it.  Probably a bad idea, though. :-)
        IInvariant.setTaggedValue('invariants', invariants)
        #
        # even though the interface has changed, we should still only have one
        # error.
        errorsEqual(self, o, 1, ['If Foo, then Bar!'])
        # however, if we set foo to 0 (Boolean False) and bar to a negative
        # number then we'll get the new error
        o.foo = 2
        o.bar = 1
        errorsEqual(self, o, 1, ['Please, Boo MUST be greater than Foo!'])
        # and if we set foo to a positive number and boo to 0, we'll
        # get both errors!
        o.foo = 1
        o.bar = 0
        errorsEqual(self, o, 2, ['If Foo, then Bar!',
                                 'Please, Boo MUST be greater than Foo!'])
        # for another happy ending, we'll make the invariants happy again
        o.foo = 1
        o.bar = 2
        self.assertEquals(IInvariant.validateInvariants(o), None) # bliss
        # clean up
        IInvariant.setTaggedValue('invariants', old_invariants)

    def test___doc___element(self):
        from zope.interface import Interface
        from zope.interface import Attribute
        class I(Interface):
            "xxx"

        self.assertEqual(I.__doc__, "xxx")
        self.assertEqual(list(I), [])

        class I(Interface):
            "xxx"

            __doc__ = Attribute('the doc')

        self.assertEqual(I.__doc__, "")
        self.assertEqual(list(I), ['__doc__'])

    def testIssue228(self):
        from zope.interface import Interface
        # Test for http://collector.zope.org/Zope3-dev/228
        if sys.version[0] == '3':
            # No old style classes in Python 3, so the test becomes moot.
            return
        class I(Interface):
            "xxx"
        class Bad:
            __providedBy__ = None
        # Old style classes don't have a '__class__' attribute
        self.failUnlessRaises(AttributeError, I.providedBy, Bad)



if sys.version_info >= (2, 4):

    def test_invariant_as_decorator():
        """Invaiants can be deined in line

          >>> from zope.interface.exceptions import Invalid
          >>> from zope.interface import Interface
          >>> from zope.interface import Attribute
          >>> from zope.interface import implements
          >>> from zope.interface import invariant
          >>> class IRange(Interface):
          ...     min = Attribute("Lower bound")
          ...     max = Attribute("Upper bound")
          ...
          ...     @invariant
          ...     def range_invariant(ob):
          ...         if ob.max < ob.min:
          ...             raise Invalid('max < min')


          >>> class Range(object):
          ...     implements(IRange)
          ...
          ...     def __init__(self, min, max):
          ...         self.min, self.max = min, max

          >>> from zope.interface.exceptions import Invalid
          >>> IRange.validateInvariants(Range(1,2))
          >>> IRange.validateInvariants(Range(1,1))
          >>> try:
          ...     IRange.validateInvariants(Range(2,1))
          ... except Invalid, e:
          ...     str(e)
          'max < min'


        """


def test_description_cache_management():
    """ See https://bugs.launchpad.net/zope.interface/+bug/185974

There was a bug where the cache used by Specification.get() was not
cleared when the bases were changed.

    >>> from zope.interface import Interface
    >>> from zope.interface import Attribute
    >>> class I1(Interface):
    ...     a = Attribute('a')

    >>> class I2(I1):
    ...     pass

    >>> class I3(I2):
    ...     pass

    >>> I3.get('a') is I1.get('a')
    True
    >>> I2.__bases__ = (Interface,)
    >>> I3.get('a') is None
    True
    """


def test_suite():
    suite = unittest.makeSuite(InterfaceTests)
    suite.addTest(doctest.DocTestSuite("zope.interface.interface"))
    if sys.version_info >= (2, 4):
        suite.addTest(doctest.DocTestSuite())
    suite.addTest(doctest.DocFileSuite(
        '../README.txt',
        globs={'__name__': '__main__'},
        optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
        ))
    suite.addTest(doctest.DocFileSuite(
        '../README.ru.txt',
        globs={'__name__': '__main__'},
        optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
        ))
    return suite
