#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Device Objects Unit Tests for the River System Control and Monitoring Software
# Copyright (C) 2017-2022 Wimborne Model Town
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
import os

#Import other modules.
sys.path.insert(0, os.path.abspath('../../../')) #Need to be able to import the Tools module from here.

import Tools
from Tools import deviceobjects

#Import test data and functions.
from . import deviceobjects_test_data as data

#Set up deviceobjects to use dummy GPIO.
deviceobjects.GPIO = data.GPIO

#Prevent any management threads from being started - use dummy ones instead.
deviceobjects.device_mgmt = data

class TestBaseDeviceClass(unittest.TestCase):
    """This test class tests the features of the BaseDeviceClass class in Tools/deviceobjects.py"""

    def setUp(self):
        self.basedevice = deviceobjects.BaseDeviceClass("SUMP:M0", "Test")

    def tearDown(self):
        del self.basedevice

    #---------- CONSTRUCTOR TESTS ----------
    def test_constructor_1(self):
        """Test that the constructor works when _id is valid, and name is not specified."""
        for dataset in data.TEST_BASEDEVICECLASS_NONAME_DATA:
            _id = dataset[0]

            basedevice = deviceobjects.BaseDeviceClass(_id)

            self.assertEqual(basedevice.get_id(), _id)
            self.assertEqual(basedevice.get_name(), "<unspecified>")

    def test_constructor_2(self):
        """Test that the constructor works when _id is valid, and name is valid and specified."""
        for dataset in data.TEST_BASEDEVICECLASS_DATA:
            _id = dataset[0]
            _name = dataset[1]

            basedevice = deviceobjects.BaseDeviceClass(_id, _name)

            self.assertEqual(basedevice.get_id(), _id)
            self.assertEqual(basedevice.get_name(), _name)

    def test_constructor_3(self):
        """Test that the constructor fails when _id and _name are invalid."""
        for dataset in data.TEST_BASEDEVICECLASS_BAD_DATA:
            _id = dataset[0]
            _name = dataset[1]

            try:
                basedevice = deviceobjects.BaseDeviceClass(_id, _name)

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

    def test_get_site_id_1(self):
        """Test that get_site_id() works as expected."""
        self.assertEqual(self.basedevice.get_site_id(), "SUMP")

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
            self.assertTrue(False, "ValueError was expected for: "+str(pins))

