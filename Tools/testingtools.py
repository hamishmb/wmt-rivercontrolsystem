#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Testing Tools for the River System Control and Monitoring Software
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

"""
This module defines some testing classes and functions that simulate hardware, in order for the
control software to be run more easily in test deployments without real hardware, such as
in virtual machines.

The classes in this module override RPi.GPIO and parts of the adafruit_ads1x15.ads1115 module.

.. module:: testingtools.py
    :platform: Linux
    :synopsis: Allows the river control system to be run more easily in virtual machines.

.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>

"""

ads = 0

class GPIO:
    BCM = 0

    #Input and output.
    IN = 0
    OUT = 0

    #High and low.
    HIGH = 0
    LOW = 0

    #Falling and rising edges.
    FALLING = 0
    RISING = 0

    @classmethod
    def setup(cls, pin, mode):
        pass

    @classmethod
    def output(cls, pin, state):
        pass

    @classmethod
    def input(cls, pin):
        return True

    @classmethod
    def add_event_detect(cls, pin, mode, callback):
        pass

    @classmethod
    def remove_event_detect(cls, pin):
        pass

class ADS:
    #Pins.
    P0 = 0
    P1 = 0
    P2 = 0
    P3 = 0

    #Voltage.
    voltage = 0

    @classmethod
    def ADS1115(cls, i2c, address=None):
        pass

def AnalogIn(ads2, pin):
    return ADS
