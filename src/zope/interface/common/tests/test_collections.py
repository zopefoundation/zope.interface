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
try:
    import collections.abc as abc
except ImportError:
    import collections as abc
from collections import deque

try:
    from types import MappingProxyType
except ImportError:
    MappingProxyType = object()

from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from zope.interface.common import ABCInterface
from zope.interface.common import ABCInterfaceClass
# Note that importing z.i.c.collections does work on import.
from zope.interface.common import collections


from zope.interface._compat import PYPY
from zope.interface._compat import PYTHON2 as PY2

def walk_abc_interfaces():
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

        registered = list(iface.getRegisteredConformers())
        if registered:
            yield iface, registered


class TestVerifyClass(unittest.TestCase):

    verifier = staticmethod(verifyClass)

    def _adjust_object_before_verify(self, iface, x):
        return x

    def verify(self, iface, klass, **kwargs):
        return self.verifier(iface,
                             self._adjust_object_before_verify(iface, klass),
                             **kwargs)


    # Here we test some known builtin classes that are defined to implement
    # various collection interfaces as a quick sanity test.
    def test_frozenset(self):
        self.assertIsInstance(frozenset(), abc.Set)
        self.assertTrue(self.verify(collections.ISet, frozenset))

    def test_list(self):
        self.assertIsInstance(list(), abc.MutableSequence)
        self.assertTrue(self.verify(collections.IMutableSequence, list))

    # Now we go through the registry, which should have several things,
    # mostly builtins, but if we've imported other libraries already,
    # it could contain things from outside of there too. We aren't concerned
    # about third-party code here, just standard library types. We start with a
    # blacklist of things to exclude, but if that gets out of hand we can figure
    # out a better whitelisting.
    _UNVERIFIABLE = {
        # This is declared to be an ISequence, but is missing lots of methods,
        # including some that aren't part of a language protocol, such as
        # ``index`` and ``count``.
        memoryview,
        # 'pkg_resources._vendor.pyparsing.ParseResults' is registered as a
        # MutableMapping but is missing methods like ``popitem`` and ``setdefault``.
        # It's imported due to namespace packages.
        'ParseResults',
        # sqlite3.Row claims ISequence but also misses ``index`` and ``count``.
        # It's imported because...? Coverage imports it, but why do we have it without
        # coverage?
        'Row',
    }

    if PYPY:
        _UNVERIFIABLE.update({
            # collections.deque.pop() doesn't support the index= argument to
            # MutableSequence.pop(). We can't verify this on CPython because we can't
            # get the signature, but on PyPy we /can/ get the signature, and of course
            # it doesn't match.
            deque,
            # Likewise for index
            range,
        })
    if PY2:
        # pylint:disable=undefined-variable,no-member
        # There are a lot more types that are fundamentally unverifiable on Python 2.
        _UNVERIFIABLE.update({
            # Missing several key methods like __getitem__
            basestring,
            # Missing __iter__ and __contains__, hard to construct.
            buffer,
            # Missing ``__contains__``, ``count`` and ``index``.
            xrange,
            # These two are missing Set.isdisjoint()
            type({}.viewitems()),
            type({}.viewkeys()),
            # str is missing __iter__!
            str,
        })

    @classmethod
    def gen_tests(cls):
        for iface, registered_classes in walk_abc_interfaces():
            for stdlib_class in registered_classes:
                if stdlib_class in cls._UNVERIFIABLE or stdlib_class.__name__ in cls._UNVERIFIABLE:
                    continue

                def test(self, stdlib_class=stdlib_class, iface=iface):
                    self.assertTrue(self.verify(iface, stdlib_class))

                name = 'test_auto_' + stdlib_class.__name__ + '_' + iface.__name__
                test.__name__ = name
                assert not hasattr(cls, name)
                setattr(cls, name, test)

TestVerifyClass.gen_tests()


class TestVerifyObject(TestVerifyClass):
    verifier = staticmethod(verifyObject)

    _CONSTRUCTORS = {
        collections.IValuesView: {}.values,
        collections.IItemsView: {}.items,
        collections.IKeysView: {}.keys,
        memoryview: lambda: memoryview(b'abc'),
        range: lambda: range(10),
        MappingProxyType: lambda: MappingProxyType({})
    }

    if PY2:
        # pylint:disable=undefined-variable,no-member
        _CONSTRUCTORS.update({
            collections.IValuesView: {}.viewvalues,
        })

    def _adjust_object_before_verify(self, iface, x):
        return self._CONSTRUCTORS.get(iface,
                                      self._CONSTRUCTORS.get(x, x))()
