============
 Interfaces
============

.. currentmodule:: zope.interface

Interfaces are objects that specify (document) the external behavior
of objects that "provide" them.  An interface specifies behavior
through:

- Informal documentation in a doc string

- Attribute definitions

- Invariants, which are conditions that must hold for objects that
  provide the interface

Attribute definitions specify specific attributes. They define the
attribute name and provide documentation and constraints of attribute
values.  Attribute definitions can take a number of forms, as we'll
see below.

Defining interfaces
===================

Interfaces are defined using Python ``class`` statements:

.. doctest::

  >>> import zope.interface
  >>> class IFoo(zope.interface.Interface):
  ...    """Foo blah blah"""
  ...
  ...    x = zope.interface.Attribute("""X blah blah""")
  ...
  ...    def bar(q, r=None):
  ...        """bar blah blah"""

In the example above, we've created an interface, :class:`IFoo`.  We
subclassed :class:`zope.interface.Interface`, which is an ancestor interface for
all interfaces, much as ``object`` is an ancestor of all new-style
classes [#create]_.   The interface is not a class, it's an Interface,
an instance of :class:`zope.interface.interface.InterfaceClass`:

.. doctest::

  >>> type(IFoo)
  <class 'zope.interface.interface.InterfaceClass'>

We can ask for the interface's documentation:

.. doctest::

  >>> IFoo.__doc__
  'Foo blah blah'

and its name:

.. doctest::

  >>> IFoo.__name__
  'IFoo'

and even its module:

.. doctest::

  >>> IFoo.__module__
  'builtins'

The interface defined two attributes:

``x``
  This is the simplest form of attribute definition.  It has a name
  and a doc string.  It doesn't formally specify anything else.

``bar``
  This is a method.  A method is defined via a function definition.  A
  method is simply an attribute constrained to be a callable with a
  particular signature, as provided by the function definition.

  Note that ``bar`` doesn't take a ``self`` argument.  Interfaces document
  how an object is *used*.  When calling instance methods, you don't
  pass a ``self`` argument, so a ``self`` argument isn't included in the
  interface signature.  The ``self`` argument in instance methods is
  really an implementation detail of Python instances. Other objects,
  besides instances can provide interfaces and their methods might not
  be instance methods. For example, modules can provide interfaces and
  their methods are usually just functions.  Even instances can have
  methods that are not instance methods.

You can access the attributes defined by an interface using mapping
syntax:

.. doctest::

  >>> x = IFoo['x']
  >>> type(x)
  <class 'zope.interface.interface.Attribute'>
  >>> x.__name__
  'x'
  >>> x.__doc__
  'X blah blah'

  >>> IFoo.get('x').__name__
  'x'

  >>> IFoo.get('y')

You can use ``in`` to determine if an interface defines a name:

.. doctest::

  >>> 'x' in IFoo
  True

You can iterate over interfaces to get the names they define:

.. doctest::

  >>> names = list(IFoo)
  >>> names.sort()
  >>> names
  ['bar', 'x']

Remember that interfaces aren't classes. You can't access attribute
definitions as attributes of interfaces:

.. doctest::

  >>> IFoo.x
  Traceback (most recent call last):
    File "<stdin>", line 1, in ?
  AttributeError: 'InterfaceClass' object has no attribute 'x'

Methods provide access to the method signature:

.. doctest::

  >>> bar = IFoo['bar']
  >>> bar.getSignatureString()
  '(q, r=None)'

TODO
  Methods really should have a better API.  This is something that
  needs to be improved.

Declaring interfaces
====================

Having defined interfaces, we can *declare* that objects provide
them.  Before we describe the details, lets define some terms:

*provide*
   We say that objects *provide* interfaces.  If an object provides an
   interface, then the interface specifies the behavior of the
   object. In other words, interfaces specify the behavior of the
   objects that provide them.

*implement*
   We normally say that classes *implement* interfaces.  If a class
   implements an interface, then the instances of the class provide
   the interface.  Objects provide interfaces that their classes
   implement [#factory]_.  (Objects can provide interfaces directly,
   in addition to what their classes implement.)

   It is important to note that classes don't usually provide the
   interfaces that they implement.

   We can generalize this to factories.  For any callable object we
   can declare that it produces objects that provide some interfaces
   by saying that the factory implements the interfaces.

Now that we've defined these terms, we can talk about the API for
declaring interfaces.

Declaring implemented interfaces
--------------------------------

The most common way to declare interfaces is using the `implementer`
decorator on a class:

.. doctest::

  >>> @zope.interface.implementer(IFoo)
  ... class Foo:
  ...
  ...     def __init__(self, x=None):
  ...         self.x = x
  ...
  ...     def bar(self, q, r=None):
  ...         return q, r, self.x
  ...
  ...     def __repr__(self):
  ...         return "Foo(%s)" % self.x


In this example, we declared that ``Foo`` implements ``IFoo``. This means
that instances of ``Foo`` provide ``IFoo``.  Having made this declaration,
there are several ways we can introspect the declarations.  First, we
can ask an interface whether it is implemented by a class:

.. doctest::

  >>> IFoo.implementedBy(Foo)
  True

And we can ask whether an interface is provided by an object:

.. doctest::

  >>> foo = Foo()
  >>> IFoo.providedBy(foo)
  True

Of course, ``Foo`` doesn't *provide* ``IFoo``, it *implements* it:

.. doctest::

  >>> IFoo.providedBy(Foo)
  False

We can also ask what interfaces are implemented by a class:

.. doctest::

  >>> list(zope.interface.implementedBy(Foo))
  [<InterfaceClass builtins.IFoo>]

It's an error to ask for interfaces implemented by a non-callable
object:

.. doctest::

  >>> IFoo.implementedBy(foo)
  Traceback (most recent call last):
  ...
  TypeError: ('ImplementedBy called for non-factory', Foo(None))

  >>> list(zope.interface.implementedBy(foo))
  Traceback (most recent call last):
  ...
  TypeError: ('ImplementedBy called for non-factory', Foo(None))

Similarly, we can ask what interfaces are provided by an object:

.. doctest::

  >>> list(zope.interface.providedBy(foo))
  [<InterfaceClass builtins.IFoo>]
  >>> list(zope.interface.providedBy(Foo))
  []

We can declare interfaces implemented by other factories (besides
classes).  We do this using the same `implementer` decorator.

.. doctest::

  >>> @zope.interface.implementer(IFoo)
  ... def yfoo(y):
  ...     foo = Foo()
  ...     foo.y = y
  ...     return foo

  >>> list(zope.interface.implementedBy(yfoo))
  [<InterfaceClass builtins.IFoo>]

Note that the implementer decorator may modify its argument. Callers
should not assume that a new object is created.

Using implementer also works on callable objects. This is used by
:py:mod:`zope.formlib`, as an example:

.. doctest::

  >>> class yfactory:
  ...     def __call__(self, y):
  ...         foo = Foo()
  ...         foo.y = y
  ...         return foo
  >>> yfoo = yfactory()
  >>> yfoo = zope.interface.implementer(IFoo)(yfoo)

  >>> list(zope.interface.implementedBy(yfoo))
  [<InterfaceClass builtins.IFoo>]

XXX: Double check and update these version numbers:

In :py:mod:`zope.interface` 3.5.2 and lower, the implementer decorator can not
be used for classes, but in 3.6.0 and higher it can:

.. doctest::

  >>> Foo = zope.interface.implementer(IFoo)(Foo)
  >>> list(zope.interface.providedBy(Foo()))
  [<InterfaceClass builtins.IFoo>]

Note that class decorators using the ``@implementer(IFoo)`` syntax are only
supported in Python 2.6 and later.

.. autofunction:: implementer
   :noindex:

   .. XXX: Duplicate description.

Declaring provided interfaces
-----------------------------

We can declare interfaces directly provided by objects.  Suppose that
we want to document what the ``__init__`` method of the ``Foo`` class
does.  It's not *really* part of ``IFoo``.  You wouldn't normally call
the ``__init__`` method on Foo instances.  Rather, the ``__init__`` method
is part of ``Foo``'s ``__call__`` method:

.. doctest::

  >>> class IFooFactory(zope.interface.Interface):
  ...     """Create foos"""
  ...
  ...     def __call__(x=None):
  ...         """Create a foo
  ...
  ...         The argument provides the initial value for x ...
  ...         """

It's the class that provides this interface, so we declare the
interface on the class:

.. doctest::

  >>> zope.interface.directlyProvides(Foo, IFooFactory)

And then, we'll see that Foo provides some interfaces:

.. doctest::

  >>> list(zope.interface.providedBy(Foo))
  [<InterfaceClass builtins.IFooFactory>]
  >>> IFooFactory.providedBy(Foo)
  True

Declaring class interfaces is common enough that there's a special
decorator for it, `provider`:

.. doctest::

  >>> @zope.interface.implementer(IFoo)
  ... @zope.interface.provider(IFooFactory)
  ... class Foo2:
  ...
  ...     def __init__(self, x=None):
  ...         self.x = x
  ...
  ...     def bar(self, q, r=None):
  ...         return q, r, self.x
  ...
  ...     def __repr__(self):
  ...         return "Foo(%s)" % self.x

  >>> list(zope.interface.providedBy(Foo2))
  [<InterfaceClass builtins.IFooFactory>]
  >>> IFooFactory.providedBy(Foo2)
  True

There's a similar function, ``moduleProvides``, that supports interface
declarations from within module definitions.  For example, see the use
of ``moduleProvides`` call in ``zope.interface.__init__``, which declares that
the package ``zope.interface`` provides ``IInterfaceDeclaration``.

Sometimes, we want to declare interfaces on instances, even though
those instances get interfaces from their classes.  Suppose we create
a new interface, ``ISpecial``:

.. doctest::

  >>> class ISpecial(zope.interface.Interface):
  ...     reason = zope.interface.Attribute("Reason why we're special")
  ...     def brag():
  ...         "Brag about being special"

We can make an existing foo instance special by providing ``reason``
and ``brag`` attributes:

.. doctest::

  >>> foo.reason = 'I just am'
  >>> def brag():
  ...      return "I'm special!"
  >>> foo.brag = brag
  >>> foo.reason
  'I just am'
  >>> foo.brag()
  "I'm special!"

and by declaring the interface:

.. doctest::

  >>> zope.interface.directlyProvides(foo, ISpecial)

then the new interface is included in the provided interfaces:

.. doctest::

  >>> ISpecial.providedBy(foo)
  True
  >>> list(zope.interface.providedBy(foo))
  [<InterfaceClass builtins.ISpecial>, <InterfaceClass builtins.IFoo>]

We can find out what interfaces are directly provided by an object:

.. doctest::

  >>> list(zope.interface.directlyProvidedBy(foo))
  [<InterfaceClass builtins.ISpecial>]

  >>> newfoo = Foo()
  >>> list(zope.interface.directlyProvidedBy(newfoo))
  []

.. autofunction:: provider
   :noindex:

   .. XXX: Duplicate description.

Inherited declarations
----------------------

Normally, declarations are inherited:

.. doctest::

  >>> @zope.interface.implementer(ISpecial)
  ... class SpecialFoo(Foo):
  ...     reason = 'I just am'
  ...     def brag(self):
  ...         return "I'm special because %s" % self.reason

  >>> list(zope.interface.implementedBy(SpecialFoo))
  [<InterfaceClass builtins.ISpecial>, <InterfaceClass builtins.IFoo>]

  >>> list(zope.interface.providedBy(SpecialFoo()))
  [<InterfaceClass builtins.ISpecial>, <InterfaceClass builtins.IFoo>]

Sometimes, you don't want to inherit declarations.  In that case, you
can use ``implementer_only``, instead of ``implementer``:

.. doctest::

  >>> @zope.interface.implementer_only(ISpecial)
  ... class Special(Foo):
  ...     reason = 'I just am'
  ...     def brag(self):
  ...         return "I'm special because %s" % self.reason

  >>> list(zope.interface.implementedBy(Special))
  [<InterfaceClass builtins.ISpecial>]

  >>> list(zope.interface.providedBy(Special()))
  [<InterfaceClass builtins.ISpecial>]

External declarations
---------------------

Normally, we make implementation declarations as part of a class
definition. Sometimes, we may want to make declarations from outside
the class definition. For example, we might want to declare interfaces
for classes that we didn't write.  The function ``classImplements`` can
be used for this purpose:

.. doctest::

  >>> class C:
  ...     pass

  >>> zope.interface.classImplements(C, IFoo)
  >>> list(zope.interface.implementedBy(C))
  [<InterfaceClass builtins.IFoo>]

.. autofunction:: classImplements
   :noindex:

We can use ``classImplementsOnly`` to exclude inherited interfaces:

.. doctest::

  >>> class C(Foo):
  ...     pass

  >>> zope.interface.classImplementsOnly(C, ISpecial)
  >>> list(zope.interface.implementedBy(C))
  [<InterfaceClass builtins.ISpecial>]

.. autofunction:: classImplementsOnly
   :noindex:

   .. XXX: Duplicate description.

Declaration Objects
-------------------

When we declare interfaces, we create *declaration* objects.  When we
query declarations, declaration objects are returned:

.. doctest::

  >>> type(zope.interface.implementedBy(Special))
  <class 'zope.interface.declarations.Implements'>

Declaration objects and interface objects are similar in many ways. In
fact, they share a common base class.  The important thing to realize
about them is that they can be used where interfaces are expected in
declarations. Here's a silly example:

.. doctest::

  >>> @zope.interface.implementer_only(
  ...     zope.interface.implementedBy(Foo),
  ...     ISpecial,
  ... )
  ... class Special2(object):
  ...     reason = 'I just am'
  ...     def brag(self):
  ...         return "I'm special because %s" % self.reason

The declaration here is almost the same as
``zope.interface.implementer(ISpecial)``, except that the order of
interfaces in the resulting declaration is different:

.. doctest::

  >>> list(zope.interface.implementedBy(Special2))
  [<InterfaceClass builtins.IFoo>, <InterfaceClass builtins.ISpecial>]


Interface Inheritance
=====================

Interfaces can extend other interfaces. They do this simply by listing
the other interfaces as base interfaces:

.. doctest::

  >>> class IBlat(zope.interface.Interface):
  ...     """Blat blah blah"""
  ...
  ...     y = zope.interface.Attribute("y blah blah")
  ...     def eek():
  ...         """eek blah blah"""

  >>> IBlat.__bases__
  (<InterfaceClass zope.interface.Interface>,)

  >>> class IBaz(IFoo, IBlat):
  ...     """Baz blah"""
  ...     def eek(a=1):
  ...         """eek in baz blah"""
  ...

  >>> IBaz.__bases__
  (<InterfaceClass builtins.IFoo>, <InterfaceClass builtins.IBlat>)

  >>> names = list(IBaz)
  >>> names.sort()
  >>> names
  ['bar', 'eek', 'x', 'y']

Note that ``IBaz`` overrides ``eek``:

.. doctest::

  >>> IBlat['eek'].__doc__
  'eek blah blah'
  >>> IBaz['eek'].__doc__
  'eek in baz blah'

We were careful to override ``eek`` in a compatible way.  When extending
an interface, the extending interface should be compatible [#compat]_
with the extended interfaces.

We can ask whether one interface extends another:

.. doctest::

  >>> IBaz.extends(IFoo)
  True
  >>> IBlat.extends(IFoo)
  False

Note that interfaces don't extend themselves:

.. doctest::

  >>> IBaz.extends(IBaz)
  False

Sometimes we wish they did, but we can instead use ``isOrExtends``:

.. doctest::

  >>> IBaz.isOrExtends(IBaz)
  True
  >>> IBaz.isOrExtends(IFoo)
  True
  >>> IFoo.isOrExtends(IBaz)
  False

When we iterate over an interface, we get all of the names it defines,
including names defined by base interfaces. Sometimes, we want *just*
the names defined by the interface directly. We can use the ``names``
method for that:

.. doctest::

  >>> list(IBaz.names())
  ['eek']

Inheritance of attribute specifications
---------------------------------------

An interface may override attribute definitions from base interfaces.
If two base interfaces define the same attribute, the attribute is
inherited from the most specific interface. For example, with:

.. doctest::

  >>> class IBase(zope.interface.Interface):
  ...
  ...     def foo():
  ...         "base foo doc"

  >>> class IBase1(IBase):
  ...     pass

  >>> class IBase2(IBase):
  ...
  ...     def foo():
  ...         "base2 foo doc"

  >>> class ISub(IBase1, IBase2):
  ...     pass

``ISub``'s definition of ``foo`` is the one from ``IBase2``, since ``IBase2`` is more
specific than ``IBase``:

.. doctest::

  >>> ISub['foo'].__doc__
  'base2 foo doc'

Note that this differs from a depth-first search.

Sometimes, it's useful to ask whether an interface defines an
attribute directly.  You can use the direct method to get a directly
defined definitions:

.. doctest::

  >>> IBase.direct('foo').__doc__
  'base foo doc'

  >>> ISub.direct('foo')

Specifications
--------------

Interfaces and declarations are both special cases of specifications.
What we described above for interface inheritance applies to both
declarations and specifications.  Declarations actually extend the
interfaces that they declare:

.. doctest::

  >>> @zope.interface.implementer(IBaz)
  ... class Baz(object):
  ...     pass

  >>> baz_implements = zope.interface.implementedBy(Baz)
  >>> baz_implements.__bases__
  (<InterfaceClass builtins.IBaz>, <implementedBy ...object>)

  >>> baz_implements.extends(IFoo)
  True

  >>> baz_implements.isOrExtends(IFoo)
  True
  >>> baz_implements.isOrExtends(baz_implements)
  True

Specifications (interfaces and declarations) provide an ``__sro__``
that lists the specification and all of it's ancestors:

.. doctest::

  >>> from pprint import pprint
  >>> pprint(baz_implements.__sro__)
  (<implementedBy builtins.Baz>,
   <InterfaceClass builtins.IBaz>,
   <InterfaceClass builtins.IFoo>,
   <InterfaceClass builtins.IBlat>,
   <implementedBy ...object>,
   <InterfaceClass zope.interface.Interface>)
  >>> class IBiz(zope.interface.Interface):
  ...    pass
  >>> @zope.interface.implementer(IBiz)
  ... class Biz(Baz):
  ...    pass
  >>> pprint(zope.interface.implementedBy(Biz).__sro__)
  (<implementedBy builtins.Biz>,
   <InterfaceClass builtins.IBiz>,
   <implementedBy builtins.Baz>,
   <InterfaceClass builtins.IBaz>,
   <InterfaceClass builtins.IFoo>,
   <InterfaceClass builtins.IBlat>,
   <implementedBy ...object>,
   <InterfaceClass zope.interface.Interface>)

Tagged Values
=============

.. autofunction:: taggedValue

Interfaces and attribute descriptions support an extension mechanism,
borrowed from UML, called "tagged values" that lets us store extra
data:

.. doctest::

  >>> IFoo.setTaggedValue('date-modified', '2004-04-01')
  >>> IFoo.setTaggedValue('author', 'Jim Fulton')
  >>> IFoo.getTaggedValue('date-modified')
  '2004-04-01'
  >>> IFoo.queryTaggedValue('date-modified')
  '2004-04-01'
  >>> IFoo.queryTaggedValue('datemodified')
  >>> tags = list(IFoo.getTaggedValueTags())
  >>> tags.sort()
  >>> tags
  ['author', 'date-modified']

Function attributes are converted to tagged values when method
attribute definitions are created:

.. doctest::

  >>> class IBazFactory(zope.interface.Interface):
  ...     def __call__():
  ...         "create one"
  ...     __call__.return_type = IBaz

  >>> IBazFactory['__call__'].getTaggedValue('return_type')
  <InterfaceClass builtins.IBaz>

Tagged values can also be defined from within an interface definition:

.. doctest::

  >>> class IWithTaggedValues(zope.interface.Interface):
  ...     zope.interface.taggedValue('squish', 'squash')
  >>> IWithTaggedValues.getTaggedValue('squish')
  'squash'

Tagged values are inherited in the same way that attribute and method
descriptions are. Inheritance can be ignored by using the "direct"
versions of functions.

.. doctest::

   >>> class IExtendsIWithTaggedValues(IWithTaggedValues):
   ...     zope.interface.taggedValue('child', True)
   >>> IExtendsIWithTaggedValues.getTaggedValue('child')
   True
   >>> IExtendsIWithTaggedValues.getDirectTaggedValue('child')
   True
   >>> IExtendsIWithTaggedValues.getTaggedValue('squish')
   'squash'
   >>> print(IExtendsIWithTaggedValues.queryDirectTaggedValue('squish'))
   None
   >>> IExtendsIWithTaggedValues.setTaggedValue('squish', 'SQUASH')
   >>> IExtendsIWithTaggedValues.getTaggedValue('squish')
   'SQUASH'
   >>> IExtendsIWithTaggedValues.getDirectTaggedValue('squish')
   'SQUASH'


Invariants
==========

.. autofunction:: invariant

Interfaces can express conditions that must hold for objects that
provide them. These conditions are expressed using one or more
invariants.  Invariants are callable objects that will be called with
an object that provides an interface. An invariant raises an ``Invalid``
exception if the condition doesn't hold.  Here's an example:

.. doctest::

  >>> class RangeError(zope.interface.Invalid):
  ...     """A range has invalid limits"""
  ...     def __repr__(self):
  ...         return "RangeError(%r)" % self.args

  >>> def range_invariant(ob):
  ...     if ob.max < ob.min:
  ...         raise RangeError(ob)

Given this invariant, we can use it in an interface definition:

.. doctest::

  >>> class IRange(zope.interface.Interface):
  ...     min = zope.interface.Attribute("Lower bound")
  ...     max = zope.interface.Attribute("Upper bound")
  ...
  ...     zope.interface.invariant(range_invariant)

Interfaces have a method for checking their invariants:

.. doctest::

  >>> @zope.interface.implementer(IRange)
  ... class Range(object):
  ...     def __init__(self, min, max):
  ...         self.min, self.max = min, max
  ...
  ...     def __repr__(self):
  ...         return "Range(%s, %s)" % (self.min, self.max)

  >>> IRange.validateInvariants(Range(1,2))
  >>> IRange.validateInvariants(Range(1,1))
  >>> IRange.validateInvariants(Range(2,1))
  Traceback (most recent call last):
  ...
  RangeError: Range(2, 1)

If you have multiple invariants, you may not want to stop checking
after the first error.  If you pass a list to ``validateInvariants``,
then a single ``Invalid`` exception will be raised with the list of
exceptions as its argument:

.. doctest::

  >>> from zope.interface.exceptions import Invalid
  >>> errors = []
  >>> try:
  ...     IRange.validateInvariants(Range(2,1), errors)
  ... except Invalid as e:
  ...     str(e)
  '[RangeError(Range(2, 1))]'

And the list will be filled with the individual exceptions:

.. doctest::

  >>> errors
  [RangeError(Range(2, 1))]

  >>> del errors[:]

Adaptation
==========

Interfaces can be called to perform adaptation.

The semantics are based on those of the  :pep:`246` ``adapt``
function.

If an object cannot be adapted, then a ``TypeError`` is raised:

.. doctest::

  >>> class I(zope.interface.Interface):
  ...     pass

  >>> I(0)
  Traceback (most recent call last):
  ...
  TypeError: ('Could not adapt', 0, <InterfaceClass builtins.I>)


unless an alternate value is provided as a second positional argument:

.. doctest::

  >>> I(0, 'bob')
  'bob'

If an object already implements the interface, then it will be returned:

.. doctest::

  >>> @zope.interface.implementer(I)
  ... class C(object):
  ...     pass

  >>> obj = C()
  >>> I(obj) is obj
  True

:pep:`246` outlines a requirement:

    When the object knows about the [interface], and either considers
    itself compliant, or knows how to wrap itself suitably.

This is handled with ``__conform__``. If an object implements
``__conform__``, then it will be used to give the object the chance to
decide if it knows about the interface.

.. doctest::

  >>> @zope.interface.implementer(I)
  ... class C(object):
  ...     def __conform__(self, proto):
  ...          return 0

  >>> I(C())
  0

If ``__conform__`` returns ``None`` (because the object is unaware of
the interface), then the rest of the adaptation process will continue.
Here, we demonstrate that if the object already provides the
interface, it is returned.

.. doctest::

  >>> @zope.interface.implementer(I)
  ... class C(object):
  ...     def __conform__(self, proto):
  ...          return None

  >>> c = C()
  >>> I(c) is c
  True


Adapter hooks (see ``__adapt__``) will also be used, if present (after
a ``__conform__`` method, if any, has been tried):

.. doctest::

  >>> from zope.interface.interface import adapter_hooks
  >>> def adapt_0_to_42(iface, obj):
  ...     if obj == 0:
  ...         return 42

  >>> adapter_hooks.append(adapt_0_to_42)
  >>> I(0)
  42

  >>> adapter_hooks.remove(adapt_0_to_42)
  >>> I(0)
  Traceback (most recent call last):
  ...
  TypeError: ('Could not adapt', 0, <InterfaceClass builtins.I>)

``__adapt__``
-------------

.. doctest::

  >>> class I(zope.interface.Interface):
  ...     pass

Interfaces implement the :pep:`246` ``__adapt__`` method to satisfy
the requirement:

    When the [interface] knows about the object, and either the object
    already complies or the [interface] knows how to suitably wrap the
    object.

This method is normally not called directly. It is called by the
:pep:`246` adapt framework and by the interface ``__call__`` operator
once ``__conform__`` (if any) has failed.

The ``adapt`` method is responsible for adapting an object to the
receiver.

The default version returns ``None`` (because by default no interface
"knows how to suitably wrap the object"):

.. doctest::

  >>> I.__adapt__(0)

unless the object given provides the interface ("the object already complies"):

.. doctest::

  >>> @zope.interface.implementer(I)
  ... class C(object):
  ...     pass

  >>> obj = C()
  >>> I.__adapt__(obj) is obj
  True

Adapter hooks can be provided (or removed) to provide custom
adaptation. We'll install a silly hook that adapts 0 to 42.
We install a hook by simply adding it to the ``adapter_hooks``
list:

.. doctest::

  >>> from zope.interface.interface import adapter_hooks
  >>> def adapt_0_to_42(iface, obj):
  ...     if obj == 0:
  ...         return 42

  >>> adapter_hooks.append(adapt_0_to_42)
  >>> I.__adapt__(0)
  42

Hooks must either return an adapter, or ``None`` if no adapter can
be found.

Hooks can be uninstalled by removing them from the list:

.. doctest::

  >>> adapter_hooks.remove(adapt_0_to_42)
  >>> I.__adapt__(0)


It is possible to replace or customize the ``__adapt___``
functionality for particular interfaces.

.. doctest::

   >>> class ICustomAdapt(zope.interface.Interface):
   ...     @zope.interface.interfacemethod
   ...     def __adapt__(self, obj):
   ...          if isinstance(obj, str):
   ...              return obj
   ...          return super(type(ICustomAdapt), self).__adapt__(obj)

   >>> @zope.interface.implementer(ICustomAdapt)
   ... class CustomAdapt(object):
   ...     pass
   >>> ICustomAdapt('a string')
   'a string'
   >>> ICustomAdapt(CustomAdapt())
   <CustomAdapt object at ...>

.. seealso:: :func:`zope.interface.interfacemethod`, which explains
   how to override functions in interface definitions and why, prior
   to Python 3.6, the zero-argument version of `super` cannot be used.

.. _global_persistence:

Persistence, Sorting, Equality and Hashing
==========================================

.. tip:: For the practical implications of what's discussed below, and
         some potential problems, see :ref:`spec_eq_hash`.

Just like Python classes, interfaces are designed to inexpensively
support persistence using Python's standard :mod:`pickle` module. This
means that one process can send a *reference* to an interface to another
process in the form of a byte string, and that other process can load
that byte string and get the object that is that interface. The processes
may be separated in time (one after the other), in space (running on
different machines) or even be parts of the same process communicating
with itself.

We can demonstrate this. Observe how small the byte string needed to
capture the reference is. Also note that since this is the same
process, the identical object is found and returned:

.. doctest::

   >>> import sys
   >>> import pickle
   >>> class Foo(object):
   ...    pass
   >>> sys.modules[__name__].Foo = Foo # XXX, see below
   >>> pickled_byte_string = pickle.dumps(Foo, 0)
   >>> len(pickled_byte_string)
   21
   >>> imported = pickle.loads(pickled_byte_string)
   >>> imported == Foo
   True
   >>> imported is Foo
   True
   >>> class IFoo(zope.interface.Interface):
   ...     pass
   >>> sys.modules[__name__].IFoo = IFoo # XXX, see below
   >>> pickled_byte_string = pickle.dumps(IFoo, 0)
   >>> len(pickled_byte_string)
   22
   >>> imported = pickle.loads(pickled_byte_string)
   >>> imported is IFoo
   True
   >>> imported == IFoo
   True

The eagle-eyed reader will have noticed the two funny lines like
``sys.modules[__name__].Foo = Foo``. What's that for? To understand,
we must know a bit about how Python "pickles" (``pickle.dump`` or
``pickle.dumps``) classes or interfaces.

When Python pickles a class or an interface, it does so as a "global
object" [#global_object]_. Global objects are expected to already
exist (contrast this with pickling a string or an object instance,
which creates a new object in the receiving process) with all their
necessary state information (for classes and interfaces, the state
information would be things like the list of methods and defined
attributes) in the receiving process; the pickled byte string needs
only contain enough data to look up that existing object; this is a
*reference*. Not only does this minimize the amount of data required
to persist such an object, it also facilitates changing the definition
of the object over time: if a class or interface gains or loses
methods or attributes, loading a previously pickled reference will use
the *current definition* of the object.

The *reference* to a global object that's stored in the byte string
consists only of the object's ``__name__`` and ``__module__``. Before
a global object *obj* is pickled, Python makes sure that the object being
pickled is the same one that can be found at
``getattr(sys.modules[obj.__module__], obj.__name__)``; if there is no
such object, or it refers to a different object, pickling fails. The
two funny lines make sure that holds, no matter how this example is
run (using some doctest runners, it doesn't hold by default, unlike it
normally would).

We can show some examples of what happens when that condition doesn't
hold. First, what if we change the global object and try to pickle the
old one?

.. doctest::

   >>> sys.modules[__name__].Foo = 42
   >>> pickle.dumps(Foo)
   Traceback (most recent call last):
   ...
   _pickle.PicklingError: Can't pickle <class 'Foo'>: it's not the same object as builtins.Foo

A consequence of this is that only one object of the given name can be
defined and pickled at a time. If we were to try to define a new ``Foo``
class (remembering that normally the ``sys.modules[__name__].Foo =``
line is automatic), we still cannot pickle the old one:

.. doctest::

   >>> orig_Foo = Foo
   >>> class Foo(object):
   ...    pass
   >>> sys.modules[__name__].Foo = Foo # XXX, see below
   >>> pickle.dumps(orig_Foo)
   Traceback (most recent call last):
   ...
   _pickle.PicklingError: Can't pickle <class 'Foo'>: it's not the same object as builtins.Foo

Or what if there simply is no global object?

.. doctest::

   >>> del sys.modules[__name__].Foo
   >>> pickle.dumps(Foo)
   Traceback (most recent call last):
   ...
   _pickle.PicklingError: Can't pickle <class 'Foo'>: attribute lookup Foo on builtins failed

Interfaces and classes behave the same in all those ways.

.. rubric:: What's This Have To Do With Sorting, Equality and Hashing?

Another important design consideration for interfaces is that they
should be sortable. This permits them to be used, for example, as keys
in a (persistent) `BTree <https://btrees.readthedocs.io>`_. As such,
they define a total ordering, meaning that any given interface can
definitively said to be greater than, less than, or equal to, any
other interface. This relationship must be *stable* and hold the same
across any two processes.

An object becomes sortable by overriding the equality method
``__eq__`` and at least one of the comparison methods (such as
``__lt__``).

Classes, on the other hand, are not sortable [#class_sort]_.
Classes can only be tested for equality, and they implement this using
object identity: ``class_a == class_b`` is equivalent to ``class_a is class_b``.

In addition to being sortable, it's important for interfaces to be
hashable so they can be used as keys in dictionaries or members of
sets. This is done by implementing the ``__hash__`` method [#hashable]_.

Classes are hashable, and they also implement this based on object
identity, with the equivalent of ``id(class_a)``.

To be both hashable and sortable, the hash method and the equality and
comparison methods **must** `be consistent with each other
<https://docs.python.org/3/reference/datamodel.html#object.__hash__>`_.
That is, they must all be based on the same principle.

Classes use the principle of identity to implement equality and
hashing, but they don't implement sorting because identity isn't a
stable sorting method (it is different in every process).

Interfaces need to be sortable. In order for all three of hashing,
equality and sorting to be consistent, interfaces implement them using
the same principle as persistence. Interfaces are treated like "global
objects" and sort and hash using the same information a *reference* to
them would: their ``__name__`` and ``__module__``.

In this way, hashing, equality and sorting are consistent with each
other, and consistent with pickling:

.. doctest::

   >>> class IFoo(zope.interface.Interface):
   ...     pass
   >>> sys.modules[__name__].IFoo = IFoo
   >>> f1 = IFoo
   >>> pickled_f1 = pickle.dumps(f1)
   >>> class IFoo(zope.interface.Interface):
   ...     pass
   >>> sys.modules[__name__].IFoo = IFoo
   >>> IFoo == f1
   True
   >>> unpickled_f1 = pickle.loads(pickled_f1)
   >>> unpickled_f1 == IFoo == f1
   True

This isn't quite the case for classes; note how ``f1`` wasn't equal to
``Foo`` before pickling, but the unpickled value is:

.. doctest::

   >>> class Foo(object):
   ...     pass
   >>> sys.modules[__name__].Foo = Foo
   >>> f1 = Foo
   >>> pickled_f1 = pickle.dumps(Foo)
   >>> class Foo(object):
   ...     pass
   >>> sys.modules[__name__].Foo = Foo
   >>> f1 == Foo
   False
   >>> unpickled_f1 = pickle.loads(pickled_f1)
   >>> unpickled_f1 == Foo # Surprise!
   True
   >>> unpickled_f1 == f1
   False

For more information, and some rare potential pitfalls, see
:ref:`spec_eq_hash`.

.. rubric:: Footnotes

.. [#create] The main reason we subclass ``Interface`` is to cause the
             Python class statement to create an interface, rather
             than a class.

             It's possible to create interfaces by calling a special
             interface class directly.  Doing this, it's possible
             (and, on rare occasions, useful) to create interfaces
             that don't descend from ``Interface``.  Using this
             technique is beyond the scope of this document.

.. [#factory] Classes are factories.  They can be called to create
              their instances.  We expect that we will eventually
              extend the concept of implementation to other kinds of
              factories, so that we can declare the interfaces
              provided by the objects created.

.. [#compat] The goal is substitutability.  An object that provides an
             extending interface should be substitutable for an object
             that provides the extended interface.  In our example, an
             object that provides ``IBaz`` should be usable wherever an
             object that provides ``IBlat`` is expected.

             The interface implementation doesn't enforce this,
             but maybe it should do some checks.

.. [#class_sort] In Python 2, classes could be sorted, but the sort
                 was not stable (it also used the identity principle)
                 and not useful for persistence; this was considered a
                 bug that was fixed in Python 3.

.. [#hashable] In order to be hashable, you must implement both
               ``__eq__``  and ``__hash__``. If you only implement
               ``__eq__``, Python makes sure the type cannot be
               used in a dictionary, set, or with :func:`hash`. In
               Python 2, this wasn't the case, and forgetting to
               override ``__hash__`` was a constant source of bugs.

.. [#global_object] From the name of the pickle bytecode operator; it
                    varies depending on the protocol but always
                    includes "GLOBAL".
