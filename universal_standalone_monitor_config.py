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

try:
    #Wrap in a try block so we can generate documentation. FIXME Fix this later.
    import Tools
    from Tools import sensorobjects

except ImportError: pass

#FIXME: Pins MUST NOT conflict.

try:
    #As above.
    DATA = {
        #Probe Name: (Probe Object, Pin(s), Default Reading Interval)

        "Resistance Probe": (Tools.sensorobjects.ResistanceProbe, (15, 17, 27, 22, 23, 24, 10, 9, 25, 11), 300),
        "Hall Effect": (Tools.sensorobjects.HallEffectDevice, (15), 300),
        "Hall Effect Probe": (Tools.sensorobjects.HallEffectProbe, (15, 17, 27, 22, 23, 24, 10, 9, 25, 11), 10),
        "Capacitive Probe": (Tools.sensorobjects.CapacitiveProbe, (15), 300),
        "Float Switch": (Tools.sensorobjects.FloatSwitch, (8), 30),
    }

except: pass
