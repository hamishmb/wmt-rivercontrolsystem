#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Control Logic Unit Test Data for the River System Control and Monitoring Software
# Copyright (C) 2020-2022 Wimborne Model Town
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
from Tools import deviceobjects

class Dummy:
    """A dummy class that does nothing, just used for testing"""
    def __init__(self): pass

class Motor(deviceobjects.BaseDeviceClass):
    """A fake do-nothing Motor class, just used for testing"""
    def __init__(self, _id, _name):
        #Call the base class constructor.
        deviceobjects.BaseDeviceClass.__init__(self, _id, _name)

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

#Readings dictionary to hold fake readings for each sensor for sumppi control logic tests.
readings = {}

#Dictionary to hold devices that have been attempted to be controlled, and the state requested.
states = {}

#Dummy logiccoretools.attempt_to_control method for sumppi control logic.
def fake_attempt_to_control(site_id, sensor_id, request, retries=3):
    states[site_id+":"+sensor_id] = []
    states[site_id+":"+sensor_id].append(request)

#Dummy logiccoretools.update_status method for sumppi control logic.
def fake_update_status(pi_status, sw_status, current_action, retries=3):
    return True

#Dummy logiccoretools.get_latest_reading method for sumppi contro logic.
def fake_get_latest_reading(site_id, sensor_id):
    return readings[site_id+":"+sensor_id][-1]

class FakeGetState:
    """
    Provides a fake "logiccoretools.get_state" method, with the ability
    to control the return value by setting fake device control overrides.
    
    By default, there are no overrides applied. (Creating a simulation that
    nothing is trying to control any devices.)
    """
    def __init__(self):
        self.overrides = {}
    
    def _key(self, site_id, sensor_id):
        """Make a key for the overrides dictionary"""
        return str(site_id) + ":" + str(sensor_id)
    
    def set_override(self, site_id, sensor_id, value):
        """
        Sets a fake override on the given site_id:sensor_id, with the given
        value.
        
        To clear the override, set a value of None.
        """
        key = self._key(site_id, sensor_id)
        
        if value is None:
            del self.overrides[key]
        else:
            self.overrides[key] = str(value)
    
    def get_state(self, site_id, sensor_id, retries=3):
        """A fake "logiccoretools.get_state" method."""
        key = self._key(site_id, sensor_id)
        try:
            # Override; device control
            return ("Locked", self.overrides[key], "NAS")
        except KeyError:
            # No override; no device control
            return ("Unlocked", "None", "None")
