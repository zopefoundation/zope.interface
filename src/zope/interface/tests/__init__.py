from zope.interface._compat import _should_attempt_c_optimizations


class OptimizationTestMixin(object):
    """
    Helper for testing that C optimizations are used
    when appropriate.
    """

    def _getTargetClass(self):
        """
        Define this to return the implementation in use,
        without the 'Py' or 'Fallback' suffix.
        """
        raise NotImplementedError

    def _getFallbackClass(self):
        """
        Define this to return the fallback Python implementation.
        """
        # Is there an algorithmic way to do this? The C
        # objects all come from the same module so I don't see how we can
        # get the Python object from that.
        raise NotImplementedError

    def test_optimizations(self):
        used = self._getTargetClass()
        fallback = self._getFallbackClass()

        if _should_attempt_c_optimizations():
            self.assertIsNot(used, fallback)
        else:
            self.assertIs(used, fallback)

# Be sure cleanup functionality is available; classes that use the adapter hook
# need to be sure to subclass ``CleanUp``.
#
# If zope.component is installed and imported when we run our tests
# (import chain:
# zope.testrunner->zope.security->zope.location->zope.component.api)
# it adds an adapter hook that uses its global site manager. That can cause
# leakage from one test to another unless its cleanup hooks are run. The symptoms can
# be odd, especially if one test used C objects and the next used the Python
# implementation. (For example, you can get strange TypeErrors or find inexplicable
# comparisons being done.)
try:
    from zope.testing import cleanup
except ImportError:
    class CleanUp(object):
        def cleanUp(self):
            pass

        setUp = tearDown = cleanUp
else:
    CleanUp = cleanup.CleanUp
