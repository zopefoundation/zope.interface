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

from zope.interface._compat import PY38
from zope.interface._compat import PY39
from zope.interface._compat import PY310
from zope.interface._compat import PY311
from zope.interface._compat import PY312
from zope.interface._compat import PY313
from zope.interface.common import builtins

from . import VerifyClassMixin
from . import VerifyObjectMixin
from . import add_verify_tests


class TestVerifyClass(VerifyClassMixin,
                      unittest.TestCase):
    pass


VERIFY_TESTS = [
    (builtins.IList, (list,)),
    (builtins.ITuple, (tuple,)),
    (builtins.ITextString, (str,)),
    (builtins.INativeString, (str,)),
    (builtins.IBool, (bool,)),
    (builtins.IDict, (dict,)),
    (builtins.IFile, ()),

]
if PY38 or PY39 or PY310 or PY311 or PY312 or PY313:
    VERIFY_TESTS.append(
        (builtins.IByteString, (bytes,))
    )

add_verify_tests(TestVerifyClass, tuple(VERIFY_TESTS))


class TestVerifyObject(VerifyObjectMixin,
                       TestVerifyClass):
    CONSTRUCTORS = {
        builtins.IFile: lambda: open(__file__)
    }
