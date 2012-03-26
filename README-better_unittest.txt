Overview
========

This branch has three goals:

- Convert all doctests in zope.interface to "normal" Sphinx documentation

- Replace existin API coverage previously provided by the doctests with
  standard unit tests.  

- Get the unit test coverage, sans doctests, to 100%.

There are secondary, related cleanups, mostly in line with the coding
standards for unit tests proposed here:

- http://palladion.com/home/tseaver/obzervationz/2008/unit_testing_notes-20080724

- http://palladion.com/home/tseaver/obzervationz/2009/unit_testing_redux-20090802

TODO
====

- [_] Move doctest files to docs:

      o ``src/zope/interface/README.txt``

      o ``src/zope/interface/index.txt``

      o ``src/zope/interface/adapter.txt``

      o ``src/zope/interface/human.txt``

      o ``src/zope/interface/verify.txt``

      o ``src/zope/interface/tests/foodforthought``

      o ``src/zope/interface/README.ru.txt``

      o ``src/zope/interface/adapter.ru.txt``

      o ``src/zope/interface/human.ru.txt``

- [X] Remove ``src/zope/interface/tests/unitfixtures.py``.

- [X] Test both C and Python implementations.

- [X] 100% unit test coverage when run under ``nose --with-coverage``:

      * :mod:`zope.interface`

      * :mod:`zope.interface.adapter`

      * :mod:`zope.interface.common`

      * :mod:`zope.interface.common.idatetime`

      * :mod:`zope.interface.common.interfaces`

      * :mod:`zope.interface.common.mapping`

      * :mod:`zope.interface.common.sequence`

      * :mod:`zope.interface.advice`

      * :mod:`zope.interface.declarations`

      * :mod:`zope.interface.document`

      * :mod:`zope.interface.exceptions`

      * :mod:`zope.interface.interface`

      * :mod:`zope.interface.interfaces`

      * :mod:`zope.interface.registry`

      * :mod:`zope.interface.ro`

      * :mod:`zope.interface.verify`
