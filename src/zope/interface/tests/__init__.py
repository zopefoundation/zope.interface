import os
import subprocess
import sys

from zope.interface._compat import _should_attempt_c_optimizations


class OptimizationTestMixin:
    """Mixin testing that C optimizations are used when appropriate.
    """

    def _getTargetClass(self):
        """Return the implementation in use, without 'Py' or 'Fallback' suffix.
        """
        raise NotImplementedError

    def _getFallbackClass(self):
        """Return the fallback Python implementation.
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


class SubclassableMixin:

    def _getTargetClass(self):
        """Return the implementation in use without 'Py' or 'Fallback' suffix.
        """
        raise NotImplementedError

    def test_can_subclass(self):
        klass = self._getTargetClass()

        class Derived(klass):  # no raise
            pass


class MissingSomeAttrs:
    """
    Helper for tests that raises a specific exception
    for attributes that are missing. This is usually not
    an AttributeError, and this object is used to test that
    those errors are not improperly caught and treated like
    an AttributeError.
    """

    def __init__(self, exc_kind, **other_attrs):
        self.__exc_kind = exc_kind
        d = object.__getattribute__(self, '__dict__')
        d.update(other_attrs)

    def __getattribute__(self, name):
        # Note that we ignore objects found in the class dictionary.
        d = object.__getattribute__(self, '__dict__')
        try:
            return d[name]
        except KeyError:
            raise d['_MissingSomeAttrs__exc_kind'](name)

    EXCEPTION_CLASSES = (
        TypeError,
        RuntimeError,
        BaseException,
        ValueError,
    )

    @classmethod
    def test_raises(cls, unittest, test_func, expected_missing, **other_attrs):
        """
        Loop through various exceptions, calling *test_func* inside a
        ``assertRaises`` block.

        :param test_func: A callable of one argument, the instance of this
            class.
        :param str expected_missing: The attribute that should fail with the
            exception.  This is used to ensure that we're testing the path we
            think we are.
        :param other_attrs: Attributes that should be provided on the test
            object.  Must not contain *expected_missing*.
        """
        assert isinstance(expected_missing, str)
        assert expected_missing not in other_attrs
        for exc in cls.EXCEPTION_CLASSES:
            ob = cls(exc, **other_attrs)
            with unittest.assertRaises(exc) as ex:
                test_func(ob)

            unittest.assertEqual(ex.exception.args[0], expected_missing)

        # Now test that the AttributeError for that expected_missing is *not*
        # raised.
        ob = cls(AttributeError, **other_attrs)
        try:
            test_func(ob)
        except AttributeError as e:
            unittest.assertNotIn(expected_missing, str(e))
        except Exception:  # pylint:disable=broad-except
            pass

# Be sure cleanup functionality is available; classes that use the adapter hook
# need to be sure to subclass ``CleanUp``.
#
# If zope.component is installed and imported when we run our tests
# (import chain:
# zope.testrunner->zope.security->zope.location->zope.component.api)
# it adds an adapter hook that uses its global site manager. That can cause
# leakage from one test to another unless its cleanup hooks are run. The
# symptoms can be odd, especially if one test used C objects and the next used
# the Python implementation. (For example, you can get strange TypeErrors or
# find inexplicable comparisons being done.)


try:
    from zope.testing import cleanup
except ImportError:

    class CleanUp:
        def cleanUp(self):
            pass

        setUp = tearDown = cleanUp
else:
    CleanUp = cleanup.CleanUp


def run_child(code, *args):
    """Run *code* with ``python -c`` in a subprocess and return the result.

    For reproducers that have to run in a fresh interpreter, so that a crash
    or a broken module is observed as a non-zero exit rather than taking the
    test run down.

    A test runner that injects egg paths into sys.path in process --
    buildout's bin/test via zc.recipe.testrunner -- leaves nothing for a
    subprocess to inherit, and the child then dies on the import instead of
    running the reproducer.  Passing them on through PYTHONPATH is a
    workaround, not an exact copy of this process's import state: it cannot
    carry an entry containing os.pathsep, it places these paths ahead of the
    child's standard library, and it does not reproduce import hooks.  Good
    enough to reach the reproducer, which is all the child needs.
    """
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(
        p for p in sys.path if p))
    return subprocess.run(
        [sys.executable, "-c", code, *args],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
