#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Core Tools Unit Test Data for the River System Control and Monitoring Software
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

import datetime
import sys

#Import other modules.
sys.path.append('../..') #Need to be able to import the Tools module from here.

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
