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
import shutil
import datetime
import threading
import subprocess

#Import other modules.
sys.path.append('../..') #Need to be able to import the Tools module from here.

import Tools
import Tools.monitortools as monitor_tools
import Tools.coretools as core_tools

#Import test data and functions.
from . import monitortools_test_data as data

class TestBaseMonitorClass(unittest.TestCase):
    """This test class tests the features of the BaseMonitorClass class in Tools/monitortools.py"""
    def setUp(self):
        self.basemonitor = monitor_tools.BaseMonitorClass("SUMP", "M0")

        self.reading = core_tools.Reading(str(datetime.datetime.now()), 0,
                                     "G4:M0", "400mm", "OK")

        self.basemonitor.queue.append(self.reading)

    def tearDown(self):
        del self.reading
        del self.basemonitor

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

            shutil.rmtree("readings")

        except Exception as e:
            raise e

        finally:
            try:
                self.basemonitor.file_handle.close()

            except:
                pass

            os.chdir("../")

    @unittest.expectedFailure
    def test_create_file_handle_3(self):
        """Test that create_file_handle fails when the readings directory is there, but we don't have permission to write to it"""
        #Create the readings directory, and change its permissions so we have no access to it.
        os.chdir("UnitTests")

        error = None

        try:
            if os.path.exists("readings"):
                shutil.rmtree("readings")

            os.mkdir("readings")
            subprocess.check_call(["chmod", "a-rwx", "readings"])

            self.basemonitor.create_file_handle()
            self.basemonitor.file_handle.close()

            shutil.rmtree("readings")

        except Exception as e:
            error = e

        finally:
            try:
                self.basemonitor.file_handle.close()

            except:
                pass

            os.rmdir("readings")
            os.chdir("../")

            if error is not None:
                raise error

    def test_request_exit_1(self):
        """Test that requesting exit without waiting works"""
        self.basemonitor.request_exit()
        self.assertTrue(self.basemonitor.should_exit)

    def test_request_exit_2(self):
        """Test that requesting exit and waiting works"""
        return

        self.basemonitor.running = True

        #Schedule the exit flag to be set in 10 seconds.
        threading.Timer(10, self.set_exited_flag).start()
        self.basemonitor.request_exit(wait=True)
        self.assertTrue(self.basemonitor.should_exit)

class TestMonitor(unittest.TestCase):
    """
    This test class tests the features of the Monitor class in
    Tools/monitortools.py
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass

class TestSocketsMonitor(unittest.TestCase):
    """
    This test class tests the features of the SocketsMonitor class in
    Tools/monitortools.py
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass
