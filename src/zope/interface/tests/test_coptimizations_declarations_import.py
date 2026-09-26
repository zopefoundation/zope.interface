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
"""Regression test for a reference leak in the lazy declarations import
done by the C optimizations (see issue #363).

``_zic_state_load_declarations`` imports ``zope.interface.declarations``
and pulls a handful of attributes off of it the first time a module-level
function such as ``getObjectSpecification`` needs them.  Every early
``return NULL`` on that path used to drop the module (and any attribute
already fetched) without decrefing it first.  The failure is only reached
when ``PyImport_ImportModule`` succeeds but a later
``PyObject_GetAttrString`` does not, which does not happen in ordinary
use -- so the reproducer below breaks the target attribute on purpose and
loads a second, independent instance of the extension module so the
module-level "already imported" cache does not just short circuit the
call.
"""
import os
import subprocess
import sys
import textwrap
import unittest


_CHILD = textwrap.dedent(
    """
    import gc
    import importlib.util
    import sys

    from zope.interface.adapter import LookupBase
    if LookupBase.__module__ != "_zope_interface_coptimizations":
        raise SystemExit("requires the C implementation")

    import zope.interface.declarations as decl_mod

    spec = importlib.util.find_spec(
        "zope.interface._zope_interface_coptimizations")
    if spec is None or spec.loader is None:
        raise SystemExit("could not locate the C extension's module spec")

    def fresh_module():
        # A brand new module object gets its own module state, so its
        # "have we already imported declarations" flag starts unset --
        # unlike the already-imported module in sys.modules, which would
        # just serve the cached attributes and never touch the code path
        # under test.
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    class Foo:
        pass

    saved = decl_mod.BuiltinImplementationSpecifications
    del decl_mod.BuiltinImplementationSpecifications
    try:
        broken = fresh_module()
        gc.collect()
        before = sys.getrefcount(decl_mod)
        try:
            broken.getObjectSpecification(Foo())
        except AttributeError:
            pass
        else:
            raise SystemExit(
                "expected AttributeError, call unexpectedly succeeded")
        gc.collect()
        after = sys.getrefcount(decl_mod)
    finally:
        decl_mod.BuiltinImplementationSpecifications = saved

    if after != before:
        raise SystemExit(
            "declarations module refcount went from %d to %d across a "
            "failed import" % (before, after))

    # The failed attempt must not have left the module state half
    # populated: a subsequent, successful load on another fresh instance
    # still has to work normally.
    working = fresh_module()
    working.getObjectSpecification(Foo())
    print("ok")
    """
)


class DeclarationsImportRefcountTests(unittest.TestCase):

    def test_failed_lazy_import_does_not_leak_declarations_module(self):
        from zope.interface.adapter import LookupBase

        if LookupBase.__module__ != "_zope_interface_coptimizations":
            self.skipTest("requires the C implementation")
        if sys.version_info < (3, 11):
            self.skipTest(
                "the heap-types module state is only used on Python 3.11+")

        # Run in a subprocess: the reproducer deletes an attribute from the
        # real zope.interface.declarations module and loads extra instances
        # of the C extension, and a failure here should not take the whole
        # test run down with it.
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(
            p for p in sys.path if p))
        result = subprocess.run(
            [sys.executable, "-c", _CHILD],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
        self.assertEqual(
            result.returncode,
            0,
            "declarations import refcount check failed "
            "(returncode %r):\n%s"
            % (result.returncode, result.stderr[-2000:]),
        )
        self.assertIn("ok", result.stdout)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
