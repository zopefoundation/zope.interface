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

try:
    from setuptools import setup, Extension, Feature
except ImportError:
    # do we need to support plain distutils for building when even
    # the package itself requires setuptools for installing?
    from distutils.core import setup, Extension

    if sys.version_info[:2] >= (2, 4):
        extra = dict(
            package_data={
                'zope.interface': ['*.txt'],
                'zope.interface.tests': ['*.txt'],
                }
            )
    else:
        extra = {}

else:
    codeoptimization_c = os.path.join('src', 'zope', 'interface',
                                      '_zope_interface_coptimizations.c')
    codeoptimization = Feature(
            "Optional code optimizations",
            standard = True,
            ext_modules = [Extension(
                           "zope.interface._zope_interface_coptimizations",
                           [os.path.normcase(codeoptimization_c)]
                          )])
    py_impl = getattr(platform, 'python_implementation', lambda: None)
    is_pypy = py_impl() == 'PyPy'
    is_jython = 'java' in sys.platform

    # Jython cannot build the C optimizations, while on PyPy they are
    # anti-optimizations (the C extension compatibility layer is known-slow,
    # and defeats JIT opportunities).
    if is_pypy or is_jython:
        features = {}
    else:
        features = {'codeoptimization': codeoptimization}
    extra = dict(
        namespace_packages=["zope"],
        include_package_data = True,
        zip_safe = False,
        tests_require = [],
        install_requires = ['setuptools'],
        extras_require={'docs': ['z3c.recipe.sphinxdoc']},
        features = features
        )

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description=(
        read('README.txt')
        + '\n' +
        read('CHANGES.txt')
        )

try: # Zope 3 setuptools versions
    from build_ext_3 import optional_build_ext
    # This is Python 3. Setuptools is now required, and so is zope.fixers.
    extra['install_requires'] = ['setuptools']
    extra['setup_requires'] = ['zope.fixers']
    extra['use_2to3'] = True
    extra['convert_2to3_doctests'] = [
        'src/zope/interface/README.ru.txt',
        'src/zope/interface/README.txt',
        'src/zope/interface/adapter.ru.txt',
        'src/zope/interface/adapter.txt',
        'src/zope/interface/human.ru.txt',
        'src/zope/interface/human.txt',
        'src/zope/interface/index.txt',
        'src/zope/interface/verify.txt',
        ]
    extra['use_2to3_fixers'] = ['zope.fixers']

except (ImportError, SyntaxError):
    from build_ext_2 import optional_build_ext
    
setup(name='zope.interface',
      version='3.6.6dev',
      url='http://pypi.python.org/pypi/zope.interface',
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
        "Programming Language :: Python :: 2.4",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Topic :: Software Development :: Libraries :: Python Modules",
      ],

      packages = ['zope', 'zope.interface', 'zope.interface.tests'],
      package_dir = {'': 'src'},
      cmdclass = {'build_ext': optional_build_ext,
                  },
      test_suite = 'zope.interface.tests',
      **extra)