class TestMotor(unittest.TestCase):
    """
    This test class tests the features of the Motor class in
    Tools/deviceobjects.py
    """

    def setUp(self):
        self.motor = deviceobjects.Motor("SUMP:P0", "Test")

    def tearDown(self):
        del self.motor

    #---------- CONSTRUCTOR TESTS ----------
    #Note: All arguments are validated in BaseDeviceClass, so no complex tests here.
    def test_constructor_1(self):
        """Test the constructor works as expected."""
        motor = deviceobjects.Motor("SUMP:P1", "Test Motor")

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
        self.floatswitch = deviceobjects.FloatSwitch("G4:FS0", "Test")

    def tearDown(self):
        del self.floatswitch

    #---------- CONSTRUCTOR TESTS ----------
    #Note: All arguments are validated in BaseDeviceClass, so no complex tests here.
    def test_constructor_1(self):
        """Test the constructor works as expected"""
        floatswitch = deviceobjects.FloatSwitch("G6:FS1", "Testing")

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
        self.halleffectdevice = deviceobjects.HallEffectDevice("SUMP:W0", "Water Wheel")

    def tearDown(self):
        del self.halleffectdevice

    #---------- CONSTRUCTOR TESTS ----------
    #Note: All arguments are validated in BaseDeviceClass, so no complex tests here.
    def test_constructor_1(self):
        """Test that the constructor works as expected"""
        halleffectdevice = deviceobjects.HallEffectDevice("G6:W1", "Test")

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
        self.halleffectprobe = deviceobjects.HallEffectProbe("G4:M1", "Testing")

    def tearDown(self):
        del self.halleffectprobe

    #---------- CONSTRUCTOR TESTS ----------
    #Note: All arguments are validated in BaseDeviceClass, so no complex tests here.
    def test_constructor_1(self):
        """Test the constructor works properly"""
        halleffectprobe = deviceobjects.HallEffectProbe("SUMP:M0", "Test")

        self.assertEqual(halleffectprobe._current_reading, 0)
        self.assertEqual(halleffectprobe.high_limits, None)
        self.assertEqual(halleffectprobe.low_limits, None)
        self.assertEqual(halleffectprobe.depths, None)
        self.assertEqual(halleffectprobe.length, None)

    #---------- GETTER TESTS ----------
    def test_get_limits_1(self):
        """Test the get_limits() method works as expected"""
        self.assertEqual(self.halleffectprobe.get_limits(), (None, None))

        self.halleffectprobe.high_limits = (1, 2, 3, 4)
        self.halleffectprobe.low_limits = (-3, -2, -1, 0)

        self.assertEqual(self.halleffectprobe.get_limits(),
                         ((1, 2, 3, 4), (-3, -2, -1, 0)))

    def test_get_depths_1(self):
        """Test the get_depths() method works as expected"""
        self.assertEqual(self.halleffectprobe.get_depths(), None)

        self.halleffectprobe.depths = ((25), (50), (75), (100))

        self.assertEqual(self.halleffectprobe.get_depths(), ((25), (50), (75), (100)))

    def test_get_reading(self):
        """Test that get_reading() works as expected"""
        for num in range(0, 1000):
            self.halleffectprobe._current_reading = num

            self.assertEqual(self.halleffectprobe.get_reading(), (num, "OK"))

    #---------- SETTER TESTS ----------
    def test_set_limits_1(self):
        """Test the set_limits() method works when given valid data"""
        for dataset in data.TEST_HALLEFFECTPROBE_SETLIMITS_DATA:
            high_limits = dataset[0]
            low_limits = dataset[1]

            self.halleffectprobe.set_limits(high_limits, low_limits)

            self.assertEqual(self.halleffectprobe.get_limits(), (high_limits, low_limits))

    def test_set_limits_2(self):
        """Test the set_limits() method fails when given invalid data"""
        for dataset in data.TEST_HALLEFFECTPROBE_SETLIMITS_BAD_DATA:
            high_limits = dataset[0]
            low_limits = dataset[1]

            try:
                self.halleffectprobe.set_limits(high_limits, low_limits)

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError was expected for data: "+str(dataset))

    def test_set_depths_1(self):
        """Test that the set_depths() method works when given valid data"""
        for dataset in data.TEST_HALLEFFECTPROBE_SETDEPTHS_DATA:
            hundreds = dataset[0]
            twentyfives = dataset[1]
            fifties = dataset[2]
            seventies = dataset[3]

            self.halleffectprobe.set_depths((hundreds, twentyfives, fifties, seventies))

            self.assertEqual(self.halleffectprobe.get_depths(),
                             (hundreds, twentyfives, fifties, seventies))

            self.assertEqual(self.halleffectprobe.length, len(hundreds))

    def test_set_depths_2(self):
        """Test that the set_depths() method fails when given invalid data"""
        for dataset in data.TEST_HALLEFFECTPROBE_SETDEPTHS_BAD_DATA:
            hundreds = dataset[0]
            twentyfives = dataset[1]
            fifties = dataset[2]
            seventies = dataset[3]

            try:
                self.halleffectprobe.set_depths((hundreds, twentyfives, fifties, seventies))

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError was expected for data: "+str(dataset))

