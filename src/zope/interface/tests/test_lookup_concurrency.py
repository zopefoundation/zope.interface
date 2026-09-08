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
"""Concurrency regressions for lookup cache lifetimes (see issue #380).

On a free-threaded build, concurrent lookup and invalidation calls used to
crash the interpreter.  VerifyingBase also kept unsynchronized verification
snapshots across Python callbacks.  Run the reproducers in subprocesses so a
regression is observed as a non-zero exit rather than taking the test run down.
"""
import subprocess
import sys
import textwrap
import unittest


_CACHE_CHILD = textwrap.dedent(
    """
    import sys
    import threading
    import time
    import traceback
    from zope.interface.adapter import LookupBase
    from zope.interface.adapter import VerifyingBase

    if (
        LookupBase.__module__ != "_zope_interface_coptimizations"
        or VerifyingBase.__module__ != "_zope_interface_coptimizations"
    ):
        raise SystemExit(
            "the concurrency regression requires the C implementation"
        )

    class Lookup(LookupBase):
        def _uncached_lookup(self, required, provided, name):
            return None

        def _uncached_lookupAll(self, required, provided):
            return ()

        def _uncached_subscriptions(self, required, provided):
            return ()

    class Generation:
        @property
        def _generation(self):
            # PyObject_GetAttr() in _verify() can run arbitrary Python.  Yield
            # here to widen the read-versus-changed() lifetime window.
            time.sleep(0)
            return 1

    class Registry:
        def __init__(self):
            self.ro = (Generation(), Generation())

    class VerifyingLookup(VerifyingBase):
        def __init__(self):
            super().__init__()
            self._registry = Registry()
            self.changed(None)

        def _uncached_lookup(self, required, provided, name):
            return None

        def _uncached_lookupAll(self, required, provided):
            return ()

        def _uncached_subscriptions(self, required, provided):
            return ()

    lk = Lookup()
    verifying = VerifyingLookup()
    required = (object(),)
    provided = object()
    stop = threading.Event()
    errors = []
    errors_lock = threading.Lock()

    if sys._is_gil_enabled():
        raise SystemExit(
            "the concurrency regression requires the GIL disabled"
        )

    plain_operations = (
        lambda: lk.lookup(required, provided, ""),
        lambda: lk.lookupAll(required, provided),
        lambda: lk.subscriptions(required, provided),
    )
    verifying_operations = (
        lambda: verifying.lookup(required, provided, ""),
        lambda: verifying.lookupAll(required, provided),
        lambda: verifying.subscriptions(required, provided),
    )

    def record_error():
        with errors_lock:
            errors.append(traceback.format_exc())
        stop.set()

    def reader(operations, index):
        operation = operations[index % len(operations)]
        while not stop.is_set():
            try:
                operation()
            except Exception:
                record_error()

    def clearer(target):
        while not stop.is_set():
            try:
                target.changed(None)
            except Exception:
                record_error()

    threads = (
        [
            threading.Thread(target=reader, args=(plain_operations, i))
            for i in range(6)
        ]
        + [threading.Thread(target=clearer, args=(lk,)) for _ in range(2)]
        + [
            threading.Thread(target=reader, args=(verifying_operations, i))
            for i in range(6)
        ]
        + [
            threading.Thread(target=clearer, args=(verifying,))
            for _ in range(2)
        ]
    )
    for t in threads:
        t.start()
    stop.wait(3)
    stop.set()
    for t in threads:
        t.join()
    if errors:
        print(errors[0], file=sys.stderr)
        raise SystemExit("lookup/changed worker raised")
    print("ok")
    """
)

_VERIFY_SNAPSHOT_CHILD = textwrap.dedent(
    """
    import sys
    import threading
    from zope.interface.adapter import VerifyingBase

    if (
        sys._is_gil_enabled()
        or VerifyingBase.__module__ != "_zope_interface_coptimizations"
    ):
        raise SystemExit(
            "the concurrency regression requires the C implementation "
            "with the GIL disabled"
        )

    entered = threading.Event()
    resume = threading.Event()

    class Generation:
        armed = False

        @property
        def _generation(self):
            if self.armed:
                entered.set()
                if not resume.wait(10):
                    raise RuntimeError("timed out waiting for changed()")
            return 1

    generation = Generation()

    class Registry:
        short = False

        @property
        def ro(self):
            if self.short:
                return (object(),)
            return (object(), generation)

    registry = Registry()

    class Lookup(VerifyingBase):
        def __init__(self):
            super().__init__()
            self._registry = registry
            self.changed(None)

        def _uncached_lookup(self, required, provided, name):
            return None

        def _uncached_lookupAll(self, required, provided):
            return ()

        def _uncached_subscriptions(self, required, provided):
            return ()

    lookup = Lookup()
    generation.armed = True
    errors = []

    def read():
        try:
            lookup.lookup((object(),), object(), "")
        except Exception as exc:
            errors.append(repr(exc))

    thread = threading.Thread(target=read)
    thread.start()
    if not entered.wait(10):
        raise SystemExit("_verify() did not reach the generation callback")

    # Publish a differently-sized verification snapshot while _verify() is
    # suspended in Python.  The reader must finish against the old strong
    # snapshot instead of indexing the replacement fields.
    registry.short = True
    lookup.changed(None)
    resume.set()
    thread.join(10)
    if thread.is_alive():
        raise SystemExit("verification reader did not finish")
    if errors:
        raise SystemExit("verification reader raised: " + errors[0])
    print("ok")
    """
)


class ConcurrentLookupChangedTests(unittest.TestCase):

    def _run_child(self, child, label):
        from zope.interface.adapter import LookupBase

        if (
            not hasattr(sys, "_is_gil_enabled") or
            sys._is_gil_enabled() or
            LookupBase.__module__ != "_zope_interface_coptimizations"
        ):
            self.skipTest(
                "requires the C implementation on a free-threaded interpreter"
            )

        result = subprocess.run(
            [sys.executable, "-c", child],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(
            result.returncode,
            0,
            "%s failed "
            "(returncode %r):\n%s"
            % (label, result.returncode, result.stderr[-2000:]),
        )
        self.assertIn("ok", result.stdout)

    def test_concurrent_lookup_and_changed_does_not_crash(self):
        self._run_child(_CACHE_CHILD, "concurrent lookup()/changed()")

    def test_verify_uses_one_strong_snapshot(self):
        self._run_child(
            _VERIFY_SNAPSHOT_CHILD,
            "concurrent _verify()/changed()")


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
