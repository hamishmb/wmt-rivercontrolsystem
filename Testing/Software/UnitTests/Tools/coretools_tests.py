#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Core Tools Unit Tests for the River System Control and Monitoring Software
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
import datetime
import threading
from collections import deque
import time

#Import other modules.
sys.path.insert(0, os.path.abspath('../../../')) #Need to be able to import the Tools module from here.

import config
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

class TestDatabaseConnection(unittest.TestCase):
    """
    This test class tests the DatabaseConnection class in
    Tools/coretools.py
    """

    def setUp(self):
        self.orig_do_query = core_tools.DatabaseConnection.do_query
        core_tools.DatabaseConnection.do_query = data.fake_do_query

        self.dbconn = core_tools.DatabaseConnection("SUMP")

    def tearDown(self):
        del self.dbconn

        core_tools.DatabaseConnection.do_query = self.orig_do_query

        #Reset this to None as well to avoid polluting the environment for later tests.
        config.DBCONNECTION = None
        
    #---------- TEST CONSTRUCTOR ----------
    def test_constructor_1(self):
        """Test that the constructor works as expected when valid IDs are passed"""

        dbconn = core_tools.DatabaseConnection("SUMP")

        self.assertEqual(dbconn.site_id, "SUMP")
        self.assertFalse(dbconn.is_connected)
        self.assertEqual(dbconn.in_queue, deque())
        self.assertEqual(dbconn.result, None)
        self.assertTrue(dbconn.client_thread_done)
        self.assertFalse(dbconn.db_thread == threading.current_thread())
        self.assertTrue(isinstance(dbconn.client_lock, type(threading.RLock())))

    def test_constructor_2(self):
        """Test that the constructor fails when invalid IDs are passed"""

        for _id in (None, 0, False, (), "not_an_id", {}):
            try:
                dbconn = core_tools.DatabaseConnection(_id)

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError expected for data: "+str(id))

    #---------- TEST THREAD BODY ----------
    def test_thread_1(self):
        """Test that the thread can be started and stopped without connecting and without error."""
        #Change the database host IP to 127.0.0.1 and a strange port so we don't actually connect
        #to a real database during this test.
        original_mysql = core_tools.mysql
        core_tools.mysql = data.FakeMysqlConnectionFailure

        #Start the thread.
        self.dbconn.start_thread()

        self.assertTrue(self.dbconn.thread_running())

        #Stop the thread.
        config.EXITING = True

        while self.dbconn.thread_running():
            time.sleep(1)

        core_tools.mysql = original_mysql

    def test__connect_1(self):
        """Test this works as expected when connecting succeeds with valid arguments"""
        #Replace the mysql import with a fake one so we can test without actually connecting.
        original_mysql = core_tools.mysql
        core_tools.mysql = data.FakeMysqlConnectionSuccess

        database, cursor = self.dbconn._connect("test", "test", config.SITE_SETTINGS["SUMP"]["DBHost"], 3306)

        self.assertTrue(self.dbconn.is_ready())
        self.assertEqual(database, data.FakeDatabase)
        self.assertEqual(cursor, data.FakeDatabase)

        core_tools.mysql = original_mysql

    def test__connect_2(self):
        """Test this fails with invalid arguments"""
        #Replace the mysql import with a fake one so we can test without actually connecting.
        original_mysql = core_tools.mysql
        core_tools.mysql = data.FakeMysqlConnectionSuccess

        for args in data.TEST__CONNECT_BAD_DATA:
            try:
                self.dbconn._connect(args[0], args[1], args[2], args[3])

            except ValueError:
                #Expected.  
                self.assertFalse(self.dbconn.is_ready())

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError expected for data: "+str(args))

        core_tools.mysql = original_mysql

    def test__connect_3(self):
        """Test this works as expected when connecting fails with valid arguments"""
        #Replace the mysql import with a fake one so we can test without actually connecting.
        original_mysql = core_tools.mysql
        core_tools.mysql = data.FakeMysqlConnectionFailure

        database, cursor = self.dbconn._connect("test", "test", config.SITE_SETTINGS["SUMP"]["DBHost"], 3306)

        self.assertFalse(self.dbconn.is_ready())
        self.assertEqual(database, None)
        self.assertEqual(cursor, None)

        core_tools.mysql = original_mysql


    #NB: Not directly testing _initialise_db yet because this may well need to be
    #changed before deployment.
    
    #---------- TEST GETTER METHODS ----------
    def test_is_ready_1(self):
        """Test that the is_ready method works as expected"""
        for _bool in (True, False):
            self.dbconn.is_connected = _bool
            self.assertEqual(self.dbconn.is_ready(), _bool)

    def test_thread_running_1(self):
        """Test that the thread_running method works as expected"""
        for _bool in (True, False):
            self.dbconn.is_running = _bool
            self.assertEqual(self.dbconn.thread_running(), _bool)

    #---------- TEST CONVENIENCE READER METHODS ----------
    def test_get_latest_reading_1(self):
        """Test this works as when there are readings"""
        self.dbconn.result = [data.TEST_GET_N_LATEST_READINGS_DATA[0]]

        reading = self.dbconn.get_latest_reading("SUMP", "M0")

        self.assertTrue(isinstance(reading, core_tools.Reading))
        self.assertEqual(self.dbconn.result, None)

        #Check that the right query would have been executed.
        self.assertTrue("SUMPReadings" in self.dbconn.in_queue[0])
        self.assertTrue("M0" in self.dbconn.in_queue[0])
        self.assertEqual(self.dbconn.in_queue[0].split(" ")[-1].replace(";", ""), "1")

        #Check that the reading is equivelant to the data in the list.
        element = data.TEST_GET_N_LATEST_READINGS_DATA[0]

        self.assertEqual(reading.get_sensor_id(), element[1])
        self.assertEqual(reading.get_tick(), element[2])
        self.assertEqual(reading.get_time(), element[3])
        self.assertEqual(reading.get_value(), element[4])
        self.assertEqual(reading.get_status(), element[5])

    def test_get_latest_reading_2(self):
        """Test this works as when there no valid readings"""
        self.dbconn.result = data.TEST_GET_N_LATEST_READINGS_BAD_DATA[1:4]

        reading = self.dbconn.get_latest_reading("SUMP", "M0")

        self.assertEqual(reading, None)
        self.assertEqual(self.dbconn.result, None)

        #Check that the right query would have been executed.
        self.assertTrue("SUMPReadings" in self.dbconn.in_queue[0])
        self.assertTrue("M0" in self.dbconn.in_queue[0])
        self.assertEqual(self.dbconn.in_queue[0].split(" ")[-1].replace(";", ""), "1")

    def test_get_n_latest_readings_1(self):
        """Test this works when valid reading data is returned"""
        #Set the result ahead of time so we don't get deadlocked - the DB thread
        #isn't actually running.
        self.dbconn.result = data.TEST_GET_N_LATEST_READINGS_DATA[0:3]

        readings = self.dbconn.get_n_latest_readings("SUMP", "M0", 3)

        self.assertEqual(len(readings), 3)
        self.assertEqual(self.dbconn.result, None)

        #Check that the right query would have been executed.
        self.assertTrue("SUMPReadings" in self.dbconn.in_queue[0])
        self.assertTrue("M0" in self.dbconn.in_queue[0])
        self.assertEqual(self.dbconn.in_queue[0].split(" ")[-1].replace(";", ""), "3")

        #Check that the readings are equivelant to the data in the list.
        c = 0

        for element in data.TEST_GET_N_LATEST_READINGS_DATA[0:3]:
            self.assertEqual(readings[c].get_sensor_id(), element[1])
            self.assertEqual(readings[c].get_tick(), element[2])
            self.assertEqual(readings[c].get_time(), element[3])
            self.assertEqual(readings[c].get_value(), element[4])
            self.assertEqual(readings[c].get_status(), element[5])

            c += 1

    def test_get_n_latest_readings_2(self):
        """Test this works when no reading data is returned"""
        #Set the result ahead of time so we don't get deadlocked - the DB thread
        #isn't actually running.
        self.dbconn.result = []

        readings = self.dbconn.get_n_latest_readings("SUMP", "M0", 3)

        self.assertEqual(len(readings), 0)
        self.assertEqual(self.dbconn.result, None)

        #Check that the right query would have been executed.
        self.assertTrue("SUMPReadings" in self.dbconn.in_queue[0])
        self.assertTrue("M0" in self.dbconn.in_queue[0])
        self.assertEqual(self.dbconn.in_queue[0].split(" ")[-1].replace(";", ""), "3")

        #Check that the readings are equivelant to the data in the list.
        self.assertEqual(readings, [])

    def test_get_n_latest_readings_3(self):
        """Test this works when some invalid reading data is returned"""
        #Set the result ahead of time so we don't get deadlocked - the DB thread
        #isn't actually running.
        self.dbconn.result = data.TEST_GET_N_LATEST_READINGS_BAD_DATA

        #All except 3 of these are malformed and should be rejected.
        readings = self.dbconn.get_n_latest_readings("SUMP", "M0", 9)

        self.assertEqual(len(readings), 3)
        self.assertEqual(self.dbconn.result, None)

        #Check that the right query would have been executed.
        self.assertTrue("SUMPReadings" in self.dbconn.in_queue[0])
        self.assertTrue("M0" in self.dbconn.in_queue[0])
        self.assertEqual(self.dbconn.in_queue[0].split(" ")[-1].replace(";", ""), "9")

        #Check that the readings are equivelant to the data in the list.
        c = 0

        for element in (data.TEST_GET_N_LATEST_READINGS_BAD_DATA[0],
                        data.TEST_GET_N_LATEST_READINGS_BAD_DATA[4],
                        data.TEST_GET_N_LATEST_READINGS_BAD_DATA[6]):

            self.assertEqual(readings[c].get_sensor_id(), element[1])
            self.assertEqual(readings[c].get_tick(), element[2])
            self.assertEqual(readings[c].get_time(), element[3])
            self.assertEqual(readings[c].get_value(), element[4])
            self.assertEqual(readings[c].get_status(), element[5])

            c += 1

    def test_get_state_1(self):
        """Test this works when the state is available"""
        for result in data.TEST_GET_STATE_DATA:
            self.dbconn.result = result

            state = self.dbconn.get_state("SUMP", "P1")

            self.assertEqual(self.dbconn.result, None)
            self.assertEqual(state, result[0][2:])

            #Check that the right query would have been executed.
            self.assertTrue("SUMPControl" in self.dbconn.in_queue[0])
            self.assertTrue("P1" in self.dbconn.in_queue[0])

    def test_get_state_2(self):
        """Test this fails when the state isn't available"""
        self.dbconn.result = []

        state = self.dbconn.get_state("SUMP", "P1")

        self.assertEqual(self.dbconn.result, None)
        self.assertEqual(state, None)

        #Check that the right query would have been executed.
        self.assertTrue("SUMPControl" in self.dbconn.in_queue[0])
        self.assertTrue("P1" in self.dbconn.in_queue[0])

    #---------- TEST CONVENIENCE WRITER METHODS ----------
    def test_attempt_to_control_1(self):
        """Test this works when device isn't locked, and args are valid"""
        #Replace the get_state method with one that always returns the state we need to continue.
        original_getstate = self.dbconn.get_state
        self.dbconn.get_state = data.get_state_unlocked

        for args in data.TEST_ATTEMPT_TO_CONTROL_DATA:
            result = self.dbconn.attempt_to_control(args[0], args[1], args[2])

            self.assertTrue(result)

        #Test that the number of queries is what we expect.
        #Double the length of the data list, because we log the event each time.
        self.assertEqual(len(self.dbconn.in_queue), 2*len(data.TEST_ATTEMPT_TO_CONTROL_DATA))

        #Change the get_state method back to the original.
        self.dbconn.get_state = original_getstate

    def test_attempt_to_control_2(self):
        """Test this works when device is locked by the current pi, and args are valid"""
        #NB: Current pi is pretending to be Sump Pi for this test (see setUp method).

        #Replace the get_state method with one that always returns the state we need to continue.
        original_getstate = self.dbconn.get_state
        self.dbconn.get_state = data.get_state_lockedbysumppi

        for args in data.TEST_ATTEMPT_TO_CONTROL_DATA:
            result = self.dbconn.attempt_to_control(args[0], args[1], args[2])

            self.assertTrue(result)

        #Test that the number of queries is what we expect.
        #Double the length of the data list, because we log the event each time.
        self.assertEqual(len(self.dbconn.in_queue), 2*len(data.TEST_ATTEMPT_TO_CONTROL_DATA))

        #Change the get_state method back to the original.
        self.dbconn.get_state = original_getstate

    def test_attempt_to_control_3(self):
        """Test this works when device is locked by a different pi, and args are valid"""
        #NB: Current pi is pretending to be Sump Pi for this test (see setUp method).

        #Replace the get_state method with one that always returns the state we need to continue.
        original_getstate = self.dbconn.get_state
        self.dbconn.get_state = data.get_state_lockedbybuttspi

        for args in data.TEST_ATTEMPT_TO_CONTROL_DATA:
            result = self.dbconn.attempt_to_control(args[0], args[1], args[2])

            self.assertFalse(result)

        #Test that the number of queries is what we expect.
        self.assertEqual(len(self.dbconn.in_queue), 0)

        #Change the get_state method back to the original.
        self.dbconn.get_state = original_getstate

    def test_attempt_to_control_4(self):
        """Test this works when state is unavailable, and args are valid"""
        #NB: Current pi is pretending to be Sump Pi for this test (see setUp method).

        #Replace the get_state method with one that always returns the state we need to continue.
        original_getstate = self.dbconn.get_state
        self.dbconn.get_state = data.get_state_unavailable

        for args in data.TEST_ATTEMPT_TO_CONTROL_DATA:
            result = self.dbconn.attempt_to_control(args[0], args[1], args[2])

            self.assertFalse(result)

        #Test that the number of queries is what we expect.
        self.assertEqual(len(self.dbconn.in_queue), 0)

        #Change the get_state method back to the original.
        self.dbconn.get_state = original_getstate

    def test_attempt_to_control_5(self):
        """Test this fails when args are invalid"""
        #Replace the get_state method with one that always returns the state we need to continue.
        original_getstate = self.dbconn.get_state
        self.dbconn.get_state = data.get_state_lockedbybuttspi

        for args in data.TEST_ATTEMPT_TO_CONTROL_BAD_DATA:
            try:
                self.dbconn.attempt_to_control(args[0], args[1], args[2])

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError expected for data: "+str(args))

        #Change the get_state method back to the original.
        self.dbconn.get_state = original_getstate

    def test_release_control_1(self):
        """Test this works when the device is already unlocked, with valid arguments"""
        #Replace the get_state method with one that always returns the state we need to continue.
        original_getstate = self.dbconn.get_state
        self.dbconn.get_state = data.get_state_unlocked

        for args in data.TEST_ATTEMPT_TO_CONTROL_DATA:
            self.dbconn.release_control(args[0], args[1])

        #Test that the number of queries is what we expect.
        self.assertEqual(len(self.dbconn.in_queue), 0)

        #Change the get_state method back to the original.
        self.dbconn.get_state = original_getstate

    def test_release_control_2(self):
        """Test this works when the device is locked by a different pi, with valid arguments"""
        #Replace the get_state method with one that always returns the state we need to continue.
        original_getstate = self.dbconn.get_state
        self.dbconn.get_state = data.get_state_lockedbybuttspi

        for args in data.TEST_ATTEMPT_TO_CONTROL_DATA:
            self.dbconn.release_control(args[0], args[1])

        #Test that the number of queries is what we expect.
        self.assertEqual(len(self.dbconn.in_queue), 0)

        #Change the get_state method back to the original.
        self.dbconn.get_state = original_getstate

    def test_release_control_3(self):
        """Test this works when the device state is unavailable, with valid arguments"""
        #Replace the get_state method with one that always returns the state we need to continue.
        original_getstate = self.dbconn.get_state
        self.dbconn.get_state = data.get_state_unavailable

        for args in data.TEST_ATTEMPT_TO_CONTROL_DATA:
            self.dbconn.release_control(args[0], args[1])

        #Test that the number of queries is what we expect.
        self.assertEqual(len(self.dbconn.in_queue), 0)

        #Change the get_state method back to the original.
        self.dbconn.get_state = original_getstate

    def test_release_control_4(self):
        """Test this works when the device was locked by this pi, with valid arguments"""
        #NB: Current pi is pretending to be Sump Pi for this test (see setUp method).

        #Replace the get_state method with one that always returns the state we need to continue.
        original_getstate = self.dbconn.get_state
        self.dbconn.get_state = data.get_state_lockedbysumppi

        for args in data.TEST_ATTEMPT_TO_CONTROL_DATA:
            self.dbconn.release_control(args[0], args[1])

        #Change the get_state method back to the original.
        self.dbconn.get_state = original_getstate

    def test_release_control_5(self):
        """Test this fails with invalid arguments"""
        #NB: Current pi is pretending to be Sump Pi for this test (see setUp method).

        #Replace the get_state method with one that always returns the state we need to continue.
        original_getstate = self.dbconn.get_state
        self.dbconn.get_state = data.get_state_lockedbysumppi

        for args in data.TEST_RELEASE_CONTROL_BAD_DATA:
            try:
                self.dbconn.release_control(args[0], args[1])

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed!
                self.assertTrue(False, "ValueError was expected for data: "+str(args))

        #Test that the number of queries is what we expect.
        self.assertEqual(len(self.dbconn.in_queue), 0)

        #Change the get_state method back to the original.
        self.dbconn.get_state = original_getstate

    def test_log_event_1(self):
        """Test this works when given valid arguments"""
        for event in ("SUMP Rebooting", "P0 Enabled", "G6 is down"):
            self.dbconn.log_event(event)

        self.assertTrue(len(self.dbconn.in_queue) == 3)

    def test_log_event_2(self):
        """Test this fails when given invalid arguments"""
        for event in ("", 7, True, 5.6, None, (), {}):
            try:
                self.dbconn.log_event(event)

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed.
                self.assertTrue(False, "ValueError expected for data: "+str(event))

    def test_update_status_1(self):
        """Test this works when given valid arguments"""
        for args in (("Up", "OK", "None"), ("Up", "OK", "P0 Enabled"),
                     ("Down", "Rebooting", "None"), ("Down", "No Connection", "None")):
            self.dbconn.update_status(args[0], args[1], args[2])

    def test_update_status_2(self):
        """Test this fails when given invalid arguments"""
        for args in (("Up", "", "None"), (True, "OK", "P0 Enabled"),
                     ("Down", 0.7, "None"), (None, "No Connection", "None"),
                     ((), "test", "None"), ("Up", "Slow Connection", {})):
            try:
                self.dbconn.update_status(args[0], args[1], args[2])

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed.
                self.assertTrue(False, "ValueError expected for data: "+str(args))

    def test_store_reading_1(self):
        """Test this works when given valid arguments"""
        time = str(datetime.datetime.now())
        reading = core_tools.Reading(time, 1, "SUMP:M0", "100", "OK")
        reading_2 = core_tools.Reading(time, 6, "SUMP:M1", "200", "OK")
        reading_3 = core_tools.Reading(time, 6, "SUMP:M0", "100", "OK")

        for reading_obj in (reading, reading_2, reading_3):
            self.dbconn.store_reading(reading_obj)

        self.assertTrue(len(self.dbconn.in_queue) == 3)

    def test_store_reading_2(self):
        """Test this fails when given invalid arguments"""
        for reading_obj in ("", "test", 0, 9.8, True, None, {}, (), []):
            try:
                self.dbconn.store_reading(reading_obj)

            except ValueError:
                #Expected.
                pass

            else:
                #This should have failed.
                self.assertTrue(False, "ValueError expected for data: "+str(reading_obj))

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
