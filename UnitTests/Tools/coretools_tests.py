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

class TestControlLogic(unittest.TestCase):
    """
    This test class tests the control logic functions in
    Tools/coretools.py
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_sumppi_control_logic_(self):
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
