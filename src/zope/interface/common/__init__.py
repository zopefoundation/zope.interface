from weakref import WeakKeyDictionary
from types import FunctionType

from zope.interface import classImplements
from zope.interface import Interface
from zope.interface.interface import fromFunction
from zope.interface.interface import InterfaceClass
from zope.interface.interface import _decorator_non_return

__all__ = [
    # Nothing public here.
]

# Map of standard library class to its primary
# interface. We assume there's a simple linearization
# so that each standard library class can be represented
# by a single interface.
# TODO: Maybe store this in the individual interfaces? We're
# only really keeping this around for test purposes.
stdlib_class_registry = WeakKeyDictionary()

def stdlib_classImplements(cls, iface):
    # Execute ``classImplements(cls, iface)`` and record
    # that in the registry for validation by tests.
    if cls in stdlib_class_registry:
        raise KeyError(cls)
    stdlib_class_registry[cls] = iface
    classImplements(cls, iface)


# pylint:disable=inherit-non-class,
# pylint:disable=no-self-argument,no-method-argument
# pylint:disable=unexpected-special-method-signature

def optional(meth):
    # Apply this decorator to a method definition to make it
    # optional (remove it from the list of required names), overriding
    # the definition inherited from the ABC.
    return _decorator_non_return


class ABCInterfaceClass(InterfaceClass):

    def __init__(self, name, bases, attrs):
        # go ahead and give us a name to ease debugging.
        self.__name__ = name

        based_on = attrs.pop('abc')
        if based_on is None:
            # An ABC from the future, not available to us.
            methods = {
                '__doc__': 'This ABC is not available.'
            }
        else:
            assert name[1:] == based_on.__name__, (name, based_on)
            methods = {
                # Passing the name is important in case of aliases,
                # e.g., ``__ror__ = __or__``.
                k: self.__method_from_function(v, k)
                for k, v in vars(based_on).items()
                if isinstance(v, FunctionType) and not self.__is_private_name(k)
                and not self.__is_reverse_protocol_name(k)
            }
            methods['__doc__'] = "See `%s.%s`" % (
                based_on.__module__,
                based_on.__name__,
            )
        # Anything specified in the body takes precedence.
        # This lets us remove things that are rarely, if ever,
        # actually implemented. For example, ``tuple`` is registered
        # as an Sequence, but doesn't implement the required ``__reversed__``
        # method, but that's OK, it still works with the ``reversed()`` builtin
        # because it has ``__len__`` and ``__getitem__``.
        methods.update(attrs)
        InterfaceClass.__init__(self, name, bases, methods)
        self.__abc = based_on
        self.__register_classes()

    @staticmethod
    def __is_private_name(name):
        if name.startswith('__') and name.endswith('__'):
            return False
        return name.startswith('_')

    @staticmethod
    def __is_reverse_protocol_name(name):
        # The reverse names, like __rand__,
        # aren't really part of the protocol. The interpreter has
        # very complex behaviour around invoking those. PyPy
        # doesn't always even expose them as attributes.
        return name.startswith('__r') and name.endswith('__')

    def __method_from_function(self, function, name):
        method = fromFunction(function, self, name=name)
        # Eliminate the leading *self*, which is implied in
        # an interface, but explicit in an ABC.
        method.positional = method.positional[1:]
        return method

    def __register_classes(self):
        # Make the concrete classes already present in our ABC's registry
        # declare that they implement this interface.
        based_on = self.__abc
        if based_on is None:
            return

        try:
            registered = list(based_on._abc_registry)
        except AttributeError:
            # Rewritten in C in Python 3.?.
            # These expose the underlying weakref.
            from abc import _get_dump
            registry = _get_dump(based_on)[0]
            registered = [x() for x in registry]
            registered = [x for x in registered if x is not None]

        for cls in registered:
            stdlib_classImplements(cls, self)

    def getABC(self):
        """Return the ABC this interface represents."""
        return self.__abc


ABCInterface = ABCInterfaceClass.__new__(ABCInterfaceClass, None, None, None)
InterfaceClass.__init__(ABCInterface, 'ABCInterface', (Interface,), {})
