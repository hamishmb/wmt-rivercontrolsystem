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
http://www.hadrian-way.co.uk/WMT_River_System_Development/,
along with the Design and Requirements documents. Old
versions of the code from before this repository was opened
can be found there as well.

API Documentation
=================

The API documentation for the software is also included
in this repository, and is generated from docstrings in the
source code, using Sphinx.

Generating the documentation
============================

To generate the documentation, you need to ensure you have
sphinx installed with either:

"pip install sphinx"

or:

Install a distribution package for sphinx, like:

"sudo apt install python3-sphinx"

on Ubuntu and derivatives.

Note that the directory containing the source code **must**
be called "rivercontrolsystem" for this to work.

Then, using a terminal, change directory into the
"docs" directory, then run:

"make"

to list all the output formats.

Once you've picked a format eg html, run:

"make <format>"

And then find your documentation under docs/build.
