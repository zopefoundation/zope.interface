import sys
from distutils.errors import (CCompilerError, DistutilsExecError, 
                              DistutilsPlatformError)
try:
    from setuptools.command.build_ext import build_ext
except ImportError:
    from distutils.command.build_ext import build_ext
    

class optional_build_ext(build_ext):
    """This class subclasses build_ext and allows
       the building of C extensions to fail.
    """
    def run(self):
        try:
            build_ext.run(self)
        
        except DistutilsPlatformError, e:
            self._unavailable(e)

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        
        except (CCompilerError, DistutilsExecError), e:
            self._unavailable(e)

    def _unavailable(self, e):
        print >> sys.stderr, '*' * 80
        print >> sys.stderr, """WARNING:

        An optional code optimization (C extension) could not be compiled.

        Optimizations for this package will not be available!"""
        print >> sys.stderr
        print >> sys.stderr, e
        print >> sys.stderr, '*' * 80
        