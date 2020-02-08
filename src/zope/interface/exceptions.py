##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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
"""Interface-specific exceptions
"""

__all__ = [
    # Invalid tree
    'Invalid',
    'DoesNotImplement',
    'BrokenImplementation',
    'BrokenMethodImplementation',
    'MultipleInvalid',
    # Other
    'BadImplements',
    'InvalidInterface',
]

class Invalid(Exception):
    """A specification is violated
    """

_NotGiven = '<Not Given>'

class _TargetMixin(object):
    target = _NotGiven
    interface = None

    @property
    def _target_prefix(self):
        if self.target is _NotGiven:
            return "An object"
        return "The object %r" % (self.target,)

    _trailer = '.'

    @property
    def _general_description(self):
        return "has failed to implement interface %s:" % (
            self.interface
        ) if self.interface is not None else ''


    def __str__(self):
        return "%s %s%s%s" % (
            self._target_prefix,
            self._general_description,
            self._specifics,
            self._trailer
        )


class DoesNotImplement(_TargetMixin, Invalid):
    """
    The *target* (optional) does not implement the *interface*.

    .. versionchanged:: 5.0.0
       Add the *target* argument and attribute, and change the resulting
       string value of this object accordingly.
    """

    def __init__(self, interface, target=_NotGiven):
        Invalid.__init__(self, interface, target)
        self.interface = interface
        self.target = target

    _general_description = "does not implement the interface"

    @property
    def _specifics(self):
        return ' ' + str(self.interface)

class BrokenImplementation(_TargetMixin, Invalid):
    """
    The *target* (optional) is missing the attribute *name*.

    .. versionchanged:: 5.0.0
       Add the *target* argument and attribute, and change the resulting
       string value of this object accordingly.

       The *name* can either be a simple string or a ``Attribute`` object.
    """

    def __init__(self, interface, name, target=_NotGiven):
        Invalid.__init__(self, interface, name, target)
        self.interface = interface
        self.name = name
        self.target = target


    @property
    def _specifics(self):
        return " The %s attribute was not provided" % (
            repr(self.name) if isinstance(self.name, str) else self.name
        )

class BrokenMethodImplementation(_TargetMixin, Invalid):
    """
    The *target* (optional) has a *method* that violates
    its contract in a way described by *mess*.

    .. versionchanged:: 5.0.0
       Add the *target* argument and attribute, and change the resulting
       string value of this object accordingly.

       The *method* can either be a simple string or a ``Method`` object.
    """

    def __init__(self, method, mess, target=_NotGiven):
        Invalid.__init__(self, method, mess, target)
        self.method = method
        self.mess = mess
        self.target = target

    @property
    def _specifics(self):
        return 'violates the contract of %s because %s' % (
            repr(self.method) if isinstance(self.method, str) else self.method,
            self.mess,
        )


class MultipleInvalid(_TargetMixin, Invalid):
    """
    The *target* has failed to implement the *iface* in
    multiple ways.

    The failures are described by *exceptions*, a collection of
    other `Invalid` instances.

    .. versionadded:: 5.0
    """

    def __init__(self, iface, target, exceptions):
        exceptions = list(exceptions)
        Invalid.__init__(self, iface, target, exceptions)
        self.target = target
        self.interface = iface
        self.exceptions = exceptions

    @property
    def _specifics(self):
        # It would be nice to use tabs here, but that
        # is hard to represent in doctests.
        return '\n    ' + '\n    '.join(
            x._specifics.strip() if isinstance(x, _TargetMixin) else(str(x))
            for x in self.exceptions
        )

    _trailer = ''


class InvalidInterface(Exception):
    """The interface has invalid contents
    """

class BadImplements(TypeError):
    """An implementation assertion is invalid

    because it doesn't contain an interface or a sequence of valid
    implementation assertions.
    """
