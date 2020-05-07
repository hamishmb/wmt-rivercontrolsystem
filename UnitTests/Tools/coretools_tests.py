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
import threading
from collections import deque
import time

#Import other modules.
sys.path.append('../..') #Need to be able to import the Tools module from here.

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
        self.dbconn = core_tools.DatabaseConnection("SUMP")

    def tearDown(self):
        del self.dbconn

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
        original_dbhost = config.SITE_SETTINGS["SUMP"]["DBHost"]
        original_dbport = config.SITE_SETTINGS["SUMP"]["DBPort"]

        config.SITE_SETTINGS["SUMP"]["DBHost"] = "127.0.0.1"
        config.SITE_SETTINGS["SUMP"]["DBPort"] = 65534

        #Start the thread.
        self.dbconn.start_thread()

        self.assertTrue(self.dbconn.thread_running())

        #Stop the thread.
        config.EXITING = True

        while self.dbconn.thread_running():
            time.sleep(1)

        #Reset db host IP.
        config.SITE_SETTINGS["SUMP"]["DBHost"] = original_dbhost
        config.SITE_SETTINGS["SUMP"]["DBPort"] = original_dbport

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

        #Test that the number of queries is what we expect.
        #Double the length of the data list, because we log the event each time.
        self.assertEqual(len(self.dbconn.in_queue), 2*len(data.TEST_ATTEMPT_TO_CONTROL_DATA))

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

        #Double the length of the data list, because we log the event each time.
        self.assertTrue(len(self.dbconn.in_queue) == 8)

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
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "800mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "True", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(reading_interval, 60)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_2(self):
        """Test this works as expected when sump and butts are at 800mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "800mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_3(self):
        """Test this works as expected when sump and butts are at 700mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "700mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "700mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_5(self):
        """Test this works as expected when sump and butts are at 600mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "600mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "600mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_6(self):
        """Test this works as expected when sump and butts are at 500mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "500mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "500mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(reading_interval, 15)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_7(self):
        """Test this works as expected when sump and butts are at 500mm, butts pump on, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "500mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "500mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        #Turn the fake butts pump on.
        self.butts_pump.enable()

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(reading_interval, 15)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_8(self):
        """Test this works as expected when sump and butts are at 400mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "400mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(reading_interval, 60)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_9(self):
        """Test this works as expected when sump and butts are at 300mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "300mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "300mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(reading_interval, 60)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_10(self):
        """Test this works as expected when sump at 300mm, butts at 200mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "300mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "200mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(reading_interval, 60)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_11(self):
        """Test this works as expected when sump at 200mm, butts at 600mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "200mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "600mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_12(self):
        """Test this works as expected when sump and butts are at 200mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "200mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "200mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(reading_interval, 30)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_13(self):
        """Test this works as expected when sump and butts are at 100mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "100mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(reading_interval, 15)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    def test_sumppi_control_logic_14(self):
        """Test this works as expected when sump at 100m, butts at 400mm, float switch pressed"""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
        self.assertEqual(reading_interval, 15)
        self.assertEqual(self.test_monitor.get_reading_interval(), reading_interval)

    #-------------------- ERRONEOUS VALUES --------------------
    @unittest.expectedFailure
    def test_sumppi_control_logic_bad_1(self):
        """Test this fails when the main circulation pump is not in the list of devices."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        #Remove main circulation pump from device list.
        self.devices.pop(1)

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)
    @unittest.expectedFailure
    def test_sumppi_control_logic_bad_2(self):
        """Test this fails when the butts pump is not in the list of devices."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        #Remove butts pump from device list.
        self.devices.pop(0)

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    @unittest.expectedFailure
    def test_sumppi_control_logic_bad_3(self):
        """Test this fails when there are no devices in the list."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        #Clear the devices list.
        self.devices = []

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    def test_sumppi_control_logic_bad_4(self):
        """Test this fails when there are no sockets in the list."""
        #FIXME sockets not used here any more, so doesn't fail.
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        #Clear the sockets list.
        self.sockets = []

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    @unittest.expectedFailure
    def test_sumppi_control_logic_bad_5(self):
        """Test this fails when the reading interval is 0."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           0)

    def test_sumppi_control_logic_bad_6(self):
        """Test this works when the readings for the sump and the butts are over 1000mm."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "1100mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "4400mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    def test_sumppi_control_logic_bad_7(self):
        """Test this works when the readings for the sump and the butts are under 0mm."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "-100mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "-400mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    #-------------------- EXCEPTIONAL VALUES --------------------
    @unittest.expectedFailure
    def test_sumppi_control_logic_exceptional_1(self):
        """Test this fails when the reading interval is negative."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           -78)

    @unittest.expectedFailure
    def test_sumppi_control_logic_exceptional_2(self):
        """Test this fails when the readings are None."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = None
        readings["G4:M0"] = None
        readings["G4:FS0"] = None

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)

    @unittest.expectedFailure
    def test_sumppi_control_logic_exceptional_3(self):
        """Test this fails when the butts float switch reading is a string of nonsense."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "100mm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "400mm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "ABCDEF", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
                                                           self.monitors, self.sockets,
                                                           self.reading_interval)
    @unittest.expectedFailure
    def test_sumppi_control_logic_exceptional_4(self):
        """Test this fails when the level readings are not integers."""
        #Create reading objects.
        readings = {}
        readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "0xemm", "OK")
        readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "rydfmm", "OK")
        readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "False", "OK")

        reading_interval = core_tools.sumppi_control_logic(readings, self.devices,
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
