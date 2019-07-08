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
        self.motor = device_objects.Motor("SUMP:P0", "Test")

    def tearDown(self):
        del self.motor

    #---------- CONSTRUCTOR TESTS ----------
    #Note: All arguments are validated in BaseDeviceClass, so no complex tests here.
    def test_constructor_1(self):
        """Test the constructor works as expected."""
        motor = device_objects.Motor("SUMP:P1", "Test Motor")

        self.assertFalse(motor._state)
        self.assertFalse(motor._supports_pwm)
        self.assertEqual(motor._pwm_pin, -1)

    #---------- GETTER TESTS ----------
    def get_reading_1(self):
        """Test that get_reading() works as expected"""
        #NOTE: Currently no fault checking to test.
        self.assertEqual(self.motor.get_reading(), (False, "OK"))

        self.motor._state = True

        self.assertEqual(self.motor.get_reading(), (True, "OK"))

    def test_pwm_supported_1(self):
        """Test that pwm_supported() works as expected"""
        self.assertFalse(self.motor._supports_pwm)

        self.motor._supports_pwm = True

        self.assertTrue(self.motor._supports_pwm)

    #---------- SETTER TESTS ----------
    def test_set_pwm_available_1(self):
        """Test that set_pwm_available() works as expected with valid arguments."""
        for dataset in data.TEST_MOTOR_SETPWMAVAILABLE_DATA:
            pwm_available = dataset[0]
            pwm_pin = dataset[1]

            if pwm_pin is not None:
                self.motor.set_pwm_available(pwm_available, pwm_pin)

            else:
                self.motor.set_pwm_available(pwm_available)

                #Reset pwm_pin to -1 - default if unspecified.
                pwm_pin = -1

            self.assertEqual(pwm_available, self.motor._supports_pwm)
            self.assertEqual(pwm_pin, self.motor._pwm_pin)

    def test_set_pwm_available_2(self):
        """Test that set_pwm_available() fails with invalid arguments."""
        for dataset in data.TEST_MOTOR_SETPWMAVAILABLE_BAD_DATA:
            pwm_available = dataset[0]
            pwm_pin = dataset[1]

            try:
                if pwm_pin is not None:
                    self.motor.set_pwm_available(pwm_available, pwm_pin)

                else:
                    self.motor.set_pwm_available(pwm_available)

                    #Reset pwm_pin to -1 - default if unspecified.
                    pwm_pin = -1

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError was expected for data: "+str(dataset))

    #---------- CONTROL TESTS ----------
    def test_enable_1(self):
        """Test that enabling the motor works when the control pin is set"""
        self.motor.set_pins(7, _input=False)

        retval = self.motor.enable()

        self.assertTrue(retval)
        self.assertTrue(self.motor.get_reading()[0])

    @unittest.expectedFailure
    def test_enable_2(self):
        """Test that enabling the motor fails when the control pin isn't set"""
        retval = self.motor.enable()

    def test_disable_1(self):
        """Test that disabling the motor works when the control pin is set"""
        self.motor.set_pins(7, _input=False)

        retval = self.motor.disable()

        self.assertTrue(retval)
        self.assertFalse(self.motor.get_reading()[0])

    @unittest.expectedFailure
    def test_disable_2(self):
        """Test that enabling the motor fails when the control pin isn't set"""
        retval = self.motor.disable()

class TestFloatSwitch(unittest.TestCase):
    """
    This test class tests the features of the FloatSwitch class in
    Tools/deviceobjects.py
    """

    def setUp(self):
        self.floatswitch = device_objects.FloatSwitch("G4:FS0", "Test")

    def tearDown(self):
        del self.floatswitch

    #---------- CONSTRUCTOR TESTS ----------
    #Note: All arguments are validated in BaseDeviceClass, so no complex tests here.
    def test_constructor_1(self):
        """Test the constructor works as expected"""
        floatswitch = device_objects.FloatSwitch("G6:FS1", "Testing")

        self.assertTrue(self.floatswitch._active_state)

    #---------- GETTER TESTS ----------
    def test_get_active_state_1(self):
        """Test that get_active_state() works as expected"""
        self.assertTrue(self.floatswitch.get_active_state())

        self.floatswitch.set_active_state(False)

        self.assertFalse(self.floatswitch.get_active_state())

    def test_get_reading_1(self):
        """Test that get_reading() works as expected"""
        #The fake GPIO.input() function alternates the return value each time - we can predict what it should be.
        #By default the active state is True - active high.
        self.assertEqual(self.floatswitch.get_reading(), (False, "OK"))
        self.assertEqual(self.floatswitch.get_reading(), (True, "OK"))

        #Now we will change the active state to False - active low.
        self.floatswitch._active_state = False

        self.assertEqual(self.floatswitch.get_reading(), (True, "OK"))
        self.assertEqual(self.floatswitch.get_reading(), (False, "OK"))

    #---------- SETTER TESTS ----------
    def test_set_active_state_1(self):
        """Test that set_active_state() works when given a valid state"""
        for state in (False, True):
            self.floatswitch.set_active_state(state)
            self.assertEqual(self.floatswitch._active_state, state)

    def test_set_active_state_2(self):
        """Test that set_active_state() fails with invalid states"""
        for state in (0, -1, 7.6, [], {}):
            try:
                self.floatswitch.set_active_state(state)

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError expected for data: "+str(state))

class TestHallEffectDevice(unittest.TestCase):
    """
    This test class tests the features of the HallEffectDevice (water wheel) class in
    Tools/deviceobjects.py
    """

    def setUp(self):
        self.halleffectdevice = device_objects.HallEffectDevice("SUMP:W0", "Water Wheel")

    def tearDown(self):
        del self.halleffectdevice

    #---------- CONSTRUCTOR TESTS ----------
    #Note: All arguments are validated in BaseDeviceClass, so no complex tests here.
    def test_constructor_1(self):
        """Test that the constructor works as expected"""
        halleffectdevice = device_objects.HallEffectDevice("G6:W1", "Test")

        self.assertEqual(halleffectdevice._num_detections, 0)

    #------------ PRIVATE METHOD TESTS ----------
    def test_increment_num_detections(self):
        """Test that _increment_num_detections() works as expected"""
        self.assertEqual(self.halleffectdevice._num_detections, 0)

        for i in range(0, 500):
            self.halleffectdevice._increment_num_detections("test")

        self.assertEqual(self.halleffectdevice._num_detections, 500)

    #---------- GETTER TESTS ----------
    def test_get_reading(self):
        """Test that get_reading() works as expected (slow test)"""
        #NOTE: We have a custom fake GPIO.add_event_detect() method just for this purpose.
        #NOTE: We can set data.GPIO.num_events to change how many times it calls back the function.
        for num in (1, 5, 10, 50, 7000):
            data.GPIO.num_events = num

            reading = self.halleffectdevice.get_reading()

            self.assertEqual(reading, (num*12, "OK"))

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
