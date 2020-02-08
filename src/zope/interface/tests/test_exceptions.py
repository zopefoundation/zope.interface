##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
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
""" zope.interface.exceptions unit tests
"""
import unittest

def _makeIface():
    from zope.interface import Interface
    class IDummy(Interface):
        pass
    return IDummy

class DoesNotImplementTests(unittest.TestCase):

    def _getTargetClass(self):
        from zope.interface.exceptions import DoesNotImplement
        return DoesNotImplement

    def _makeOne(self, *args):
        iface = _makeIface()
        return self._getTargetClass()(iface, *args)

    def test___str__(self):
        dni = self._makeOne()
        self.assertEqual(
            str(dni),
            'An object does not implement the interface '
            '<InterfaceClass zope.interface.tests.test_exceptions.IDummy>.')

    def test___str__w_candidate(self):
        dni = self._makeOne('candidate')
        self.assertEqual(
            str(dni),
            'The object \'candidate\' does not implement the interface '
            '<InterfaceClass zope.interface.tests.test_exceptions.IDummy>.')


class BrokenImplementationTests(unittest.TestCase):

    def _getTargetClass(self):
        from zope.interface.exceptions import BrokenImplementation
        return BrokenImplementation

    def _makeOne(self, *args):
        iface = _makeIface()
        return self._getTargetClass()(iface, 'missing', *args)

    def test___str__(self):
        dni = self._makeOne()
        self.assertEqual(
            str(dni),
            'An object has failed to implement interface '
            '<InterfaceClass zope.interface.tests.test_exceptions.IDummy>: '
            "The 'missing' attribute was not provided.")

    def test___str__w_candidate(self):
        dni = self._makeOne('candidate')
        self.assertEqual(
            str(dni),
            'The object \'candidate\' has failed to implement interface '
            '<InterfaceClass zope.interface.tests.test_exceptions.IDummy>: '
            "The 'missing' attribute was not provided.")

class BrokenMethodImplementationTests(unittest.TestCase):

    def _getTargetClass(self):
        from zope.interface.exceptions import BrokenMethodImplementation
        return BrokenMethodImplementation

    def _makeOne(self, *args):
        return self._getTargetClass()('aMethod', 'I said so', *args)

    def test___str__(self):
        dni = self._makeOne()
        self.assertEqual(
            str(dni),
            "An object violates the contract of 'aMethod' because I said so.")

    def test___str__w_candidate(self):
        dni = self._makeOne('candidate')
        self.assertEqual(
            str(dni),
            "The object 'candidate' violates the contract of 'aMethod' because I said so.")

    def test___repr__w_candidate(self):
        dni = self._makeOne('candidate')
        self.assertEqual(
            repr(dni),
            "BrokenMethodImplementation('aMethod', 'I said so', 'candidate')"
        )


class MultipleInvalidTests(unittest.TestCase):

    def _getTargetClass(self):
        from zope.interface.exceptions import MultipleInvalid
        return MultipleInvalid

    def _makeOne(self, excs):
        iface = _makeIface()
        return self._getTargetClass()(iface, 'target', excs)

    def test__str__(self):
        from zope.interface.exceptions import BrokenMethodImplementation
        excs = [
            BrokenMethodImplementation('aMethod', 'I said so'),
            Exception("Regular exception")
        ]
        dni = self._makeOne(excs)
        self.assertEqual(
            str(dni),
            "The object 'target' has failed to implement interface "
            "<InterfaceClass zope.interface.tests.test_exceptions.IDummy>:\n"
            "    violates the contract of 'aMethod' because I said so\n"
            "    Regular exception"
        )

    def test__repr__(self):
        from zope.interface.exceptions import BrokenMethodImplementation
        excs = [
            BrokenMethodImplementation('aMethod', 'I said so'),
            # Use multiple arguments to normalize repr; versions of Python
            # prior to 3.7 add a trailing comma if there's just one.
            Exception("Regular", "exception")
        ]
        dni = self._makeOne(excs)
        self.assertEqual(
            repr(dni),
            "MultipleInvalid(<InterfaceClass zope.interface.tests.test_exceptions.IDummy>,"
            " 'target',"
            " [BrokenMethodImplementation('aMethod', 'I said so', '<Not Given>'),"
            " Exception('Regular', 'exception')])"
        )
