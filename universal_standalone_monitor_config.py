#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Universal Standalone Monitor Config for the River System Control and Monitoring Software Version 0.9.1
# Copyright (C) 2017 Wimborne Model Town
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3 or,
# at your option, any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This is the configuration for the secondary part of the
software. It forms the config for the universal monitor
that is used on the slave/client pis. Universal in this
case means that this same program can be used for all of
the probes this software framework supports.

This essentially takes the form of a dictionary object
named "DATA" in the format:

>>> DATA = {
>>>     Probe Name: (Probe Object, Pin(s), Default Reading Interval),
>>>     Probe Name2: (Probe Object2, Pin(s), Default Reading Interval),
>>> }

The probe name forms the key, and has configuration for:

- "Resistance Probe"
- "Hall Effect" (water-wheel)
- "Hall Effect Probe"
- "Capacitive Probe"
- "Float Switch"

So, if you want configuration for
a capacitive probe, you can run:

>>> probe, pins, reading_interval = config.DATA["Capactive Probe"]

and for a hall effect device (NOT the probe), run:

>>> probe, pins, reading_interval = config.DATA["Hall Effect"]

There are no classes or functions defined in this file.

.. module:: universal_standalone_monitor_config.py
    :platform: Linux
    :synopsis: The configuration for the secondary part of the control software.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>

"""

import Tools
from Tools import sensorobjects

#FIXME: Pins MUST NOT conflict.

DATA = {
    #Probe Name: (Probe Object, Pin(s), Default Reading Interval)

    "Resistance Probe": (Tools.sensorobjects.ResistanceProbe, (15, 17, 27, 22, 23, 24, 10, 9, 25, 11), 300),
    "Hall Effect": (Tools.sensorobjects.HallEffectDevice, (15), 300),
    "Hall Effect Probe": (Tools.sensorobjects.HallEffectProbe, (15, 17, 27, 22, 23, 24, 10, 9, 25, 11), 10),
    "Capacitive Probe": (Tools.sensorobjects.CapacitiveProbe, (15), 300),
    "Float Switch": (Tools.sensorobjects.FloatSwitch, (8), 30),
}
