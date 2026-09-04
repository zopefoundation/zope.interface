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

On a free-threaded build, concurrent ``lookup()`` and ``changed()`` calls used to crash the
interpreter (a data race on the ``_cache``/``_mcache``/``_scache`` fields). This runs the
reproducer in a subprocess so a regression is observed as a non-zero exit rather than taking
the whole test run down; on GIL builds it trivially passes.
"""
import subprocess
import sys
import textwrap
import unittest


_CHILD = textwrap.dedent(
    """
    import threading, time
    from zope.interface import Interface
    from zope.interface.adapter import AdapterRegistry, AdapterLookup

    class IA(Interface): pass
    class IB(Interface): pass

    reg = AdapterRegistry()
    reg.register([IA], IB, "", "v")
    lk = AdapterLookup(reg)
    stop = threading.Event()

    def reader():
        while not stop.is_set():
            try:
                lk.lookup([IA], IB, "")
            except Exception:
                pass

    def clearer():
        while not stop.is_set():
            try:
                lk.changed(None)
            except Exception:
                pass

    threads = ([threading.Thread(target=reader) for _ in range(8)]
               + [threading.Thread(target=clearer) for _ in range(4)])
    for t in threads:
        t.start()
    time.sleep(3)
    stop.set()
    for t in threads:
        t.join()
    print("ok")
    """
)


class ConcurrentLookupChangedTests(unittest.TestCase):

    def test_concurrent_lookup_and_changed_does_not_crash(self):
        result = subprocess.run(
            [sys.executable, "-c", _CHILD],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(
            result.returncode, 0,
            "concurrent lookup()/changed() crashed the interpreter "
            "(returncode %r):\n%s" % (result.returncode, result.stderr[-2000:]),
        )
        self.assertIn("ok", result.stdout)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
