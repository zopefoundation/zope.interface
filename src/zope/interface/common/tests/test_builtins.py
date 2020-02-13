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
from __future__ import absolute_import

import unittest

from zope.interface._compat import PYTHON2 as PY2
from zope.interface.common import builtins

from . import VerifyClassMixin
from . import VerifyObjectMixin


class TestVerifyClass(VerifyClassMixin,
                      unittest.TestCase):
    UNVERIFIABLE = (

    )
    FILE_IMPL = ()
    if PY2:
        UNVERIFIABLE += (
            # On both CPython and PyPy, there's no
            # exposed __iter__ method for strings or unicode.
            unicode,
            str,
        )
        FILE_IMPL = ((file, builtins.IFile),)
    @classmethod
    def create_tests(cls):
        for klass, iface in (
                (list, builtins.IList),
                (tuple, builtins.ITuple),
                (type(u'abc'), builtins.ITextString),
                (bytes, builtins.IByteString),
                (str, builtins.INativeString),
                (bool, builtins.IBool),
                (dict, builtins.IDict),
        ) + cls.FILE_IMPL:
            def test(self, klass=klass, iface=iface):
                if klass in self.UNVERIFIABLE:
                    self.skipTest("Cannot verify %s" % klass)

                self.assertTrue(self.verify(iface, klass))

            name = 'test_auto_' + klass.__name__ + '_' + iface.__name__
            test.__name__ = name
            setattr(cls, name, test)

TestVerifyClass.create_tests()


class TestVerifyObject(VerifyObjectMixin,
                       TestVerifyClass):
    CONSTRUCTORS = {
        builtins.IFile: lambda: open(__file__)
    }
