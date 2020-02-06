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
    # Other
    'BadImplements',
    'InvalidInterface',
]

class Invalid(Exception):
    """A specification is violated
    """

_NotGiven = object()

class _TargetMixin(object):
    target = _NotGiven

    @property
    def _prefix(self):
        if self.target is _NotGiven:
            return "An object"
        return "The object %r" % (self.target,)

class DoesNotImplement(Invalid, _TargetMixin):
    """
    The *target* (optional) does not implement the *interface*.

    .. versionchanged:: 5.0.0
       Add the *target* argument and attribute, and change the resulting
       string value of this object accordingly.
    """

    def __init__(self, interface, target=_NotGiven):
        Invalid.__init__(self)
        self.interface = interface
        self.target = target

    def __str__(self):
        return "%s does not implement the interface %s." % (
            self._prefix,
            self.interface
        )

class BrokenImplementation(Invalid, _TargetMixin):
    """
    The *target* (optional) is missing the attribute *name*.

    .. versionchanged:: 5.0.0
       Add the *target* argument and attribute, and change the resulting
       string value of this object accordingly.

       The *name* can either be a simple string or a ``Attribute`` object.
    """

    def __init__(self, interface, name, target=_NotGiven):
        Invalid.__init__(self)
        self.interface = interface
        self.name = name
        self.target = target

    def __str__(self):
        return "%s has failed to implement interface %s: The %s attribute was not provided." % (
            self._prefix,
            self.interface,
            repr(self.name) if isinstance(self.name, str) else self.name
        )

class BrokenMethodImplementation(Invalid, _TargetMixin):
    """
    The *target* (optional) has a *method* that violates
    its contract in a way described by *mess*.

    .. versionchanged:: 5.0.0
       Add the *target* argument and attribute, and change the resulting
       string value of this object accordingly.

       The *method* can either be a simple string or a ``Method`` object.
    """

    def __init__(self, method, mess, target=_NotGiven):
        Invalid.__init__(self)
        self.method = method
        self.mess = mess
        self.target = target

    def __str__(self):
        return "%s violates its contract in %s: %s." % (
            self._prefix,
            repr(self.method) if isinstance(self.method, str) else self.method,
            self.mess
        )


class InvalidInterface(Exception):
    """The interface has invalid contents
    """

class BadImplements(TypeError):
    """An implementation assertion is invalid

    because it doesn't contain an interface or a sequence of valid
    implementation assertions.
    """
