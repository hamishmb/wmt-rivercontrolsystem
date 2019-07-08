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
from . import deviceobjects_test_data as data

#Set up device_objects to use dummy GPIO.
device_objects.GPIO = data.GPIO

class TestBaseDeviceClass(unittest.TestCase):
    """This test class tests the features of the BaseDeviceClass class in Tools/deviceobjects.py"""

    def setUp(self):
        self.basedevice = device_objects.BaseDeviceClass("SUMP:M0", "Test")

    def tearDown(self):
        del self.basedevice

    #---------- CONSTRUCTOR TESTS ----------
    def test_constructor_1(self):
        """Test that the constructor works when _id is valid, and name is not specified."""
        for dataset in data.TEST_BASEDEVICECLASS_NONAME_DATA:
            _id = dataset[0]

            basedevice = device_objects.BaseDeviceClass(_id)

            self.assertEqual(basedevice.get_id(), _id)
            self.assertEqual(basedevice.get_name(), "<unspecified>")

    def test_constructor_2(self):
        """Test that the constructor works when _id is valid, and name is valid and specified."""
        for dataset in data.TEST_BASEDEVICECLASS_DATA:
            _id = dataset[0]
            _name = dataset[1]

            basedevice = device_objects.BaseDeviceClass(_id, _name)

            self.assertEqual(basedevice.get_id(), _id)
            self.assertEqual(basedevice.get_name(), _name)

    def test_constructor_3(self):
        """Test that the constructor fails when _id and _name are invalid."""
        for dataset in data.TEST_BASEDEVICECLASS_BAD_DATA:
            _id = dataset[0]
            _name = dataset[1]

            try:
                basedevice = device_objects.BaseDeviceClass(_id, _name)

            except ValueError:
                #This is required for the test to pass.
                pass

            else:
                #All of these should throw errors!
                self.assertTrue(False, "ValueError was expected for data: "+str(dataset))

    #---------- GETTER TESTS ----------
    def test_get_device_id_1(self):
        """Test that get_device_id() works as expected."""
        self.assertEqual(self.basedevice.get_device_id(), "M0")

    def test_get_system_id_1(self):
        """Test that get_system_id() works as expected."""
        self.assertEqual(self.basedevice.get_system_id(), "SUMP")

    def test_get_id_1(self):
        """Test that get_id() works as expected."""
        self.assertEqual(self.basedevice.get_id(), "SUMP:M0")

    def test_get_name_1(self):
        """Test that get_name() works as expected."""
        self.assertEqual(self.basedevice.get_name(), "Test")

    #---------- SETTER TESTS ----------
    def test_set_pins_1(self):
        """Test that set_pins() works when only one pin is specified, and it is valid."""
        for pin in data.TEST_BASEDEVICECLASS_GETPINS_DATA:
            self.basedevice.set_pins(pin)

            self.assertEqual(self.basedevice._pins, [pin])
            self.assertEqual(self.basedevice._reverse_pins, [pin])
            self.assertEqual(self.basedevice._pin, pin)

    def test_set_pins_2(self):
        """Test that set_pins() works when multiple valid pins are specified."""
        pins = data.TEST_BASEDEVICECLASS_GETPINS_DATA

        self.basedevice.set_pins(pins)

        self.assertEqual(self.basedevice._pins, pins)
        self.assertEqual(self.basedevice._reverse_pins, pins[::-1])
        self.assertEqual(self.basedevice._pin, -1)

    def test_set_pins_3(self):
        """Test that set_pins() fails when only one pin is specified, and it is invalid."""
        for pin in data.TEST_BASEDEVICECLASS_GETPINS_BAD_DATA:
            try:
                self.basedevice.set_pins(pin)

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError was expected for pin: "+str(pin))

    def test_set_pins_4(self):
        """Test that set_pins() fails when multiple invalid pins are specified"""
        pins = data.TEST_BASEDEVICECLASS_GETPINS_BAD_DATA

        try:
            self.basedevice.set_pins(pins)

        except ValueError:
            #Expected.
            pass

        else:
            #This should have failed!
            self.assertTrue(False, "ValueError was expected for: "+str(pin))

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
