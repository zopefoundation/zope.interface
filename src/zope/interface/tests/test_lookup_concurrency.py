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
"""Concurrency regression test for the LookupBase cache (see issue #380).

On a free-threaded build, concurrent lookup and invalidation calls used to
crash the interpreter.  Run the reproducer in a subprocess so a regression is
observed as a non-zero exit rather than taking the whole test run down.
"""
import subprocess
import sys
import textwrap
import unittest


_CHILD = textwrap.dedent(
    """
    import sys
    import threading
    import time
    import traceback
    from zope.interface.adapter import LookupBase

    if LookupBase.__module__ != "_zope_interface_coptimizations":
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

    lk = Lookup()
    required = (object(),)
    provided = object()
    stop = threading.Event()
    errors = []
    errors_lock = threading.Lock()

    if sys._is_gil_enabled():
        raise SystemExit(
            "the concurrency regression requires the GIL disabled"
        )

    operations = (
        lambda: lk.lookup(required, provided, ""),
        lambda: lk.lookupAll(required, provided),
        lambda: lk.subscriptions(required, provided),
    )

    def record_error():
        with errors_lock:
            errors.append(traceback.format_exc())
        stop.set()

    def reader(index):
        operation = operations[index % len(operations)]
        while not stop.is_set():
            try:
                operation()
            except Exception:
                record_error()

    def clearer():
        while not stop.is_set():
            try:
                lk.changed(None)
            except Exception:
                record_error()

    threads = (
        [threading.Thread(target=reader, args=(i,)) for i in range(9)]
        + [threading.Thread(target=clearer) for _ in range(4)]
    )
    for t in threads:
        t.start()
    time.sleep(3)
    stop.set()
    for t in threads:
        t.join()
    if errors:
        print(errors[0], file=sys.stderr)
        raise SystemExit("lookup/changed worker raised")
    print("ok")
    """
)


class ConcurrentLookupChangedTests(unittest.TestCase):

    def test_concurrent_lookup_and_changed_does_not_crash(self):
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
            [sys.executable, "-c", _CHILD],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(
            result.returncode,
            0,
            "concurrent lookup()/changed() crashed the interpreter "
            "(returncode %r):\n%s"
            % (result.returncode, result.stderr[-2000:]),
        )
        self.assertIn("ok", result.stdout)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
