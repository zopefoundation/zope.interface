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

from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from zope.interface.common import ABCInterface
from zope.interface.common import ABCInterfaceClass


def iter_abc_interfaces(predicate=lambda iface: True):
    # Iterate ``(iface, classes)``, where ``iface`` is a descendent of
    # the ABCInterfaceClass passing the *predicate* and ``classes`` is
    # an iterable of classes registered to conform to that interface.
    #
    # Note that some builtin classes are registered for two distinct
    # parts of the ABC/interface tree. For example, bytearray is both ByteString
    # and MutableSequence.
    seen = set()
    stack = list(ABCInterface.dependents) # subclasses, but also implementedBy objects
    while stack:
        iface = stack.pop(0)
        if iface in seen or not isinstance(iface, ABCInterfaceClass):
            continue
        seen.add(iface)
        stack.extend(list(iface.dependents))
        if not predicate(iface):
            continue

        registered = list(iface.getRegisteredConformers())
        if registered:
            yield iface, registered


def add_abc_interface_tests(cls, module):
    def predicate(iface):
        return iface.__module__ == module

    for iface, registered_classes in iter_abc_interfaces(predicate):
        for stdlib_class in registered_classes:

            def test(self, stdlib_class=stdlib_class, iface=iface):
                if stdlib_class in self.UNVERIFIABLE or stdlib_class.__name__ in self.UNVERIFIABLE:
                    self.skipTest("Unable to verify %s" % stdlib_class)

                self.assertTrue(self.verify(iface, stdlib_class))

            name = 'test_auto_' + stdlib_class.__name__ + '_' + iface.__name__
            test.__name__ = name
            assert not hasattr(cls, name)
            setattr(cls, name, test)



class VerifyClassMixin(unittest.TestCase):
    verifier = staticmethod(verifyClass)
    UNVERIFIABLE = ()

    def _adjust_object_before_verify(self, iface, x):
        return x

    def verify(self, iface, klass, **kwargs):
        return self.verifier(iface,
                             self._adjust_object_before_verify(iface, klass),
                             **kwargs)


class VerifyObjectMixin(VerifyClassMixin):
    verifier = staticmethod(verifyObject)
    CONSTRUCTORS = {
    }

    def _adjust_object_before_verify(self, iface, x):
        return self.CONSTRUCTORS.get(iface,
                                     self.CONSTRUCTORS.get(x, x))()
