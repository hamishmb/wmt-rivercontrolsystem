#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Core Tools Unit Tests for the River System Control and Monitoring Software
# Copyright (C) 2017-2019 Wimborne Model Town
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3 or,
# at your option, any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=too-few-public-methods
#
# Reason (too-few-public-methods): Test classes don't need many public members.

#Import modules
import unittest
import sys

#Import other modules.
sys.path.append('../..') #Need to be able to import the Tools module from here.

import Tools
import Tools.coretools as core_tools

#Import test data and functions.
#TODO if needed.

class TestReading(unittest.TestCase):
    """This test class tests the features of the Reading class in Tools/coretools.py"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass

#TODO First move this class to another file in Tools/
class TestActuatorPosition(unittest.TestCase):
    """
    This test class tests the features of the ActuatorPosition class in
    Tools/coretools.py
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass

class TestControlLogic(unittest.TestCase):
    """
    This test class tests the control logic functions in
    Tools/coretools.py
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass

class TestMiscFunctions(unittest.TestCase):
    """
    This test class tests the miscellaneous functions in
    Tools/coretools.py
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass
