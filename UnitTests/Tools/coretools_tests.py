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
import datetime

#Import other modules.
sys.path.append('../..') #Need to be able to import the Tools module from here.

import Tools
import Tools.coretools as core_tools

#Import test data and functions.
from . import coretools_test_data as data

class TestReading(unittest.TestCase):
    """This test class tests the features of the Reading class in Tools/coretools.py"""

    def setUp(self):
        self.time = str(datetime.datetime.now())
        self.reading = core_tools.Reading(self.time, 1, "SUMP:M0", "100", "OK")
        self.reading_2 = core_tools.Reading(self.time, 6, "SUMP:M1", "200", "OK")
        self.reading_3 = core_tools.Reading(self.time, 6, "SUMP:M0", "100", "OK")

    def tearDown(self):
        del self.time
        del self.reading
        del self.reading_2
        del self.reading_3

    #---------- CONSTRUCTOR TESTS ----------
    def test_constructor_1(self):
        """Test that the constructor works correctly when passed valid arguments"""
        for dataset in data.TEST_READING_DATA:
            time = dataset[0]
            tick = dataset[1]
            _id = dataset[2]
            value = dataset[3]
            status = dataset[4]

            new_reading = core_tools.Reading(time, tick, _id, value, status)

            self.assertEqual(new_reading.get_time(), time)
            self.assertEqual(new_reading.get_tick(), tick)
            self.assertEqual(new_reading.get_id(), _id)
            self.assertEqual(new_reading.get_group_id(), _id.split(":")[0])
            self.assertEqual(new_reading.get_sensor_id(), _id.split(":")[1])
            self.assertEqual(new_reading.get_value(), value)
            self.assertEqual(new_reading.get_status(), status)

    def test_constructor_2(self):
        """Test that errors are thrown when invalid arguments are passed."""
        for dataset in data.TEST_READING_BAD_DATA:
            time = dataset[0]
            tick = dataset[1]
            _id = dataset[2]
            value = dataset[3]
            status = dataset[4]

            try:
                new_reading = core_tools.Reading(time, tick, _id, value, status)

            except ValueError:
                #This is expected.
                pass

            else:
                #These should all throw errors!
                self.assertTrue(False, "ValueError was expected for data: "+str(dataset))

    #---------- GETTER TESTS ----------
    #NB: These are also used above in order to test the constructor is working correctly.
    def test_get_id(self):
        """Test that the get_id method works correctly"""
        self.assertEqual(self.reading.get_id(), "SUMP:M0")

    def test_get_group_id(self):
        """Test that the get_group_id method works correctly"""
        self.assertEqual(self.reading.get_group_id(), "SUMP")

    def test_get_sensor_id(self):
        """Test that the get_sensor_id method works correctly"""
        self.assertEqual(self.reading.get_sensor_id(), "M0")

    def test_get_tick(self):
        """Test that the get_tick method works correctly"""
        self.assertEqual(self.reading.get_tick(), 1)

    def test_get_value(self):
        """Test that the get_value method works correctly"""
        self.assertEqual(self.reading.get_value(), "100")

    def test_get_status(self):
        """Test that the get_status method works correctly"""
        self.assertEqual(self.reading.get_status(), "OK")

    #---------- EQUALITY AND COMPARISON TESTS ----------
    def test_equality(self):
        """Test that the equality method (__eq__) works correctly"""
        #TODO Test with different time as well.
        #These have different ID and value.
        self.assertNotEqual(self.reading, self.reading_2)

        #The tick is different for these two readings, but those are
        #ignored in the equality check.
        self.assertEqual(self.reading, self.reading_3)

        #These have different ID and value.
        self.assertNotEqual(self.reading_2, self.reading_3)

        #A reading is never equal to None.
        self.assertNotEqual(self.reading, None)

        #This should return False - incompatible class.
        self.assertNotEqual(self.reading, data.Dummy())

    def test_inequality(self):
        """Test that the inequality method (__ne__) works correctly"""
        #These have different ID and value.
        self.assertTrue(self.reading != self.reading_2)

        #The tick (and maybe time) is different for these two readings, but those are
        #ignored in the equality check.
        self.assertFalse(self.reading != self.reading_3)

        #These have different ID and value.
        self.assertTrue(self.reading_2 != self.reading_3)

        #A reading is never equal to None.
        self.assertTrue(self.reading != None)

        #This should return False - incompatible class.
        self.assertTrue(self.reading != data.Dummy())

    #---------- TEST OTHER CONVENIENCE METHODS ----------
    def test_to_string(self):
        """Test that the __str__ method works correctly."""
        self.assertEqual(self.reading.__str__(), "Reading at time "+self.time
                         + ", and tick 1"
                         + ", from probe: SUMP:M0"
                         + ", with value: 100"
                         + ", and status: OK")

        self.assertEqual(self.reading_2.__str__(), "Reading at time "+self.time
                         + ", and tick 6"
                         + ", from probe: SUMP:M1"
                         + ", with value: 200"
                         + ", and status: OK")

        self.assertEqual(self.reading_3.__str__(), "Reading at time "+self.time
                         + ", and tick 6"
                         + ", from probe: SUMP:M0"
                         + ", with value: 100"
                         + ", and status: OK")

    def test_as_csv(self):
        """Test that the as_csv method works correctly"""
        self.assertEqual(self.reading.as_csv(), self.time
                         + ",1,SUMP:M0,100,OK")

        self.assertEqual(self.reading_2.as_csv(), self.time
                         + ",6,SUMP:M1,200,OK")

        self.assertEqual(self.reading_3.as_csv(), self.time
                         + ",6,SUMP:M0,100,OK")

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

class TestSumpPiControlLogic(unittest.TestCase):
    """
    This test class tests the sumppi control logic function in
    Tools/coretools.py
    """

    def setUp(self):
        #Create fake sump pump and butts pump objects.
        self.devices = []

        self.butts_pump = data.Motor("SUMP:P0", "Sump to Butts Pump")
        self.butts_pump.set_pins(5, _input=False)
        self.devices.append(self.butts_pump)

        self.sump_pump = data.Motor("SUMP:P1", "Sump Circulation Pump")
        self.sump_pump.set_pins(18, _input=False)
        self.devices.append(self.sump_pump)

        #Create monitors 
        self.monitors = []

        self.test_monitor = data.Monitor()
        self.monitors.append(self.test_monitor)

        #Create sockets
        self.sockets = {}

        self.gate_valve_socket = data.Sockets()
        self.sockets["SOCK14"] = self.gate_valve_socket

        #Current reading interval.
        self.reading_interval = 15

    def tearDown(self):
        del self.devices
        del self.butts_pump
        del self.sump_pump
        del self.reading_interval

    #-------------------- NORMAL VALUES --------------------
    def test_sumppi_control_logic_1(self):
        """Test this works as expected when sump and butts are at 900mm, float switch floating"""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "800mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "True", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: 60.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), ["Valve Position 0", "Reading Interval: 60"])
        self.assertEqual(reading_interval, 60)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_2(self):
        """Test this works as expected when sump and butts are at 800mm, float switch pressed"""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "800mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: on.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: 30.

        self.assertTrue(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), ["Valve Position 0", "Reading Interval: 30"])
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_3(self):
        """Test this works as expected when sump and butts are at 700mm, float switch pressed"""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "700mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "700mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: on.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: 30.

        self.assertTrue(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), ["Valve Position 0", "Reading Interval: 30"])
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_5(self):
        """Test this works as expected when sump and butts are at 600mm, float switch pressed"""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "600mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "600mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: on.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: 30.

        self.assertTrue(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), ["Valve Position 0", "Reading Interval: 30"])
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_6(self):
        """Test this works as expected when sump and butts are at 500mm, float switch pressed"""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "500mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "500mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: <left as is>.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: <left as is>.

        #This is disabled by default, and it shouldn't have been changed.
        self.assertFalse(self.butts_pump.is_enabled())

        self.assertTrue(self.sump_pump.is_enabled())

        #The test sets the interval as 15 seconds. This should not have been changed.
        self.assertEqual(self.gate_valve_socket.get_queue(), ["Valve Position 0", "Reading Interval: 15"])
        self.assertEqual(reading_interval, 15)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_7(self):
        """Test this works as expected when sump and butts are at 500mm, butts pump on, float switch pressed"""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "500mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "500mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        #Turn the fake butts pump on.
        self.butts_pump.enable()

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: <left as is>.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: <left as is>.

        #This shouldn't have been changed.
        self.assertTrue(self.butts_pump.is_enabled())

        self.assertTrue(self.sump_pump.is_enabled())

        #The test sets the interval as 15 seconds. This should not have been changed.
        self.assertEqual(self.gate_valve_socket.get_queue(), ["Valve Position 0", "Reading Interval: 15"])
        self.assertEqual(reading_interval, 15)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_8(self):
        """Test this works as expected when sump and butts are at 400mm, float switch pressed"""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "400mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: 60.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), ["Valve Position 0", "Reading Interval: 60"])
        self.assertEqual(reading_interval, 60)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_9(self):
        """Test this works as expected when sump and butts are at 300mm, float switch pressed"""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "300mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "300mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: on.
        #Gate Valve Position: 25.
        #Reading Interval: 60.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), ["Valve Position 25", "Reading Interval: 60"])
        self.assertEqual(reading_interval, 60)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_10(self):
        """Test this works as expected when sump at 300mm, butts at 200mm, float switch pressed"""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "300mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "200mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: 60.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), ["Valve Position 0", "Reading Interval: 60"])
        self.assertEqual(reading_interval, 60)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_11(self):
        """Test this works as expected when sump at 200mm, butts at 600mm, float switch pressed"""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "200mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "600mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: off.
        #Gate Valve Position: 50.
        #Reading Interval: 30.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertFalse(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), ["Valve Position 50", "Reading Interval: 30"])
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_12(self):
        """Test this works as expected when sump and butts are at 200mm, float switch pressed"""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "200mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "200mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: off.
        #Gate Valve Position: 0.
        #Reading Interval: 30.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertFalse(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), ["Valve Position 0", "Reading Interval: 30"])
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_13(self):
        """Test this works as expected when sump and butts are at 100mm, float switch pressed"""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "100mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: off.
        #Gate Valve Position: 0.
        #Reading Interval: 15.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertFalse(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), ["Valve Position 0", "Reading Interval: 15"])
        self.assertEqual(reading_interval, 15)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_14(self):
        """Test this works as expected when sump at 100m, butts at 400mm, float switch pressed"""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: off.
        #Gate Valve Position: 100.
        #Reading Interval: 15.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertFalse(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), ["Valve Position 100", "Reading Interval: 15"])
        self.assertEqual(reading_interval, 15)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    #-------------------- ERRONEOUS VALUES --------------------
    @unittest.expectedFailure
    def test_sumppi_control_logic_bad_1(self):
        """Test this fails when the main circulation pump is not in the list of devices."""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        #Remove main circulation pump from device list.
        self.devices.pop(1)

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    @unittest.expectedFailure
    def test_sumppi_control_logic_bad_2(self):
        """Test this fails when the butts pump is not in the list of devices."""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        #Remove butts pump from device list.
        self.devices.pop(0)

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    @unittest.expectedFailure
    def test_sumppi_control_logic_bad_3(self):
        """Test this fails when there are no devices in the list."""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        #Clear the devices list.
        self.devices = []

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    @unittest.expectedFailure
    def test_sumppi_control_logic_bad_4(self):
        """Test this fails when there are no sockets in the list."""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        #Clear the sockets list.
        self.sockets = []

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    @unittest.expectedFailure
    def test_sumppi_control_logic_bad_5(self):
        """Test this fails when the reading interval is 0."""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           0)

    def test_sumppi_control_logic_bad_6(self):
        """Test this works when the readings for the sump and the butts are over 1000mm."""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "1100mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "4400mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    def test_sumppi_control_logic_bad_7(self):
        """Test this works when the readings for the sump and the butts are under 0mm."""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "-100mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "-400mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    #-------------------- EXCEPTIONAL VALUES --------------------
    @unittest.expectedFailure
    def test_sumppi_control_logic_exceptional_1(self):
        """Test this fails when the reading interval is negative."""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           -78)

    @unittest.expectedFailure
    def test_sumppi_control_logic_exceptional_2(self):
        """Test this fails when the readings are None."""
        #Create reading objects.
        sump_reading = None
        butts_reading = None
        butts_float_reading = None

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)
    @unittest.expectedFailure
    def test_sumppi_control_logic_exceptional_3(self):
        """Test this fails when the butts float switch reading is a string of nonsense."""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "ABCDEF", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)
    @unittest.expectedFailure
    def test_sumppi_control_logic_exceptional_4(self):
        """Test this fails when the level readings are not integers."""
        #Create reading objects.
        sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "0xemm", "OK")
        butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "rydfmm", "OK")
        butts_float_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                           butts_float_reading, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)
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
