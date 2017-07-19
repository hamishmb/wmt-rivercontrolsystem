#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Monitoring Tools for the River System Control and Monitoring Software Version 1.0
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

#Do future imports to support running on python 2 as well. Python 3 is the default. Use unicode strings rather than ASCII strings, as they fix potential problems.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import RPi.GPIO as GPIO
import time
import datetime
import sys
import getopt #Proper option handler.
import os
import threading

# ---------- MONITOR THREAD FOR RESISTANCE PROBES ---------- 
class ResistanceProbeMonitor(threading.Thread):
    def __init__(self, Probe, NumberOfReadingsToTake, ReadingInterval):
        """Initialise and start the thread"""
        self.Probe = Probe
        self.NumberOfReadingsToTake = NumberOfReadingsToTake
        self.ReadingInterval = ReadingInterval

        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """Main part of the thread"""
        NumberOfReadingsTaken = 0

        while (self.NumberOfReadingsToTake == 0 or (NumberOfReadingsTaken < self.NumberOfReadingsToTake)):
            Level, StateText = self.Probe.GetLevel()

            print("Time: ", str(datetime.datetime.now()), "Level: "+str(Level), "mm. Pin states: "+StateText) #TODO Add to message queue, or something else useful.

            NumberOfReadingsTaken += 1

            #Take readings every however often it is.
            time.sleep(self.ReadingInterval)

# ---------- MONITOR THREAD FOR HALL EFFECT DEVICES ----------
class HallEffectMonitor(threading.Thread):
    def __init__(self, Probe, NumberOfReadingsToTake, ReadingInterval):
        """Initialise and start the thread"""
        self.Probe = Probe
        self.NumberOfReadingsToTake = NumberOfReadingsToTake
        self.ReadingInterval = ReadingInterval

        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """Main part of the thread"""
        NumberOfReadingsTaken = 0

        while (self.NumberOfReadingsToTake == 0 or (NumberOfReadingsTaken < self.NumberOfReadingsToTake)):
            Level, StateText = self.Probe.GetLevel()

            print("Time: ", str(datetime.datetime.now()), "Level: "+str(Level), "mm. Pin states: "+StateText) #TODO Add to message queue, or something else useful.

            NumberOfReadingsTaken += 1

            #Take readings every however often it is.
            time.sleep(self.ReadingInterval)
