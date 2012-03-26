import os
import sys
from distutils.errors import (CCompilerError, DistutilsExecError, 
                              DistutilsPlatformError)
try:
    from setuptools.command.build_ext import build_ext
    from pkg_resources import (normalize_path, working_set, 
                               add_activation_listener, require)
except ImportError:
    raise RuntimeError("zope.interface requires Distribute under Python 3. "
                       "See http://packages.python.org/distribute")

class optional_build_ext(build_ext):
    """This class subclasses build_ext and allows
       the building of C extensions to fail.
    """
    def run(self):
        try:
            build_ext.run(self)
        
        except DistutilsPlatformError as e:
            self._unavailable(e)

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        
        except (CCompilerError, DistutilsExecError) as e:
            self._unavailable(e)

    def _unavailable(self, e):
        print('*' * 80, file=sys.stderr)
        print("""WARNING:

        An optional code optimization (C extension) could not be compiled.

        Optimizations for this package will not be available!""", file=sys.stderr)
        print(file=sys.stderr)
        print(e, file=sys.stderr)
        print('*' * 80, file=sys.stderr)
