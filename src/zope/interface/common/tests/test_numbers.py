##############################################################################
# Copyright (c) 2020 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################


import unittest
import numbers as abc

from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

# Note that importing z.i.c.numbers does work on import.
from zope.interface.common import numbers

from . import add_abc_interface_tests


class TestVerifyClass(unittest.TestCase):
    verifier = staticmethod(verifyClass)
    UNVERIFIABLE = ()

    def _adjust_object_before_verify(self, iface, x):
        return x

    def verify(self, iface, klass, **kwargs):
        return self.verifier(iface,
                             self._adjust_object_before_verify(iface, klass),
                             **kwargs)

    def test_int(self):
        self.assertIsInstance(int(), abc.Integral)
        self.assertTrue(self.verify(numbers.IIntegral, int))

    def test_float(self):
        self.assertIsInstance(float(), abc.Real)
        self.assertTrue(self.verify(numbers.IReal, float))

add_abc_interface_tests(TestVerifyClass, numbers.INumber.__module__)


class TestVerifyObject(TestVerifyClass):
    verifier = staticmethod(verifyObject)

    def _adjust_object_before_verify(self, iface, x):
        return x()
