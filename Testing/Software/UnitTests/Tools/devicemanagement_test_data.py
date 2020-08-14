#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Device Management Unit Test Data for the River System Control and Monitoring Software
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

import sys
import os

#Import other modules.
sys.path.insert(0, os.path.abspath('../../../')) #Need to be able to import the Tools module from here.

#Variables for test methods.
voltages_position = 0

#Define dummy GPIO class for testing.
class GPIO:
    #Constants.
    IN = 1
    OUT = 1
    LOW = 1
    HIGH = 1
    FALLING = 1
    RISING = 1

    #Class variables.
    state = False
    num_events = 0

    #Dummy functions
    def setup(pin, mode):
        pass

    @classmethod
    def input(cls, pin):
        #This returns True and False, alternating each time.
        #Change state for next time.
        cls.state = not cls.state

        #Return the current state.
        return not cls.state

    def output(pin, value):
        pass

    @classmethod
    def add_event_detect(cls, pin, edge, callback):
        for i in range(0, cls.num_events):
            callback("bob")

    def remove_event_detect(pin):
        pass

#Define two dummy ADC classes for testing.
class ADS:
    def ADS1115(i2c, address):
        pass

    #Constants.
    P0 = 0
    P1 = 0
    P2 = 0
    P3 = 0

    voltage = 1

    def ADS1115(i2c, address):
        pass

class ADS2:
    #Constants.
    P0 = 0
    P1 = 0
    P2 = 0
    P3 = 0

    @property
    def voltage(self):
        raise OSError("Test class; Always throws OSError")

#Define dummy AnalogIn functions for testing.
def AnalogIn(ads, pin):
    return ADS()

def AnalogIn2(ads, pin):
    return ADS2()

#Define dummy start function for testing.
def start(self):
    pass

#Define dummy get_compensated_probe_voltages function for testing.
def get_compensated_probe_voltages():
    try:
        return TEST_MANAGEHALLEFFECTPROBE_COMP_VOLTAGES_RESULTS[voltages_position]

    except IndexError:
        #No more test data.
        return ([0.0, 0.0, 0.0, 0.0], 0)

#Helper function to get corresponding result after running the above function.
def get_level_result():
    try:
        return TEST_MANAGEHALLEFFECTPROBE_GET_LEVEL_RESULTS[voltages_position]

    except IndexError:
        raise RuntimeError("No more test data")

#Sample limits for the HallEffectProbe class so we can test our test_levels() method.
#Note: These are *NOT* the same as the real values from config.py.
HIGH_LIMITS = (0.07, 0.17, 0.35, 0.56, 0.73, 0.92, 1.4, 1.9, 2.1, 2.45)
LOW_LIMITS = (0.05, 0.15, 0.33, 0.53, 0.7, 0.88, 1.18, 1.5, 2, 2.4)

DEPTHS = [
     (0, 100, 200, 300, 400, 500, 600, 700, 800, 900),
     (25, 125, 225, 325, 425, 525, 625, 725, 825, 925),
     (50, 150, 250, 350, 450, 550, 650, 750, 850, 950),
     (75, 175, 275, 375, 475, 575, 675, 775, 875, 975)
]

#Sample channel values for ManageHallEffectProbe.get_compensated_probe_voltages.
#(these must be kept in the same order)
TEST_MANAGEHALLEFFECTPROBE_COMP_VOLTAGES = [
    #chan0, chan1, chan2, chan3.
    (3.0, 3.0, 3.0, 3.0),
    (3.0, 3.0, 3.0, 3.5),
    (1.0, 3.0, 3.0, 3.0),
    (1.5, 3.0, 2.5, 3.0),
    (3.0, 1.0, 0.5, 3.0),
    (3.0, 0.2, 3.0, 3.0),
    (3.0, 3.0, 3.0, 1.45)
]

#Sample expected results for ManageHallEffectProbe.get_compensated_probe_voltages, given the above values.
#(these must be kept in the same order)
TEST_MANAGEHALLEFFECTPROBE_COMP_VOLTAGES_RESULTS = [
    #compensated voltage, min column
    #Between levels.
    ([0.0, 0.0, 0.0, 0.0], 0),

    #Note: This is a weird one, because the voltage should always be below 3v anyway, it seems.
    #100-175mm, with fault (somewhat undefined behaviour).
    ([0.16666666666666652, 0.16666666666666652, 0.16666666666666652, 0.16666666666666652], 0),

    #800mm.
    ([2.0, 0.0, 0.0, 0.0], 0),

    #600mm.
    ([1.3333333333333335, 0.0, 0.0, 0.0], 0),

    #750mm.
    ([0.0, 0.0, 1.8333333333333335, 0.0], 2),

    #Between levels - possible fault.
    ([0.0, 2.8, 0.0, 0.0], 1),

    #775mm
    ([0.0, 0.0, 0.0, 1.55], 3)
]

#Expected levels for the above results.
#NB: Omm and between levels are reported as 1000 by this method (corrected later by
#the thread).
TEST_MANAGEHALLEFFECTPROBE_GET_LEVEL_RESULTS = [
    -1,
    100,
    800,
    600,
    750,
    -1,
    775
]
