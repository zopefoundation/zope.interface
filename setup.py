##############################################################################
#
# Copyright (c) 2004-2007 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
# This package is developed by the Zope Toolkit project, documented here:
# http://docs.zope.org/zopetoolkit
# When developing and releasing this package, please follow the documented
# Zope Toolkit policies as described by this documentation.
##############################################################################
"""Setup for zope.interface package
"""

import os
import platform
import sys

from setuptools import setup, Extension, Feature
from setuptools.command.build_ext import build_ext
from setuptools import find_packages

from distutils.errors import CCompilerError
from distutils.errors import DistutilsExecError
from distutils.errors import DistutilsPlatformError


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
        except (CCompilerError, DistutilsExecError, OSError) as e:
            self._unavailable(e)

    def _unavailable(self, e):
        print('*' * 80)
        print("""WARNING:

        An optional code optimization (C extension) could not be compiled.

        Optimizations for this package will not be available!""")
        print()
        print(e)
        print('*' * 80)

codeoptimization_c = os.path.join('src', 'zope', 'interface',
                                  '_zope_interface_coptimizations.c')
codeoptimization = Feature(
        "Optional code optimizations",
        standard=True,
        ext_modules=[
            Extension(
                "zope.interface._zope_interface_coptimizations",
                [os.path.normcase(codeoptimization_c)]
            )
        ])
py_impl = getattr(platform, 'python_implementation', lambda: None)
is_pypy = py_impl() == 'PyPy'
is_jython = 'java' in sys.platform
is_pure = 'PURE_PYTHON' in os.environ

# Jython cannot build the C optimizations, while on PyPy they are
# anti-optimizations (the C extension compatibility layer is known-slow,
# and defeats JIT opportunities).
if is_pypy or is_jython or is_pure:
    features = {}
else:
    features = {'codeoptimization': codeoptimization}
tests_require = ['zope.event']
testing_extras = tests_require + ['nose', 'coverage']


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()

long_description=(
        read('README.rst')
        + '\n' +
        read('CHANGES.rst')
        )

setup(name='zope.interface',
      version='4.4.4.dev0',
      url='https://github.com/zopefoundation/zope.interface',
      license='ZPL 2.1',
      description='Interfaces for Python',
      author='Zope Foundation and Contributors',
      author_email='zope-dev@zope.org',
      long_description=long_description,
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Framework :: Zope3",
        "Topic :: Software Development :: Libraries :: Python Modules",
      ],
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=["zope"],
      cmdclass={
          'build_ext': optional_build_ext,
      },
      test_suite='zope.interface.tests',
      include_package_data=True,
      zip_safe=False,
      tests_require=tests_require,
      install_requires=['setuptools'],
      extras_require={
          'docs': ['Sphinx', 'repoze.sphinx.autointerface'],
          'test': tests_require,
          'testing': testing_extras,
      },
      features=features,
      keywords=['interface', 'components', 'plugins'],
)
