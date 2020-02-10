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
"""
Interface definitions paralleling the abstract base classes defined in
:mod:`collections.abc`.

After this module is imported, the standard library types will declare
that they implement the appropriate interface. While most standard
library types will properly implement that interface (that
is, ``verifyObject(ISequence, list()))`` will pass, for example), a few might not:

    - `memoryview` doesn't feature all the defined methods of
      ``ISequence`` such as ``count``; it is still declared to provide
      ``ISequence`` though.

    - `collections.deque.pop` doesn't accept the ``index`` argument of
      `collections.abc.MutableSequence.pop`

    - `range.index` does not accept the ``start`` and ``stop`` arguments.

.. versionadded:: 5.0.0
"""
from __future__ import absolute_import

import sys

try:
    from collections import abc
except ImportError:
    import collections as abc

from zope.interface._compat import PYTHON2 as PY2
from zope.interface.common import ABCInterface
from zope.interface.common import optional

# pylint:disable=inherit-non-class,
# pylint:disable=no-self-argument,no-method-argument
# pylint:disable=unexpected-special-method-signature

PY35 = sys.version_info[:2] >= (3, 5)
PY36 = sys.version_info[:2] >= (3, 6)

def _new_in_ver(name, ver):
    return getattr(abc, name) if ver else None

__all__ = [
    'IAsyncGenerator',
    'IAsyncIterable',
    'IAsyncIterator',
    'IAwaitable',
    'ICollection',
    'IContainer',
    'ICoroutine',
    'IGenerator',
    'IHashable',
    'IItemsView',
    'IIterable',
    'IIterator',
    'IKeysView',
    'IMapping',
    'IMappingView',
    'IMutableMapping',
    'IMutableSequence',
    'IMutableSet',
    'IReversible',
    'ISequence',
    'ISet',
    'ISized',
    'IValuesView',
]

class IContainer(ABCInterface):
    abc = abc.Container

    @optional
    def __contains__(other):
        """
        Optional method. If not provided, the interpreter will use
        ``__iter__`` or the old ``__len__`` and ``__getitem__`` protocol
        to implement ``in``.
        """

class IHashable(ABCInterface):
    abc = abc.Hashable

class IIterable(ABCInterface):
    abc = abc.Iterable

class IIterator(IIterable):
    abc = abc.Iterator

class IReversible(IIterable):
    abc = _new_in_ver('Reversible', PY36)

    @optional
    def __reversed__():
        """
        Optional method. If this isn't present, the interpreter
        will use ``__len__`` and ``__getitem__`` to implement the
        `reversed` builtin.`
        """

class IGenerator(IIterator):
    # New in 3.5
    abc = _new_in_ver('Generator', PY35)


class ISized(ABCInterface):
    abc = abc.Sized


# ICallable is not defined because there's no standard signature.


class ICollection(ISized,
                  IIterable,
                  IContainer):
    abc = _new_in_ver('Collection', PY36)


class ISequence(IReversible,
                ICollection):
    abc = abc.Sequence

    @optional
    def __reversed__():
        """
        Optional method. If this isn't present, the interpreter
        will use ``__len__`` and ``__getitem__`` to implement the
        `reversed` builtin.`
        """


class IMutableSequence(ISequence):
    abc = abc.MutableSequence


class ISet(ICollection):
    abc = abc.Set


class IMutableSet(ISet):
    abc = abc.MutableSet


class IMapping(ICollection):
    abc = abc.Mapping

    if PY2:
        @optional
        def __eq__(other):
            """
            The interpreter will supply one.
            """

        __ne__ = __eq__

class IMutableMapping(IMapping):
    abc = abc.MutableMapping


class IMappingView(ISized):
    abc = abc.MappingView


class IItemsView(IMappingView, ISet):
    abc = abc.ItemsView


class IKeysView(IMappingView, ISet):
    abc = abc.KeysView


class IValuesView(IMappingView, ICollection):
    abc = abc.ValuesView

    @optional
    def __contains__(other):
        """
        Optional method. If not provided, the interpreter will use
        ``__iter__`` or the old ``__len__`` and ``__getitem__`` protocol
        to implement ``in``.
        """

class IAwaitable(ABCInterface):
    abc = _new_in_ver('Awaitable', PY35)


class ICoroutine(IAwaitable):
    abc = _new_in_ver('Coroutine', PY35)


class IAsyncIterable(ABCInterface):
    abc = _new_in_ver('AsyncIterable', PY35)


class IAsyncIterator(IAsyncIterable):
    abc = _new_in_ver('AsyncIterator', PY35)


class IAsyncGenerator(IAsyncIterator):
    abc = _new_in_ver('AsyncGenerator', PY36)
