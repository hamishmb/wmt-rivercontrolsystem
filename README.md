# Wimborne Model Town's River Control System Software.

This repository holds the latest bleeding edge versions
of the river control software.

Release Management
==================

Releases are managed here as well - click the button
labeled "x releases" above to see the source code for
each release.

I make a new release when I consider the software to be
somewhat stable or "complete" for a particular deployment,
rather than when a certain number of changes have occured.

Documentation
=============

Most of the documentation for this project is available at
https://wmtprojectsforum.altervista.org/files/, along with
the Design and Requirements documents. Old versions of the
code from before this repository was opened can be found
there as well. Some of the older files can also be found at
http://www.hadrian-way.co.uk/WMT_River_System_Development/.

API Documentation
-----------------

The API documentation for the software is also included
in this repository, and is generated from docstrings in the
source code, using Sphinx.

Generating the documentation
----------------------------

To generate the documentation, you need to ensure you have
sphinx installed with either:

    pip3 install sphinx

or:

Install a distribution package for sphinx, like:

    sudo apt install python3-sphinx

on Ubuntu and derivatives.

Note that the directory containing the source code **must**
be called "rivercontrolsystem" for this to work.

Then, using a terminal, change directory into the
"docs" directory, then run:

    make

to list all the output formats.

Once you've picked a format eg html, run:

    make html

And then find your documentation under docs/build.

Unit Tests
==========

A number of unit tests have been written for this software. To run them,
change into the source directory and run:

    python3 ./unittets.py

There are a number of test suites that can be specified (use the -h flag for more details).
For each one of these, the output format is as follows:

    ---------------------------- Tests for (suite name) from (file name) ----------------------------
    
    test_1 (name_of_test) ... (result)
    ...
    
    ----------------------------------------------------------------------
    Ran x tests in (time)
    
    (overall result)

As a result of this, it's worth either running the suites independently, or carefully checking through the output.


Determining Test Coverage
-------------------------

There is a simple way to determine coverage for these unit tests. To do this, first make sure coverage is available by running:

    pip3 install coverage

or install a distribution package like:

    sudo apt install python3-coverage

on Ubuntu and derivatives.

After that, run the tests with:

    python3 -m coverage run ./unittests.py

And then run:

    python3 -m coverage html

To generate the report. To view the report, run:

    xdg-open ./htmlcov/index.html

Coverage isn't at 100% as of the time of writing, but it will continue to improve as the software is developed. The total coverage is around 80% at the time of writing (17/07/2020).
