Hacking on :mod:`zope.interface`
================================


Getting the Code
-----------------

The main repository for :mod:`zope.interface` is in the Zope Subversion
repository:

http://svn.zope.org/zope.interface

You can get a read-only Subversion checkout from there:

.. code-block:: sh

   $ svn checkout svn://svn.zope.org/repos/main/zope.interface/trunk zope.interface

The project also mirrors the trunk from the Subversion repository as a
Bazaar branch on Launchpad:

https://code.launchpad.net/zope.interface

You can branch the trunk from there using Bazaar:

.. code-block:: sh

   $ bzr branch lp:zope.interface


Running the tests in a ``virtualenv``
-------------------------------------

If you use the ``virtualenv`` package to create lightweight Python
development environments, you can run the tests using nothing more
than the ``python`` binary in a virtualenv.  First, create a scratch
environment:

.. code-block:: sh

   $ /path/to/virtualenv --no-site-packages /tmp/hack-zope.interface

Next, get this package registered as a "development egg" in the
environment:

.. code-block:: sh

   $ /tmp/hack-zope.interface/bin/python setup.py develop

Finally, run the tests using the build-in ``setuptools`` testrunner:

.. code-block:: sh

   $ /tmp/hack-zope.interface/bin/python setup.py test -q
   running test
   ...
   ----------------------------------------------------------------------
   Ran 2 tests in 0.000s

   OK

The ``dev`` command alias downloads and installs extra tools, like the
:mod:`nose` testrunner and the :mod:`coverage` coverage analyzer:

.. code-block:: sh

   $ /tmp/hack-zope.interface/bin/python setup.py dev
   $ /tmp/hack-zope.interface/bin/nosetests
   running nosetests
   .................................... (lots more dots)
   ----------------------------------------------------------------------
   Ran 707 tests in 2.166s

   OK

If you have the :mod:`coverage` pacakge installed in the virtualenv,
you can see how well the tests cover the code:

.. code-block:: sh

   $ /tmp/hack-zope.interface/bin/nosetests --with coverage
   running nosetests
   .................................... (lots more dots)
   Name                               Stmts   Miss  Cover   Missing
   ----------------------------------------------------------------
   zope.interface                        30      0   100%   
   zope.interface.adapter               440      0   100%   
   zope.interface.advice                 69      0   100%   
   zope.interface.common                  0      0   100%   
   zope.interface.common.idatetime       98      0   100%   
   zope.interface.common.interfaces      81      0   100%   
   zope.interface.common.mapping         32      0   100%   
   zope.interface.common.sequence        38      0   100%   
   zope.interface.declarations          312      0   100%   
   zope.interface.document               54      0   100%   
   zope.interface.exceptions             21      0   100%   
   zope.interface.interface             378      0   100%   
   zope.interface.interfaces            137      0   100%   
   zope.interface.registry              300      0   100%   
   zope.interface.ro                     25      0   100%   
   zope.interface.verify                 48      0   100%   
   ----------------------------------------------------------------
   TOTAL                               2063      0   100%   
   ----------------------------------------------------------------------
   Ran 707 tests in 2.166s

   OK


Building the documentation in a ``virtualenv``
----------------------------------------------

:mod:`zope.interface` uses the nifty :mod:`Sphinx` documentation system
for building its docs.  Using the same virtualenv you set up to run the
tests, you can build the docs:

The ``docs`` command alias downloads and installs Sphinx and its dependencies:

.. code-block:: sh

   $ /tmp/hack-zope.interface/bin/python setup.py docs
   ...
   $ bin/sphinx-build -b html -d docs/_build/doctrees docs docs/_build/html
   ...
   build succeeded.

   Build finished. The HTML pages are in docs/_build/html.

You can also test the code snippets in the documentation:

.. code-block:: sh

   $ bin/sphinx-build -b doctest -d docs/_build/doctrees docs docs/_build/doctest
   ...
   running tests...

   Document: index
   ---------------
   1 items passed all tests:
     17 tests in default
   17 tests in 1 items.
   17 passed and 0 failed.
   Test passed.

   Doctest summary
   ===============
      17 tests
       0 failures in tests
       0 failures in setup code
   build succeeded.
   Testing of doctests in the sources finished, look at the  \
       results in docs/_build/doctest/output.txt.


Running the tests using  :mod:`zc.buildout`
-------------------------------------------

:mod:`zope.interface` ships with its own :file:`buildout.cfg` file and
:file:`bootstrap.py` for setting up a development buildout:

.. code-block:: sh

   $ /path/to/python2.6 bootstrap.py
   ...
   Generated script '.../bin/buildout'
   $ bin/buildout
   Develop: '/home/tseaver/projects/Zope/BTK/interface/.'
   ...
   Generated script '.../bin/sphinx-quickstart'.
   Generated script '.../bin/sphinx-build'.

You can now run the tests:

.. code-block:: sh

   $ bin/test --all
   Running zope.testing.testrunner.layer.UnitTests tests:
     Set up zope.testing.testrunner.layer.UnitTests in 0.000 seconds.
     Ran 702 tests with 0 failures and 0 errors in 0.000 seconds.
   Tearing down left over layers:
     Tear down zope.testing.testrunner.layer.UnitTests in 0.000 seconds.


Building the documentation using :mod:`zc.buildout`
---------------------------------------------------

The :mod:`zope.inteface` buildout installs the Sphinx scripts required to build
the documentation, including testing its code snippets:

.. todo:: verify this!

.. code-block:: sh

   $ cd docs
   $ PATH=../bin:$PATH make doctest html
   .../bin/sphinx-build -b doctest -d .../docs/_build/doctrees   .../docs .../docs/_build/doctest
   running tests...

   Document: index
   ---------------
   1 items passed all tests:
     17 tests in default
   17 tests in 1 items.
   17 passed and 0 failed.
   Test passed.

   Doctest summary
   ===============
      17 tests
       0 failures in tests
       0 failures in setup code
   build succeeded.
   Testing of doctests in the sources finished, look at the  results in .../docs/_build/doctest/output.txt.
   .../bin/sphinx-build -b html -d .../docs/_build/doctrees   .../docs .../docs/_build/html
   ...
   build succeeded.

   Build finished. The HTML pages are in .../docs/_build/html.


Submitting a Bug Report
-----------------------

:mod:`zope.interface` tracks its bugs on Launchpad:

https://bugs.launchpad.net/zope.interface

Please submit bug reports and feature requests there.


Sharing Your Changes
--------------------

.. note::

   Please ensure that all tests are passing before you submit your code.
   If possible, your submission should include new tests for new features
   or bug fixes, although it is possible that you may have tested your
   new code by updating existing tests.

If you got a read-only checkout from the Subversion repository, and you
have made a change you would like to share, the best route is to let
Subversion help you make a patch file:

.. code-block:: sh

   $ svn diff > zope.interface-cool_feature.patch

You can then upload that patch file as an attachment to a Launchpad bug
report.

If you branched the code from Launchpad using Bazaar, you have another
option:  you can "push" your branch to Launchpad:

.. code-block:: sh

   $ bzr push lp:~tseaver/zope.interface/cool_feature

After pushing your branch, you can link it to a bug report on Launchpad,
or request that the maintainers merge your branch using the Launchpad
"merge request" feature.
