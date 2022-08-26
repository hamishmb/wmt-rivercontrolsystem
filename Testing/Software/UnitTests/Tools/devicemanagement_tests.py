#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Device Management Unit Tests for the River System Control and Monitoring Software
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
import Tools.deviceobjects as device_objects
import Tools.devicemanagement as device_mgmt

#Import test data and functions.
from . import devicemanagement_test_data as data

#Disable automatically starting the thread in the ManageHallEffectProbe class, so we can test it.

#Set up device_objects to use dummy GPIO, ADS, and AnalogIn classes.
device_mgmt.GPIO = data.GPIO
device_mgmt.ads = None
device_mgmt.ADS = data.ADS
device_mgmt.AnalogIn = data.AnalogIn

#Prevent any management threads from being started - disable self.start by replacing
#it with a do-nothing function.
device_mgmt.ManageHallEffectProbe.start = data.start
device_mgmt.ManageGateValve.start = data.start

class TestManageHallEffectProbe(unittest.TestCase):
    """This class tests the features of the ManageHallEffectProbe class in Tools/devicemanagement.py"""

    def setUp(self):
        self.probe = device_objects.HallEffectProbe("G4:M0", "Test")
        self.mgmtclass = device_mgmt.ManageHallEffectProbe(self.probe, 0x48)

    def tearDown(self):
        del self.mgmtclass
        del self.probe

    #---------- CONSTRUCTOR TESTS ----------
    #Note: No fancy test here because there's only one argument - the probe object.

    def test_constructor_1(self):
        """Test the constructor works as expected"""
        probe = device_objects.HallEffectProbe("G4:M0", "Test")
        mgmtclass = device_mgmt.ManageHallEffectProbe(probe, 0x48)

        self.assertEqual(mgmtclass.probe, probe)

        #Test that channels are being set correctly.
        self.assertEqual(mgmtclass.chan0.__class__, data.ADS)
        self.assertEqual(mgmtclass.chan1.__class__, data.ADS)
        self.assertEqual(mgmtclass.chan2.__class__, data.ADS)
        self.assertEqual(mgmtclass.chan3.__class__, data.ADS)

    #---------- OTHER METHOD TESTS ----------
    def test_get_compensated_probe_voltages_1(self):
        """Test that the get_compensated_probe_voltages() method works as expected"""
        for dataset in data.TEST_MANAGEHALLEFFECTPROBE_COMP_VOLTAGES:
            index = data.TEST_MANAGEHALLEFFECTPROBE_COMP_VOLTAGES.index(dataset)

            self.mgmtclass.chan0.voltage = dataset[0]
            self.mgmtclass.chan1.voltage = dataset[1]
            self.mgmtclass.chan2.voltage = dataset[2]
            self.mgmtclass.chan3.voltage = dataset[3]

            results = self.mgmtclass.get_compensated_probe_voltages()

            self.assertEqual(results, data.TEST_MANAGEHALLEFFECTPROBE_COMP_VOLTAGES_RESULTS[index])

    def test_get_level_1(self):
        """Test that the get_level() function works as expected"""
        self.probe.set_limits(data.HIGH_LIMITS, data.LOW_LIMITS)
        self.probe.set_depths(data.DEPTHS)

        #Replace this with our fake method so we can inject values to test.
        self.mgmtclass.get_compensated_probe_voltages = data.get_compensated_probe_voltages

        try:
            while True:
                level = self.mgmtclass.get_level()
                self.assertEqual(level, data.get_level_result())
                data.voltages_position += 1

        except RuntimeError:
            #Happens when there are no more results to test.
            pass

