#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Device Management Unit Tests for the River System Control and Monitoring Software
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
        self.mgmtclass = device_mgmt.ManageHallEffectProbe(self.probe)

    def tearDown(self):
        del self.mgmtclass
        del self.probe

    #---------- CONSTRUCTOR TESTS ----------
    #Note: No fancy test here because there's only one argument - the probe object.

    def test_constructor_1(self):
        """Test the constructor works as expected"""
        probe = device_objects.HallEffectProbe("G4:M0", "Test")
        mgmtclass = device_mgmt.ManageHallEffectProbe(probe)

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

    def test_test_levels_1(self):
        """Test that the test_levels() function works as expected"""
        self.probe.set_limits(data.HIGH_LIMITS, data.LOW_LIMITS)
        self.probe.set_depths(data.DEPTHS)

        #Replace this with our face method so we can inject values to test.
        self.mgmtclass.get_compensated_probe_voltages = data.get_compensated_probe_voltages

        try:
            while True:
                level = self.mgmtclass.test_levels()
                self.assertEqual(level, data.test_levels_result())
                data.voltages_position += 1

        except RuntimeError:
            #Happens when there are no more results to test.
            pass
