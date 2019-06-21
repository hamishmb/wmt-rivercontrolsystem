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

#Sample values for the arguments to the BaseMonitorClass class constructor.
TEST_BASEMONITOR_DATA = [
    ["SUMP", "M0"],
    ["SUMP", "FS0"],
    ["G4", "TBD0"],
    ["G6", "FS0"],
    ["G6", "M1"]
]

#Bad sample values for the arguments to the BaseMonitorClass class constructor.
TEST_BASEMONITOR_BAD_DATA = [
    ["SUMP:", "M0"],
    [":SUMP", "FS0"],
    ["SU:MP", "FS0"],
    ["", "FS0"],
    ["::", "FS0"],
    ["G4", ":TBD0"],
    ["G6", "FS0:"],
    ["G6", "M:1"],
    ["G6", "M:1"],
    ["G6", ""],
    ["G6", ":"],
    ["G6", "::"],
]
