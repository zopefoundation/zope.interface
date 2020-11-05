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
import sys

from distutils.errors import CCompilerError
from distutils.errors import DistutilsExecError
from distutils.errors import DistutilsPlatformError

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from setuptools import find_packages


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
        print("")
        print(e)
        print('*' * 80)


codeoptimization_c = os.path.join('src', 'zope', 'interface',
                                  '_zope_interface_coptimizations.c')
codeoptimization = [
    Extension(
        "zope.interface._zope_interface_coptimizations",
        [os.path.normcase(codeoptimization_c)]
    ),
]

is_jython = 'java' in sys.platform
is_pypy = hasattr(sys, 'pypy_version_info')

# Jython cannot build the C optimizations. Nor, as of 7.3, can PyPy (
# it doesn't have PySuper_Type) Everywhere else, defer the decision to
# runtime.
if is_jython or is_pypy:
    ext_modules = []
else:
    ext_modules = codeoptimization
tests_require = [
    # The test dependencies should NOT have direct or transitive
    # dependencies on zope.interface.
    'coverage >= 5.0.3',
    'zope.event',
    'zope.testing',
]
testing_extras = tests_require


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()


long_description = (
        read('README.rst')
        + '\n' +
        read('CHANGES.rst')
        )

setup(name='zope.interface',
      version='5.2.1.dev0',
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
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: Python :: Implementation :: CPython",
          "Programming Language :: Python :: Implementation :: PyPy",
          "Framework :: Zope :: 3",
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
      python_requires=', '.join([
          '>=2.7',
          '!=3.0.*',
          '!=3.1.*',
          '!=3.2.*',
          '!=3.3.*',
          '!=3.4.*',
      ]),
      extras_require={
          'docs': ['Sphinx', 'repoze.sphinx.autointerface'],
          'test': tests_require,
          'testing': testing_extras,
      },
      ext_modules=ext_modules,
      keywords=['interface', 'components', 'plugins'],
)