class TestGateValve(unittest.TestCase):
    """
    This test class tests the features of the GateValve class in
    Tools/deviceobjects.py
    """

    def setUp(self):
        #Don't specify the other arguments because they're only used in the
        #ManageGateValve class.
        self.gatevalve = deviceobjects.GateValve("VALVE4:V4", "Test")

        self.gatevalve.set_pins((2, 3, 4))
        self.gatevalve.set_pos_tolerance(5)
        self.gatevalve.set_max_open(99)
        self.gatevalve.set_min_open(1)
        self.gatevalve.set_ref_voltage(3.3)
        self.gatevalve.set_i2c_address(0x48)

    def tearDown(self):
        del self.gatevalve

    #---------- CONSTRUCTOR TESTS ----------
    #Note: All arguments (used in this class) are validated in BaseDeviceClass,
    #so no tests for those here. Other arguments specifically for this class
    #are tested here, though.

    def test_constructor_1(self):
        """Test that the constructor works when given valid arguments"""
        for dataset in data.TEST_GATEVALVE_DATA:
            _id = dataset[0]
            _name = dataset[1]
            pins = dataset[2]
            pos_tolerance = dataset[3]
            max_open = dataset[4]
            min_open = dataset[5]
            ref_voltage = dataset[6]

            gatevalve = deviceobjects.GateValve(_id, _name)
            gatevalve.set_pins(pins)
            gatevalve.set_pos_tolerance(pos_tolerance)
            gatevalve.set_max_open(max_open)
            gatevalve.set_min_open(min_open)
            gatevalve.set_ref_voltage(ref_voltage)

            self.assertEqual(gatevalve.forward_pin, pins[0])
            self.assertEqual(gatevalve.reverse_pin, pins[1])
            self.assertEqual(gatevalve.clutch_pin, pins[2])
            self.assertEqual(gatevalve.pos_tolerance, pos_tolerance)
            self.assertEqual(gatevalve.max_open, max_open)
            self.assertEqual(gatevalve.min_open, min_open)
            self.assertEqual(gatevalve.ref_voltage, ref_voltage)

    def test_constructor_2(self):
        """Test that the constructor fails when given invalid arguments"""
        for dataset in data.TEST_GATEVALVE_BAD_DATA:
            _id = dataset[0]
            _name = dataset[1]
            pins = dataset[2]
            pos_tolerance = dataset[3]
            max_open = dataset[4]
            min_open = dataset[5]
            ref_voltage = dataset[6]

            try:
                gatevalve = deviceobjects.GateValve(_id, _name)
                gatevalve.set_pins(pins)
                gatevalve.set_pos_tolerance(pos_tolerance)
                gatevalve.set_max_open(max_open)
                gatevalve.set_min_open(min_open)
                gatevalve.set_ref_voltage(ref_voltage)

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError was expected for data: "+str(dataset))

    #---------- GETTER TESTS ----------
    def test_get_pos_tolerance(self):
        """Test that the get_pos_tolerance() method works as expected"""
        self.assertEqual(self.gatevalve.get_pos_tolerance(), 5)

    def test_get_max_open(self):
        """Test that the get_max_open() method works as expected"""
        self.assertEqual(self.gatevalve.get_max_open(), 99)

    def test_get_min_open(self):
        """Test that the get_min_open() method works as expected"""
        self.assertEqual(self.gatevalve.get_min_open(), 1)

    def test_get_ref_voltage(self):
        """Test that the get_ref_voltage() method works as expected"""
        self.assertEqual(self.gatevalve.get_ref_voltage(), 3.3)

    def test_get_reading_1(self):
        """Test that the get_reading() method works as expected"""
        #Start our fake thread.
        self.gatevalve.start_thread()

        for position in range(0, 100):
            self.gatevalve.mgmt_thread.position = position
            self.assertEqual(self.gatevalve.get_reading(), (position, "OK"))

    #---------- SETTER TESTS ----------
    def test_set_position_1(self):
        """Test that the set_position() method works as expected"""
        #Start our fake thread.
        self.gatevalve.start_thread()

        for position in range(0, 100):
            self.gatevalve.set_position(position)
            self.assertEqual(self.gatevalve.mgmt_thread.position, position)

    def test_set_position_2(self):
        """Test that the set_position() method fails with negative values"""
        #Start our fake thread.
        self.gatevalve.start_thread()

        for i in range(-100, 0):
            self.gatevalve.set_position(i)
            self.assertEqual(self.gatevalve.mgmt_thread.position, 0)

    def test_set_position_3(self):
        """Test that the set_position() method fails with values greater than 100"""
        #Start our fake thread.
        self.gatevalve.start_thread()

        for i in range(101, 500):
            self.gatevalve.set_position(i)
            self.assertEqual(self.gatevalve.mgmt_thread.position, 100)

    def test_set_position_4(self):
        """Test that the set_position() method fails with values of the wrong type"""
        #Start our fake thread.
        self.gatevalve.start_thread()

        for i in (0.0, False, None, (), [], {}, "test"):
            try:
                self.gatevalve.set_position(i)

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError expected for: "+str(i))
