#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Device Objects Unit Tests for the River System Control and Monitoring Software
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
import Tools.deviceobjects as device_objects

#Import test data and functions.
#TODO if needed.

class TestBaseDeviceClass(unittest.TestCase):
    """This test class tests the features of the BaseDeviceClass class in Tools/deviceobjects.py"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass

class TestMotor(unittest.TestCase):
    """
    This test class tests the features of the Motor class in
    Tools/deviceobjects.py
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass

class TestFloatSwitch(unittest.TestCase):
    """
    This test class tests the features of the FloatSwitch class in
    Tools/deviceobjects.py
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass

class TestHallEffectDevice(unittest.TestCase):
    """
    This test class tests the features of the HallEffectDevice (water wheel) class in
    Tools/deviceobjects.py
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass

#TODO First split this class into a probe class and a control class,
#like with GateValve and ActuatorPosition.
class TestHallEffectProbe(unittest.TestCase):
    """
    This test class tests the features of the HallEffectProbe class in
    Tools/deviceobjects.py
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass

class TestGateValve(unittest.TestCase):
    """
    This test class tests the features of the GateValve class in
    Tools/deviceobjects.py
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass
