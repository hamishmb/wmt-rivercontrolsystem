#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Core Tools Unit Test Data for the River System Control and Monitoring Software
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

import datetime
import sys
import os

#Import other modules.
sys.path.insert(0, os.path.abspath('../../../')) #Need to be able to import the Tools module from here.

#This is needed for access to BaseDeviceClass, which our dummy classes extend from.
import Tools
import Tools.deviceobjects as device_objects

class Dummy:
    """A dummy class that does nothing, just used for testing"""
    def __init__(self): pass

class Motor(device_objects.BaseDeviceClass):
    """A fake do-nothing Motor class, just used for testing"""
    def __init__(self, _id, _name):
        #Call the base class constructor.
        device_objects.BaseDeviceClass.__init__(self, _id, _name)

        #Set some semi-private variables.
        self._state = False                  #Motor is initialised to be off.
        self._supports_pwm = False           #Assume we don't have PWM by default.
        self._pwm_pin = -1                   #Needs to be set.

    # ---------- OVERRIDES ----------
    def set_pins(self, pins, _input=False):
        pass

    # ---------- INFO SETTER METHODS ----------
    def set_pwm_available(self, pwm_available, pwm_pin=-1):
        self._supports_pwm = pwm_available
        self._pwm_pin = pwm_pin

    # ---------- INFO GETTER METHODS ----------
    def pwm_supported(self):
        return self._supports_pwm

    def is_enabled(self):
        """Testing function used to determine current state of Motor"""
        return self._state

    # ---------- CONTROL METHODS ----------
    def enable(self):
        self._state = True

        return True

    def disable(self):
        self._state = False

        return True

class Monitor:
    """A fake do-nothing Monitor class, just used for testing"""
    def __init__(self):
        self.reading_interval = 0

    #---------- GETTERS ----------
    def get_reading_interval(self):
        return self.reading_interval

    #---------- SETTERS ----------
    def set_reading_interval(self, reading_interval):
        self.reading_interval = reading_interval

class Sockets:
    """A fake do-nothing Sockets class, just used for testing"""
    def __init__(self):
        self.out_queue = []

    #---------- GETTERS ----------
    def get_queue(self):
        return self.out_queue

    def write(self, data):
        self.out_queue.append(data)

class FakeDatabase:
    @classmethod
    def cursor(cls):
        return cls

    @classmethod
    def execute(cls, query):
        pass

    @classmethod
    def commit(cls):
        pass

class FakeMysqlConnectionSuccess:
    @classmethod
    def connect(cls, host=None, port=None, user=None, passwd=None, connect_timeout=None, db=None):
        return FakeDatabase

class FakeMysqlConnectionFailure:
    @classmethod
    def connect(cls, host=None, port=None, user=None, passwd=None, connect_timeout=None, db=None):
        raise cls._exceptions.Error()

    class _exceptions(Exception):
        #NB: These are in the heirarchy defined by PEP 249:
        #https://www.python.org/dev/peps/pep-0249/#exceptions

        class Warning(Exception):
            pass

        class Error(Exception):
            pass

        class InterfaceError(Error):
            pass

        class DatabaseError(Error):
            pass

        class DataError(DatabaseError):
            pass

        class OperationalError(DatabaseError):
            pass

        class IntegrityError(DatabaseError):
            pass

        class InternalError(DatabaseError):
            pass

        class ProgrammingError(DatabaseError):
            pass

        class NotSupportedError(DatabaseError):
            pass

#Dummy get_state methods for testing DatabaseConnection.
def get_state_unlocked(site_id, sensor_id):
    return ("Unlocked", "None", "None")

def get_state_lockedbysumppi(site_id, sensor_id):
    return ("Locked", "None", "SUMP")

def get_state_lockedbybuttspi(site_id, sensor_id):
    return ("Locked", "None", "G4")

def get_state_unavailable(site_id, sensor_id):
    return None

#Dummy do_query method.
def fake_do_query(self, query, retries):
    self.in_queue.append(query)

    result = self.result
    self.result = None

    return result

#Dummy logiccoretools.attempt_to_control method for sumppi control logic.
def fake_attempt_to_control(site_id, sensor_id, request, retries=3):
    return True

#Dummy logiccoretools.update_status method for sumppi control logic.
def fake_update_status(pi_status, sw_status, current_action, retries=3):
    return True

#Sample values for the arguments to the Reading class constructor.
TEST_READING_DATA = [
    [str(datetime.datetime.now()), 0, "G4:M0", "400", "OK"],
    [str(datetime.datetime.now()), 1, "G4:M0", "400", "OK"],
    [str(datetime.datetime.now()), 56, "G4:M8", "450", "Fault Detected"],
    [str(datetime.datetime.now()), 728, "SUMP:M0", "475", "OK"],
    [str(datetime.datetime.now()), 0, "G6:FS0", "True", "OK"],
    [str(datetime.datetime.now()), 3, "G4:M2", "0", "OK"],
    [str(datetime.datetime.now()), 7, "G4:M1", "405", "OK"],
    [str(datetime.datetime.now()), 8885, "G2:M0", "440", "OK"],
    [str(datetime.datetime.now()), 34567, "SUMP:M1", "420", "OK"],
    [str(datetime.datetime.now()), 3856, "G2:M0", "876", "OK"],
    [str(datetime.datetime.now()), 3, "G5:M0", "854", "OK"],
    [str(datetime.datetime.now()), 2, "G9:M0", "925", "OK"]
]

#Bad sample values for the arguments to the Reading class constructor.
TEST_READING_BAD_DATA = [
    #Time is not converted to a string.
    [datetime.datetime.now(), 1, "G4:M0", "400", "OK"],

    #Invalid tick value.
    [str(datetime.datetime.now()), -1, "G4:M0", "400", "OK"],
    [str(datetime.datetime.now()), "1", "G4:M0", "400", "OK"],

    #Invalid ID.
    [str(datetime.datetime.now()), 1, "G4:M0:FS0", "400", "OK"],
    [str(datetime.datetime.now()), 1, "G4", "400", "OK"],
    [str(datetime.datetime.now()), 1, ":", "400", "OK"],
    [str(datetime.datetime.now()), 1, "::", "400", "OK"],

    #Invalid value (not a string).
    [str(datetime.datetime.now()), 1, "G4:M0", 400, "OK"],
    [str(datetime.datetime.now()), 1, "G4:M0", True, "OK"],

    #Invalid status (not a string).
    [str(datetime.datetime.now()), 1, "G4:M0", "400", 0],
    [str(datetime.datetime.now()), 1, "G4:M0", "400", True],
    [str(datetime.datetime.now()), 1, "G4:M0", "400", 7.8],
]

#Sample values for arguments to the DatabaseConnection._connect method.
TEST__CONNECT_BAD_DATA = [
    ["", "test", "0.1.0.0", 3306],
    ["user", "", "0.1.0.0", 3306],
    [2, "test", "0.1.0.0", 3306],
    ["user", False, "0.1.0.0", 3306],
    ["user", "test", "0.1.0.0", "3306"],
    ["user", "test", "0.1.0.0", True],
    ["user", "test", "0", 3306],
    ["user", "test", "notanip", 3306],
    ["user", "test", "0.0.0", 3306],
    ["test", "test", "0000", 3306],
    ["test", "test", "...", 3306],
    ["test", "test", "", 3306],
    ["", "test", {}, 3306],
]

#Sample values from the database when a reading has been requested.
TEST_GET_N_LATEST_READINGS_DATA = [
    [1, "M0", 5, "2019-10-11 14:12:37.725504", "400", "OK"],
    [2, "M0", 5, "2019-10-11 14:12:37.725504", "375", "OK"],
    [3, "M0", 5, "2019-10-11 14:12:37.725504", "350", "OK"],
    [4, "FS0", 5, "2019-10-11 14:12:37.725504", "True", "OK"],
    [5, "FS0", 5, "2019-10-11 14:12:37.725504", "False", "OK"],
    [6, "FS1", 5, "2019-10-11 14:12:37.725504", "True", "OK"],
    [7, "FS1", 5, "2019-10-11 14:12:37.725504", "False", "OK"],
]

#Sample mixed valid and invalid values from the database when a reading has been requested.
TEST_GET_N_LATEST_READINGS_BAD_DATA = [
    #This one is valid.
    [1, "M0", 5, "2019-10-11 14:12:37.725504", "400", "OK"],

    [2, 5, "2019-10-11 14:12:37.725504", "325", "OK"],
    [3, "M0", 5, "2019-10-11 14:12:37.725504", "300", "OK", "extraelem"],
    [4, "M0", "5", "2019-10-11 14:12:37.725504", "275", "OK"],

    #This one is valid.
    [5, "M0", 5, "2019-10-11 14:12:37.725504", "375", "OK"],

    [6, "M0", 5, "2019-10-11 14:12:37.725504", 250, "OK"],

    #This one is valid.
    [7, "M0", 5, "2019-10-11 14:12:37.725504", "350", "OK"],

    [8, "M0", 5, "225", "OK"],
    [9, "M1", 5, "2019-10-11 14:12:37.725504", "200", "OK"],
]

#Sample values from the datavase when a state has been requested.
TEST_GET_STATE_DATA = [
    [[1, "P1", "Locked", "On", "SUMP"]],
    [[2, "P1", "Locked", "Off", "SUMP"]],
    [[3, "P1", "Unlocked", "None", "None"]],
    [[4, "P1", "Locked", "On", "G4"]],
]

#Sample values for arguments to the DatabaseConnection.attempt_to_control and release_control methods.
TEST_ATTEMPT_TO_CONTROL_DATA = [
    ["SUMP", "P0", "On"],
    ["SUMP", "P0", "Off"],
    ["SUMP", "P1", "On"],
    ["SUMP", "P1", "Off"],
    ["VALVE4", "V4", "1%"],
    ["VALVE4", "V4", "2%"],
    ["VALVE4", "V4", "3%"],
    ["VALVE4", "V4", "4%"],
    ["VALVE4", "V4", "5%"],
    ["VALVE4", "V4", "6%"],
    ["VALVE4", "V4", "7%"],
    ["VALVE4", "V4", "8%"],
    ["VALVE4", "V4", "9%"],
    ["VALVE4", "V4", "10%"],
    ["VALVE4", "V4", "11%"],
]

#Bad sample values for arguments to the DatabaseConnection.attempt_to_control method.
TEST_ATTEMPT_TO_CONTROL_BAD_DATA = [
    ["SMP", "P0", "On"],
    ["test", "P0", "Off"],
    ["", "P1", "On"],
    [3, "P1", "Off"],
    [True, "V4", "1%"],
    ["VALVE4", "", "2%"],
    ["VALVE4", "P4", 3],
    ["VALVE4", "V4", 12.4],
    ["VALVE4", "V4", {}],
    ["VALVE4", {}, "6%"],
    [(), "V4", "7%"],
    ["VALVE4", None, "8%"],
    [[], "V4", "9%"],
    [False, "V4", True],
    ["VALVE4", "V4", None],
]

#Bad sample values for arguments to the DatabaseConnection.release_control method.
TEST_RELEASE_CONTROL_BAD_DATA = [
    ["SMP", "P0"],
    ["test", "P0"],
    ["", "P1"],
    [3, "P1"],
    [True, "V4"],
    ["V4", ""],
    ["VALVE4", "P4"],
    ["VALVE4", {}],
    [(), "V4"],
    ["VALVE4", None],
    [[], "V4"],
    [False, "V4"],
    [3.14, "V4"],
]
