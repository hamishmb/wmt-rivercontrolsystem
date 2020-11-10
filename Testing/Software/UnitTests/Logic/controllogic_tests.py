#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Control Logic Unit Tests for the River System Control and Monitoring Software
# Copyright (C) 2017-2020 Wimborne Model Town
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
import datetime
import threading
from collections import deque
import time

#Import other modules.
sys.path.insert(0, os.path.abspath('../../../')) #Need to be able to import the Tools module from here.

import config
import Tools
import Tools.coretools as core_tools
import Tools.logiccoretools as logiccoretools

import Logic
import Logic.controllogic as control_logic

#Import test data and functions.
from . import controllogic_test_data as data

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

        #Disabling functions in logiccoretools because we aren't testing them here.
        self.orig_attempt_to_control = logiccoretools.attempt_to_control
        self.orig_update_status = logiccoretools.update_status
        self.orig_get_latest_reading = logiccoretools.get_latest_reading

        logiccoretools.attempt_to_control = data.fake_attempt_to_control
        logiccoretools.update_status = data.fake_update_status
        logiccoretools.get_latest_reading = data.fake_get_latest_reading

        config.CPU = "50"
        config.MEM = "50"

    def tearDown(self):
        del self.devices
        del self.sockets
        del self.butts_pump
        del self.sump_pump
        del self.reading_interval

        logiccoretools.attempt_to_control = self.orig_attempt_to_control
        logiccoretools.update_status = self.orig_update_status
        logiccoretools.get_latest_reading = self.orig_get_latest_reading

        #Reset readings dictionary in data.
        data.readings.clear()

        config.CPU = None
        config.MEM = None

    #-------------------- NORMAL VALUES --------------------
    def test_sumppi_control_logic_1(self):
        """Test this works as expected when sump and butts are at 900mm, float switch floating"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "800mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "True", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: 60.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), [])
        self.assertEqual(data.states["VALVE4:V4"][0], "0%")
        self.assertEqual(reading_interval, 60)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_2(self):
        """Test this works as expected when sump and butts are at 800mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "800mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: on.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: 30.

        self.assertTrue(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), [])
        self.assertEqual(data.states["VALVE4:V4"][0], "0%")
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_3(self):
        """Test this works as expected when sump and butts are at 700mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "700mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "700mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: on.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: 30.

        self.assertTrue(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), [])
        self.assertEqual(data.states["VALVE4:V4"][0], "0%")
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_5(self):
        """Test this works as expected when sump and butts are at 600mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "600mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "600mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)
        #Expected behaviour:
        #Butts Pump: on.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: 30.

        self.assertTrue(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), [])
        self.assertEqual(data.states["VALVE4:V4"][0], "0%")
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_6(self):
        """Test this works as expected when sump and butts are at 500mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "500mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "500mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(self.gate_valve_socket.get_queue(), [])
        self.assertEqual(data.states["VALVE4:V4"][0], "0%")
        self.assertEqual(reading_interval, 15)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_7(self):
        """Test this works as expected when sump and butts are at 500mm, butts pump on, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "500mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "500mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        #Turn the fake butts pump on.
        self.butts_pump.enable()

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(self.gate_valve_socket.get_queue(), [])
        self.assertEqual(data.states["VALVE4:V4"][0], "0%")
        self.assertEqual(reading_interval, 15)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_8(self):
        """Test this works as expected when sump and butts are at 400mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "400mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: 60.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), [])
        self.assertEqual(data.states["VALVE4:V4"][0], "0%")
        self.assertEqual(reading_interval, 60)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_9(self):
        """Test this works as expected when sump and butts are at 300mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "300mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "300mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: on.
        #Gate Valve Position: 25.
        #Reading Interval: 60.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), [])
        self.assertEqual(data.states["VALVE4:V4"][0], "25%")
        self.assertEqual(reading_interval, 60)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_10(self):
        """Test this works as expected when sump at 300mm, butts at 200mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "300mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "200mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)
        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: on.
        #Gate Valve Position: 0.
        #Reading Interval: 60.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertTrue(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), [])
        self.assertEqual(data.states["VALVE4:V4"][0], "0%")
        self.assertEqual(reading_interval, 60)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_11(self):
        """Test this works as expected when sump at 200mm, butts at 600mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "200mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "600mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: off.
        #Gate Valve Position: 50.
        #Reading Interval: 30.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertFalse(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), [])
        self.assertEqual(data.states["VALVE4:V4"][0], "50%")
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_12(self):
        """Test this works as expected when sump and butts are at 200mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "200mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "200mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: off.
        #Gate Valve Position: 0.
        #Reading Interval: 30.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertFalse(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), [])
        self.assertEqual(data.states["VALVE4:V4"][0], "0%")
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_13(self):
        """Test this works as expected when sump and butts are at 100mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "100mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: off.
        #Gate Valve Position: 0.
        #Reading Interval: 15.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertFalse(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), [])
        self.assertEqual(data.states["VALVE4:V4"][0], "0%")
        self.assertEqual(reading_interval, 15)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_14(self):
        """Test this works as expected when sump at 100m, butts at 400mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

        #Expected behaviour:
        #Butts Pump: off.
        #Circulation Pump: off.
        #Gate Valve Position: 100.
        #Reading Interval: 15.

        self.assertFalse(self.butts_pump.is_enabled())
        self.assertFalse(self.sump_pump.is_enabled())
        self.assertEqual(self.gate_valve_socket.get_queue(), [])
        self.assertEqual(data.states["VALVE4:V4"][0], "100%")
        self.assertEqual(reading_interval, 15)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    #-------------------- ERRONEOUS VALUES --------------------
    @unittest.expectedFailure
    def test_sumppi_control_logic_bad_1(self):
        """Test this fails when the main circulation pump is not in the list of devices."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        #Remove main circulation pump from device list.
        self.devices.pop(1)

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)
    @unittest.expectedFailure
    def test_sumppi_control_logic_bad_2(self):
        """Test this fails when the butts pump is not in the list of devices."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        #Remove butts pump from device list.
        self.devices.pop(0)

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    @unittest.expectedFailure
    def test_sumppi_control_logic_bad_3(self):
        """Test this fails when there are no devices in the list."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        #Clear the devices list.
        self.devices = []

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    @unittest.expectedFailure
    def test_sumppi_control_logic_bad_5(self):
        """Test this fails when the reading interval is 0."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           0)

    def test_sumppi_control_logic_bad_6(self):
        """Test this works when the readings for the sump and the butts are over 1000mm."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "1100mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "4400mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    def test_sumppi_control_logic_bad_7(self):
        """Test this works when the readings for the sump and the butts are under 0mm."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "-100mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "-400mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    #-------------------- EXCEPTIONAL VALUES --------------------
    @unittest.expectedFailure
    def test_sumppi_control_logic_exceptional_1(self):
        """Test this fails when the reading interval is negative."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           -78)

    @unittest.expectedFailure
    def test_sumppi_control_logic_exceptional_2(self):
        """Test this fails when the readings are None."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = None

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [None]
        data.readings["G4:FS0"] = [None]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    @unittest.expectedFailure
    def test_sumppi_control_logic_exceptional_3(self):
        """Test this fails when the butts float switch reading is a string of nonsense."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "ABCDEF", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)
    @unittest.expectedFailure
    def test_sumppi_control_logic_exceptional_4(self):
        """Test this fails when the level readings are not integers."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "0xemm", "OK")

        #Prepare fake logiccoretools readings.
        data.readings["G4:M0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "rydfmm", "OK")]
        data.readings["G4:FS0"] = [core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")]

        reading_interval = control_logic.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)
