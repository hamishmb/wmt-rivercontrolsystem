#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Device Objects Unit Test Data for the River System Control and Monitoring Software
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

#Import other modules.
sys.path.append('../..') #Need to be able to import the Tools module from here.

#Define dummy GPIO class for testing.
class GPIO:
    #Constants.
    IN = 1
    OUT = 1
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

#Dummy ManageHallEffectProbe class for testing.
class ManageHallEffectProbe:
    def __init__(self, probe):
        pass

#Dummy ManageGateValve class for testing.
class ManageGateValve:
    position = 0

    def __init__(self, valve, i2c_address):
        pass

    def get_current_position(self):
        return self.position

    def set_position(self, pos):
        self.position = pos

#Sample arguments for the BaseDeviceClass constructor.
TEST_BASEDEVICECLASS_NONAME_DATA = [
    ["G4:FS0"],
    ["G6:M0"],
    ["SUMP:FS0"],
    ["V4:V4"]
]


TEST_BASEDEVICECLASS_DATA = [
    ["G4:FS0", "Wendy Butts Float Switch"],
    ["G6:M0", "Stage Butts Magnetic Probe"],
    ["SUMP:FS0", "Sump Float Switch"],
    ["V4:V4", "Gate Valve V4"]
]

TEST_BASEDEVICECLASS_BAD_DATA = [
    ["G4:", "Wendy Butts Float Switch"],
    [":G4", "Wendy Butts Float Switch"],
    [":", "Wendy Butts Float Switch"],
    ["", "Wendy Butts Float Switch"],
    [2, "Wendy Butts Float Switch"],
    ["::", "Wendy Butts Float Switch"],
    ["G6:M0", ""],
    ["SUMP:FS0", 1],
    ["V4", True],
    [False, "Test"]
]

#Sample arguments for BaseDeviceClass.get_pins()
TEST_BASEDEVICECLASS_GETPINS_DATA = list(range(2, 28))

TEST_BASEDEVICECLASS_GETPINS_BAD_DATA = [
    "0", 6.7, False, 0, 1, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, -1, -2, -3, -4, -5, -7, -8, -9, -10
]

#Sample arguments for Motor.set_pwm_available()
TEST_MOTOR_SETPWMAVAILABLE_DATA = [
    [False, None],
    [False, -1],
    [True, 3],
    [True, 17]
]

TEST_MOTOR_SETPWMAVAILABLE_BAD_DATA = [
    ["bob", -1],
    [[], -1],
    [0, -1],
    [False, 7],
    [False, -60],
    [True, None],
    [True, -1],
    [True, 78],
    [True, -5]
]

#Sample arguments for HallEffectProbe.set_limits()
TEST_HALLEFFECTPROBE_SETLIMITS_DATA = [
    [(0.07, 0.17, 0.35, 0.56, 0.73, 0.92, 1.22, 1.54, 2.1, 2.45),
     (0.05, 0.15, 0.33, 0.53, 0.7, 0.88, 1.18, 1.5, 2, 2.4)],

    [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
     (0.09, 0.19, 0.29, 0.39, 0.49, 0.59, 0.69, 0.79, 0.89, 0.99)],

    [(10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0),
     (9.0, 19.0, 29.0, 39.0, 49.0, 59.0, 69.0, 79.0, 89.0, 99.0)]
]

TEST_HALLEFFECTPROBE_SETLIMITS_BAD_DATA = [
    #Too short, must be 10 floats/ints long.
    [(0.07, 0.17, 0.35, 0.56, 0.73, 0.92, 1.22, 1.54, 2.1),
     (0.05, 0.15, 0.33, 0.53, 0.7, 0.88, 1.18, 1.5, 2)],

    #Not all floats or ints.
    [(0.1, 0.2, True, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1),
     (0.09, 0.19, 0.29, 0.39, 0.49, 0.59, False, 0.79, 0.89, 0.99)],

    #High limits are below low limits.
    [(9, 19, 29, 39, 49, 59, 69, 79, 89, 99),
     (10, 20, 30, 40, 50, 60, 70, 80, 90, 100)],

    #Only one list.
    [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0), ()],

    #Empty lists.
    [(), ()],

    #Not lists.
    [1, 2]
]

#Sample arguments for HallEffectProbe.set_depths()
TEST_HALLEFFECTPROBE_SETDEPTHS_DATA = [
    [(0, 100, 200, 300, 400, 500, 600, 700, 800, 900),
     (25, 125, 225, 325, 425, 525, 625, 725, 825, 925),
     (50, 150, 250, 350, 450, 550, 650, 750, 850, 950),
     (75, 175, 275, 375, 475, 575, 675, 775, 875, 975)],

    [(100, 200, 300, 400, 500, 600, 700, 800, 900, 1000),
     (125, 225, 325, 425, 525, 625, 725, 825, 925, 1025),
     (150, 250, 350, 450, 550, 650, 750, 850, 950, 1050),
     (175, 275, 375, 475, 575, 675, 775, 875, 975, 1075)],

    [(200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100),
     (225, 325, 425, 525, 625, 725, 825, 925, 1025, 1125),
     (250, 350, 450, 550, 650, 750, 850, 950, 1050, 1150),
     (275, 375, 475, 575, 675, 775, 875, 975, 1075, 1175)],
]