class TestManageGateValve(unittest.TestCase):
    """This class tests the features of the ManageGateValve class in Tools/devicemanagement.py"""

    def setUp(self):
        self.valve = device_objects.GateValve("VALVE4:V4", "Test")

        self.valve.set_pins((2, 3, 4))
        self.valve.set_pos_tolerance(5)
        self.valve.set_max_open(99)
        self.valve.set_min_open(1)
        self.valve.set_ref_voltage(3.3)
        self.valve.set_i2c_address(0x48)

        self.mgmtclass = device_mgmt.ManageGateValve(self.valve, 0x48)

    def tearDown(self):
        del self.mgmtclass
        del self.valve

    #---------- CONSTRUCTOR TESTS ----------
    #Note: No fancy test here because there's only one argument - the probe object.

    def test_constructor_1(self):
        """Test that the constructor works as expected"""
        valve = device_objects.GateValve("VALVE4:V4", "Test")

        valve.set_pins((2, 3, 4))
        valve.set_pos_tolerance(5)
        valve.set_max_open(99)
        valve.set_min_open(1)
        valve.set_ref_voltage(3.3)
        valve.set_i2c_address(0x48)

        mgmtclass = device_mgmt.ManageGateValve(valve, 0x48)

        #Check that variables were set correctly by the constructor.
        self.assertEqual(mgmtclass.percentage, 0)

        #NOTE: The other three variables are changed immediately and are not trivial to determine.

    #---------- GETTER TESTS ----------
    def test__get_position_1(self):
        """Test that the _get_position() method works as expected when there is no error reading the voltage"""
        return
        for voltage in range(0, 331, 1):
            #We have to use ints with range, but we want a gradual increase to
            #3.3v so, we'll divide these values by 100.
            voltage /= 100

            data.ADS.voltage = voltage

            position = self.mgmtclass._get_position()

            self.assertEqual(position, int(voltage/3.3*100))

    def test__get_position_2(self):
        """Test that the _get_position() method works as expected when there is an error reading the voltage"""
        return
        #Use the special ADS class that always throws an OSError when voltage is
        #accessed.
        device_mgmt.AnalogIn = data.AnalogIn2

        position = self.mgmtclass._get_position()

        #Revert the change.
        device_mgmt.AnalogIn = data.AnalogIn

        self.assertEqual(position, -1)

    #---------- SETTER TESTS ----------
    def test_set_position_1(self):
        """Test that the set_position() method works as expected with sane values"""
        for i in range(0, 101):
            self.mgmtclass.set_position(i)
            self.assertEqual(self.mgmtclass.percentage, i)

    def test_set_position_2(self):
        """Test that the set_position() method fails with negative values"""
        for i in range(-100, 0):
            try:
                self.mgmtclass.set_position(i)

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError expected for: "+str(i))

    def test_set_position_3(self):
        """Test that the set_position() method fails with values greater than 100"""
        for i in range(101, 500):
            try:
                self.mgmtclass.set_position(i)

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError expected for: "+str(i))

    def test_set_position_4(self):
        """Test that the set_position() method fails with values of the wrong type"""
        for i in (0.0, False, None, (), [], {}, "test"):
            try:
                self.mgmtclass.set_position(i)

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError expected for: "+str(i))

    #---------- CALCULATION METHOD TESTS ----------
    def test_calculate_limits(self):
        """Test that the calculate_limits() method works as expected"""
        #Test with all the different desired positions.
        #We have to go backwards here to make sure the limits are set -
        #they aren't changed if movement isn't required.
        for position in range(100, 0, -1):
            self.mgmtclass.set_position(position)

            #We'll test this with all the different actual positions, the same way as before.
            for voltage in range(0, 331, 1):
                #We have to use ints with range, but we want a gradual increase to 3.3v, so
                #we'll divide these values by 100.
                voltage /= 100

                data.ADS.voltage = voltage

                self.mgmtclass._get_position()
                self.mgmtclass.calculate_limits()

                #This is a slightly simplified version of what is in the calculate_limits() method,
                #because it's not super-easy to break it down into anything simpler to test with.
                if ((position + self.valve.pos_tolerance) > (self.valve.max_open - self.valve.pos_tolerance)):
                    high_limit = self.valve.max_open
                    low_limit = self.valve.max_open - 6

                elif (position - self.valve.pos_tolerance < self.valve.min_open):
                    low_limit = self.valve.min_open
                    high_limit = self.valve.min_open + 2

                else:
                    #Set the High Limit to the required percentage
                    high_limit = position + self.valve.pos_tolerance

                    #Set the Low Limit to the required percentage
                    low_limit = position - self.valve.pos_tolerance

                self.assertEqual(self.mgmtclass.low_limit, low_limit)
                self.assertEqual(self.mgmtclass.high_limit, high_limit)

    #---------- CONTROL METHOD TESTS ----------
    #We just check that these two run without error - they are very simple.
    def test_clutch_engage(self):
        """Test that the clutch_engage() method works as expected"""
        self.mgmtclass.clutch_engage()

    def test_clutch_disengage(self):
        """Test that the clutch_disengage() method works as expected"""
        self.mgmtclass.clutch_disengage()
