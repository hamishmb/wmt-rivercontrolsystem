#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Monitor Tools Unit Tests for the River System Control and Monitoring Software
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
import os
import time
import shutil
import datetime
import threading
import subprocess

#Import other modules.
sys.path.insert(0, os.path.abspath('../../../')) #Need to be able to import the Tools module from here.

import Tools
import Tools.monitortools as monitor_tools
import Tools.coretools as core_tools
import Tools.logiccoretools as logiccoretools
import Tools.deviceobjects as device_objects

#Import test data and functions.
from . import monitortools_test_data as data

class TestBaseMonitorClass(unittest.TestCase):
    """This test class tests the features of the BaseMonitorClass class in Tools/monitortools.py"""
    def setUp(self):
        self.basemonitor = monitor_tools.BaseMonitorClass("SUMP", "M0")

        self.reading = core_tools.Reading(str(datetime.datetime.now()), 0,
                                     "G4:M0", "400mm", "OK")

        self.basemonitor.queue.append(self.reading)

        self.orig_store_reading = logiccoretools.store_reading
        logiccoretools.store_reading = data.fake_store_reading

    def tearDown(self):
        del self.reading
        del self.basemonitor

        logiccoretools.store_reading = self.orig_store_reading

    def set_exited_flag(self):
        self.basemonitor.running = False

    def test_constructor_1(self):
        """Test that the constructor works when passed valid arguments"""
        for dataset in data.TEST_BASEMONITOR_DATA:
            system_id = dataset[0]
            device_id = dataset[1]

            new_basemonitor = monitor_tools.BaseMonitorClass(system_id, device_id)

            self.assertEqual(new_basemonitor.get_system_id(), system_id)
            self.assertEqual(new_basemonitor.get_probe_id(), device_id)

    def test_constructor_2(self):
        """Test that the constructor fails when passed invalid arguments"""
        for dataset in data.TEST_BASEMONITOR_BAD_DATA:
            system_id = dataset[0]
            device_id = dataset[1]

            try:
                new_basemonitor = monitor_tools.BaseMonitorClass(system_id, device_id)

            except ValueError:
                #This is expected.
                pass

            else:
                #These should all throw errors!
                self.assertTrue(False, "ValueError was expected for data: "+str(dataset))

    def test_get_reading_1(self):
        """Test that get_reading works when there is a reading to return."""
        self.assertEqual(self.basemonitor.get_reading(), self.reading)

    @unittest.expectedFailure
    def test_get_reading_2(self):
        """Test that get_reading fails when there are no readings to return."""
        self.assertEqual(self.basemonitor.get_reading(), self.reading)
        self.assertEqual(self.basemonitor.get_reading(), self.reading)

    def test_get_previous_reading_1(self):
        """Test that get_previous_reading returns "" when no previous reading is available"""
        self.assertEqual(self.basemonitor.get_previous_reading(), "")

    def test_get_previous_reading_2(self):
        """Test that get_previous_reading works when a previous reading is available"""
        self.basemonitor.get_reading()
        self.assertEqual(self.basemonitor.get_previous_reading(), self.reading)

    def test_is_running_1(self):
        """Test that is_running reports status correctly when not running"""
        self.assertFalse(self.basemonitor.is_running())

    def test_is_running_2(self):
        """Test that is_running reports status correctly when running"""
        self.basemonitor.running = True
        self.assertTrue(self.basemonitor.is_running())

    def test_has_data_1(self):
        """Test that has_data works when there is data on the queue"""
        self.assertTrue(self.basemonitor.has_data())

    def test_has_data_2(self):
        """Test that has_data works when there isn't data on the queue"""
        self.basemonitor.get_reading()
        self.assertFalse(self.basemonitor.has_data())

    def test_set_reading_interval_1(self):
        """Test that setting the reading interval works"""
        for i in range(0, 600):
            self.basemonitor.set_reading_interval(i)
            self.assertEqual(self.basemonitor.reading_interval, i)

    def test_create_file_handle_1(self):
        """Test that create_file_handle works when the readings directory is missing"""
        os.chdir("UnitTests")

        try:
            if os.path.exists("readings"):
                shutil.rmtree("readings")

            self.basemonitor.create_file_handle()
            self.basemonitor.file_handle.close()

        except Exception as e:
            raise e

        finally:
            try:
                self.basemonitor.file_handle.close()

            except:
                pass

            try:
                shutil.rmtree("readings")

            except:
                pass

            os.chdir("../")

    def test_create_file_handle_2(self):
        """Test that create_file_handle works when the readings directory is there"""
        #Create the readings directory.
        os.chdir("UnitTests")

        try:
            if os.path.exists("readings"):
                shutil.rmtree("readings")

            os.mkdir("readings")

            self.basemonitor.create_file_handle()
            self.basemonitor.file_handle.close()

        except Exception as e:
            raise e

        finally:
            try:
                self.basemonitor.file_handle.close()

            except:
                pass

            try:
                shutil.rmtree("readings")

            except:
                pass

            os.chdir("../")

    @unittest.expectedFailure
    def test_create_file_handle_3(self):
        """Test that create_file_handle fails when we can't write the start time and CSV header"""
        #Create the readings directory.
        os.chdir("UnitTests")

        error = None

        try:
            if os.path.exists("readings"):
                shutil.rmtree("readings")

            os.mkdir("readings")

            #Replace the open function with a special one for this test.
            monitor_tools.open = data.badopen

            self.basemonitor.create_file_handle()
            self.basemonitor.file_handle.close()

        except Exception as e:
            error = e

        finally:
            try:
                self.basemonitor.file_handle.close()

            except:
                pass

            monitor_tools.open = open

            try:
                shutil.rmtree("readings")

            except:
                pass

            os.chdir("../")

            if error is not None:
                raise error

    def test_handle_reading_1(self):
        """Test that handle_reading() works as expected when the reading differs to the previous reading, and there are no issues writing to the file"""
        reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")
        previous_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "775mm", "OK")

        #Create a fake file handle.
        self.basemonitor.file_handle = data.goodopen("test", "r")

        previous_reading, write_failed = self.basemonitor.handle_reading(reading, previous_reading)

        self.assertEqual(previous_reading, reading)
        self.assertFalse(write_failed)

    def test_handle_reading_2(self):
        """Test that handle_reading() works as expected when the reading equals the previous reading, and there are no issues writing to the file"""
        reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")
        previous_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")

        #Create a fake file handle.
        self.basemonitor.file_handle = data.goodopen("test", "r")

        prev_reading, write_failed = self.basemonitor.handle_reading(reading, previous_reading)

        self.assertEqual(prev_reading, previous_reading)
        self.assertEqual(prev_reading, reading)
        self.assertFalse(write_failed)

    def test_handle_reading_3(self):
        """Test that handle_reading() works as expected when there are issues writing to the file"""
        reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")
        previous_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")

        #Create a fake file handle.
        self.basemonitor.file_handle = data.badopen("test", "r")

        prev_reading, write_failed = self.basemonitor.handle_reading(reading, previous_reading)

        self.assertEqual(prev_reading, previous_reading)
        self.assertEqual(prev_reading, reading)
        self.assertTrue(write_failed)

    def test_manage_rotation_1(self):
        """Test that manage_rotation() works as expected when rotation is not due and all is fine"""
        previous_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")

        #Just a hack to make sure that the file is reported to exist.
        self.basemonitor.current_file_name = "unittests.py"

        #Set the expiration time to midnight so we can rotate readings files.
        #This uses the datetime class cos it's easier to compare times that way.
        midnight = datetime.time(hour=23, minute=59, second=59)
        current_time = datetime.datetime.now()

        self.basemonitor.midnight_tonight = datetime.datetime.combine(current_time.date(),
                                                                      midnight)

        prev_reading, should_continue = self.basemonitor.manage_rotation(False,
                                                                         previous_reading)

        del self.basemonitor.current_file_name
        del self.basemonitor.midnight_tonight

        self.assertEqual(prev_reading, previous_reading)
        self.assertFalse(should_continue)

    def test_manage_rotation_2(self):
        """Test that manage_rotation() works as expected when rotation is not due and the readings file is missing"""
        previous_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")

        #----- BEGIN HACKY STUFF TO MAKE THE TEST WORK -----
        #Just a hack to make sure that the file is reported not to exist.
        self.basemonitor.current_file_name = "i_dont_exist"

        #Set the expiration time to midnight so we can rotate readings files.
        #This uses the datetime class cos it's easier to compare times that way.
        midnight = datetime.time(hour=23, minute=59, second=59)
        current_time = datetime.datetime.now()

        self.basemonitor.midnight_tonight = datetime.datetime.combine(current_time.date(),
                                                                      midnight)

        self.basemonitor.file_handle = data.goodopen("test", "r")

        create_file_handle_method = self.basemonitor.create_file_handle

        self.basemonitor.create_filehandle = data.do_nothing

        #----- END HACKY STUFF ---

        prev_reading, should_continue = self.basemonitor.manage_rotation(False,
                                                                         previous_reading)

        #Revert all the hacky stuff we just did.
        self.basemonitor.current_file_name = None
        self.basemonitor.midnight_tonight = None
        self.basemonitor.file_handle = None
        self.basemonitor.create_file_handle = create_file_handle_method

        self.assertEqual(prev_reading, None)
        self.assertTrue(should_continue)

    def test_manage_rotation_3(self):
        """Test that manage_rotation() works as expected when rotation is not due and we failed to write to the readings file"""
        previous_reading = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "800mm", "OK")

        #----- BEGIN HACKY STUFF TO MAKE THE TEST WORK -----
        #Just a hack to make sure that the file is reported not to exist.
        self.basemonitor.current_file_name = "main.py"

        #Set the expiration time to midnight so we can rotate readings files.
        #This uses the datetime class cos it's easier to compare times that way.
        midnight = datetime.time(hour=23, minute=59, second=59)
        current_time = datetime.datetime.now()

        self.basemonitor.midnight_tonight = datetime.datetime.combine(current_time.date(),
                                                                      midnight)

        self.basemonitor.file_handle = data.goodopen("test", "r")

        create_file_handle_method = self.basemonitor.create_file_handle

        self.basemonitor.create_filehandle = data.do_nothing

        #----- END HACKY STUFF ---

        prev_reading, should_continue = self.basemonitor.manage_rotation(True,
                                                                         previous_reading)

        #Revert all the hacky stuff we just did.
        self.basemonitor.current_file_name = None
        self.basemonitor.midnight_tonight = None
        self.basemonitor.file_handle = None
        self.basemonitor.create_file_handle = create_file_handle_method

        self.assertEqual(prev_reading, None)
        self.assertTrue(should_continue)

    #TODO Test that manage_rotation works when rotation is due.

    def test_request_exit_1(self):
        """Test that requesting exit without waiting works"""
        self.basemonitor.request_exit()

    def test_request_exit_2(self):
        """Test that requesting exit and waiting works"""
        self.basemonitor.running = True

        #Schedule the exit flag to be set in 10 seconds.
        threading.Timer(10, self.set_exited_flag).start()
        self.basemonitor.request_exit(wait=True)

class TestMonitor(unittest.TestCase):
    """
    This test class tests the features of the Monitor class in
    Tools/monitortools.py
    """

    def setUp(self):
        os.chdir("UnitTests")

        self.halleffectprobe = device_objects.HallEffectProbe("SUMP:M0", "Test")

        #Make sure it won't exit immediately.
        monitor_tools.config.EXITING = False

        self.orig_store_reading = logiccoretools.store_reading
        logiccoretools.store_reading = data.fake_store_reading

    def tearDown(self):
        del self.halleffectprobe

        #Clear the readings directory that has been created.
        if os.path.isdir("readings"):
            shutil.rmtree("readings")
            os.mkdir("readings")

        os.chdir("../")

        logiccoretools.store_reading = self.orig_store_reading

    def test_1(self):
        """Test that the class initialises and exits correctly (slow test)"""
        monitor = monitor_tools.Monitor(self.halleffectprobe, 5, "SUMP")

        #Check that the constructor worked.
        self.assertEqual(monitor.probe, self.halleffectprobe)
        self.assertEqual(monitor.reading_interval, 5)
        self.assertEqual(monitor.reading_func, self.halleffectprobe.get_reading)

        time.sleep(25)

        #Stop the monitor thread.
        monitor_tools.config.EXITING = True

        while monitor.is_running():
            time.sleep(1)

        #Monitor thread has exited.
        #Check shutdown code worked.
        self.assertFalse(monitor.running)

class TestSocketsMonitor(unittest.TestCase):
    """
    This test class tests the features of the SocketsMonitor class in
    Tools/monitortools.py
    """

    def setUp(self):
        os.chdir("UnitTests")

        self.socket = data.Sockets()

        #Make sure it won't exit immediately.
        monitor_tools.config.EXITING = False

    def tearDown(self):
        del self.socket

        #Clear the readings directory that has been created.
        if os.path.isdir("readings"):
            shutil.rmtree("readings")
            os.mkdir("readings")

        os.chdir("../")

    def test_1(self):
        """Test that the class initialises and exits correctly (slow test)"""
        monitor = monitor_tools.SocketsMonitor(self.socket, "SUMP", "M0")

        #Check that the constructor worked.
        self.assertEqual(monitor.socket, self.socket)
        self.assertEqual(monitor.probe_id, "M0")

        time.sleep(25)

        #Stop the monitor thread.
        monitor_tools.config.EXITING = True

        while monitor.is_running():
            time.sleep(1)

        #Monitor thread has exited.
        #Check shutdown code worked.
        self.assertFalse(monitor.running)