TEST_HALLEFFECTPROBE_SETDEPTHS_BAD_DATA = [
    #Not all 10 depths long.
    [(0, 100, 200, 300, 400, 500, 600, 700, 800),
     (25, 125, 225, 325, 425, 525, 625, 725, 825, 925),
     (50, 150, 250, 350, 450, 550, 650, 750, 850, 950, 1050),
     (75, 175, 275, 375, 475, 575, 675, 775, 875, 975)],

    #Not all integers.
    [(100, 200, 300, 400.0, 500, 600, 700, 800, 900, 1000),
     (125, 225, 325, 425, 525, True, 725, 825, 925, 1025),
     (150, 250, 350, [], 550, 650, 750, 850, 950, 1050),
     (175, 275, 375, 475, 575, 675, 775, {}, 975, 1075)],

    #Values correct, but in wrong order.
    [(250, 350, 450, 550, 650, 750, 850, 950, 1050, 1150),
     (275, 375, 475, 575, 675, 775, 875, 975, 1075, 1175),
     (200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100),
     (225, 325, 425, 525, 625, 725, 825, 925, 1025, 1125)],

    #Values don't make sense, not on the 100, 25s, 50s etc..
    [(201, 300, 400, 500, 600, 700, 800, 900, 10, 1100),
     (245, 325, 425, 525, 625, 725, 825, 925, 1025, 1125),
     (250, 358, 450, 550, 650, 750, 852, 950, 1550, 1150),
     (275, 375, 475, 575, 675, 775, 875, 975, 1075, 1175)],

    #Not all lists.
    [(200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100),
     True,
     (250, 350, 450, 550, 650, 750, 850, 950, 1050, 1150),
     1175],

    #Empty.
    [(), (), (), ()]
]

#Sample arguments for the GateValve constructor.
TEST_GATEVALVE_DATA = [
    #ID, Name, Pins, Tolerance, Max, Min, Voltage
    ["V4", "Test", (2, 3, 4), 5, 99, 10, 2.0],
    ["V5", "Test", (3, 4, 5), 6, 98, 9, 2.1],
    ["V1", "Test", (5, 6, 7), 7, 97, 8, 2.2],
    ["V2", "Test", (6, 7, 8), 8, 96, 7, 2.3],
    ["V3", "Test", (7, 8, 9), 9, 95, 6, 2.4],
    ["V6", "Test", (8, 9, 10), 1, 94, 5, 2.5],
    ["V7", "Test", (9, 10, 11), 2, 93, 9, 2.6],
    ["V8", "Test", (10, 11, 12), 3, 92, 9, 2.7],
    ["V9", "Test", (11, 12, 13), 4, 91, 9, 2.8],
    ["V10", "Test", (12, 13, 14), 6, 90, 9, 2.9],
    ["V11", "Test", (13, 14, 15), 6, 98, 9, 3],
    ["V12", "Test", (14, 15, 16), 6, 98, 9, 3.1],
    ["V13", "Test", (2, 4, 5), 6, 98, 9, 3.2],
    ["V14", "Test", (6, 4, 5), 6, 98, 9, 3.3],
    ["V15", "Test", (9, 4, 5), 6, 98, 9, 4.1],
    ["V16", "Test", (19, 4, 5), 6, 98, 9, 3.7],
    ["V17", "Test", (3, 12, 6), 6, 98, 9, 5.5]
]

TEST_GATEVALVE_BAD_DATA = [
    #ID, Name, Pins, Tolerance, Max, Min, Voltage
    #Invalid pins.
    ["V4", "Test", (0, 3, -4), 5, 99, 10, 2.0],
    ["V5", "Test", (3, 4, -5), 6, 98, 9, 2.1],
    ["V1", "Test", (5, 6), 7, 97, 8, 2.2],
    ["V2", "Test", (), 8, 96, 7, 2.3],
    ["V3", "Test", True, 9, 95, 6, 2.4],

    #Invalid values for Tolerance.
    ["V6", "Test", (8, 9, 10), 0, 94, 5, 2.5],
    ["V7", "Test", (9, 10, 11), -18, 93, 9, 2.6],
    ["V8", "Test", (10, 11, 12), True, 92, 9, 2.7],
    ["V9", "Test", (11, 12, 13), 15, 91, 9, 2.8],
    ["V10", "Test", (12, 13, 14), 11.7, 90, 9, 2.9],
    ["V11", "Test", (13, 14, 15), {}, 98, 9, 3],

    #Invalid values for Max Open.
    ["V12", "Test", (14, 15, 16), 6.4, 89, 9, 3.1],
    ["V13", "Test", (2, 4, 5), 6, 100, 9, 3.2],
    ["V14", "Test", (6, 4, 5), 6, -98, 9, 3.3],
    ["V15", "Test", (9, 4, 5), 6, 50, 9, 4.1],
    ["V16", "Test", (19, 4, 5), 6, False, 9, 3.7],

    #Invalid values for Min Open.
    ["V17", "Test", (3, 12, 6), 6, 98, 0, 5.5],
    ["V17", "Test", (3, 12, 6), 6, 98, 11, 5.5],
    ["V17", "Test", (3, 12, 6), 6, 98, 60, 5.5],
    ["V17", "Test", (3, 12, 6), 6, 98, -78, 5.5],
    ["V17", "Test", (3, 12, 6), 6, 98, {}, 5.5],
    ["V17", "Test", (3, 12, 6), 6, 98, 9.5, 5.5],

    #Invalid values for Reference Voltage.
    ["V17", "Test", (3, 12, 6), 6, 98, 9, -5.5],
    ["V17", "Test", (3, 12, 6), 6, 98, 9, 1.9],
    ["V17", "Test", (3, 12, 6), 6, 98, 9, 5.6],
    ["V17", "Test", (3, 12, 6), 6, 98, 9, False],
    ["V17", "Test", (3, 12, 6), 6, 98, 9, ()],

]
