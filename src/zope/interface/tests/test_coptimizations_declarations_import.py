##############################################################################
#
# Copyright (c) 2026 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY, TITLE, AND FITNESS FOR A PARTICULAR
# PURPOSE.
#
##############################################################################
"""Regression tests for reference leaks in the lazy declarations import
done by the C optimizations (see issue #363).

The first time a module-level function such as ``getObjectSpecification``
needs them, ``_zic_state_load_declarations`` imports
``zope.interface.declarations`` and fetches four attributes from it.  If one
of those steps failed, the module and any attribute already fetched were
never released.  That does not happen in ordinary use, so the reproducer
breaks one attribute on purpose and loads a second, independent instance of
the extension module, whose "already imported" flag is still unset.
"""
import textwrap
import unittest

from zope.interface.tests import run_child


# Usage: python -c _CHILD <attribute to break> <delete|not-a-type>
_CHILD = textwrap.dedent(
    """
    import gc
    import importlib.util
    import sys

    import zope.interface.declarations as declarations

    # The attributes in the order the C code fetches them.
    ATTRS = [
        "BuiltinImplementationSpecifications",
        "_empty",
        "implementedByFallback",
        "Implements",
    ]
    broken_attr, mode = sys.argv[1:]

    # A brand new module object gets its own module state, so its
    # "declarations already imported" flag starts unset -- unlike the
    # module in sys.modules, which never runs the code under test again.
    spec = importlib.util.find_spec(
        "zope.interface._zope_interface_coptimizations")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class Foo:
        pass

    # Everything the C code holds when it fails has to be released again:
    # the declarations module and each attribute fetched before the broken
    # one.  For "not-a-type" that includes the bogus value itself, so use a
    # fresh object() -- a small int would be immortal and could not show a
    # leak.
    watched = {"zope.interface.declarations": declarations}
    for name in ATTRS[:ATTRS.index(broken_attr)]:
        watched[name] = getattr(declarations, name)

    saved = getattr(declarations, broken_attr)
    if mode == "delete":
        delattr(declarations, broken_attr)
        expected = AttributeError
    else:
        not_a_type = object()
        setattr(declarations, broken_attr, not_a_type)
        watched[broken_attr] = not_a_type
        expected = TypeError

    def refcounts():
        # Look the objects up by key: iterating watched.items() leaves a
        # transient reference behind that skews the count on free-threaded
        # builds.
        gc.collect()
        return {name: sys.getrefcount(watched[name]) for name in watched}

    try:
        before = refcounts()
        try:
            module.getObjectSpecification(Foo())
        except expected:
            pass
        else:
            raise SystemExit("expected %s, the call succeeded" % expected)
        after = refcounts()
    finally:
        setattr(declarations, broken_attr, saved)

    for name in watched:
        if after[name] != before[name]:
            raise SystemExit(
                "refcount of %s went from %d to %d across a failed import"
                % (name, before[name], after[name]))

    # The failed attempt must not have left the module state half
    # populated: retrying on the same instance has to work.
    module.getObjectSpecification(Foo())
    print("ok")
    """
)


def _c_optimizations_in_use():
    from zope.interface.adapter import LookupBase
    return LookupBase.__module__ == "_zope_interface_coptimizations"


@unittest.skipUnless(
    _c_optimizations_in_use(), "requires the C implementation")
class DeclarationsImportRefcountTests(unittest.TestCase):

    def test_failed_lazy_import_does_not_leak(self):
        for attr, mode in [
            ("BuiltinImplementationSpecifications", "delete"),
            ("_empty", "delete"),
            ("implementedByFallback", "delete"),
            ("Implements", "delete"),
            ("Implements", "not-a-type"),
        ]:
            with self.subTest(attr=attr, mode=mode):
                result = run_child(_CHILD, attr, mode)
                self.assertEqual(
                    result.returncode, 0,
                    "returncode %r:\n%s"
                    % (result.returncode, result.stderr[-2000:]))
                self.assertIn("ok", result.stdout)
