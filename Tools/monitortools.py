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

import RPi.GPIO as GPIO
import time
import datetime
import sys
import getopt #Proper option handler.
import os
import threading

#NOTE: Can probably be refactored a bit with a base class, but don't do it prematurely.

# ---------- BASE CLASS ----------
class BaseMonitorClass(threading.Thread):
    def __init__(self, Probe, NumberOfReadingsToTake, ReadingInterval):
        self.Probe = Probe
        self.NumberOfReadingsToTake = NumberOfReadingsToTake
        self.ReadingInterval = ReadingInterval
        self.Queue = []
        self.Running = True

    def IsRunning(self):
        """
        Returns True if running, else False.
        Usage:
            bool IsRunning()
        """

        return self.Running

    def HasData(self):
        """
        Returns True if the queue isn't empty, False if it is.
        Usage:
            bool HasData()
        """

        return int(len(self.Queue))

    def GetReading(self):
        """
        Returns a reading from the queue, and deletes it from the queue.
        Usage:
            string GetReading()
        """

        return self.Queue.pop()

    def SetReadingInterval(self, Interval):
        """
        Sets the reading interval. Takes immediate effect.
        Usage:
            SetReadingInterval(int Interval)
        """

        self.ReadingInterval = Interval

# ---------- MONITOR THREAD FOR RESISTANCE PROBES ---------- 
class ResistanceProbeMonitor(BaseMonitorClass):
    def __init__(self, Probe, NumberOfReadingsToTake, ReadingInterval):
        """Initialise and start the thread"""
        BaseMonitorClass.__init__(self, Probe, NumberOfReadingsToTake, ReadingInterval)
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """Main part of the thread"""
        NumberOfReadingsTaken = 0

        try:
            while (self.NumberOfReadingsToTake == 0 or (NumberOfReadingsTaken < self.NumberOfReadingsToTake)):
                Level, StateText = self.Probe.GetLevel()

                self.Queue.append("Time: "+str(datetime.datetime.now())+" Level: "+str(Level)+"mm Pin states: "+StateText)

                NumberOfReadingsTaken += 1

                #Take readings every however often it is.
                #I know we could use a long time.sleep(), but this MUST be responsive to changes in the reading interval.
                Count = 0

                while Count < self.ReadingInterval:
                    #This way, if our reading interval changes, the code will respond to the change immediately.
                    time.sleep(1)
                    Count += 1

        except BaseException as E:
            #Ignore all errors. Generally bad practice :P
            print("\nCaught Exception: ", E)

        self.Running = False
        
# ---------- MONITOR THREAD FOR HALL EFFECT DEVICES ----------
class HallEffectMonitor(BaseMonitorClass):
    def __init__(self, Probe, NumberOfReadingsToTake, ReadingInterval):
        """Initialise and start the thread"""
        BaseMonitorClass.__init__(self, Probe, NumberOfReadingsToTake, ReadingInterval)
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """Main part of the thread"""
        NumberOfReadingsTaken = 0

        try:
            while (self.NumberOfReadingsToTake == 0 or (NumberOfReadingsTaken < self.NumberOfReadingsToTake)):
                RPM = self.Probe.GetRPM()

                #Add the reading to the queue.
                self.Queue.append("Time: "+str(datetime.datetime.now())+" RPM: "+str(RPM))

                NumberOfReadingsTaken += 1

                #Take readings every however often it is.
                #I know we could use a long time.sleep(), but this MUST be responsive to changes in the reading interval.
                Count = 0

                while Count < self.ReadingInterval:
                    #This way, if our reading interval changes, the code will respond to the change immediately.
                    time.sleep(1)
                    Count += 1

        except BaseException as E:
            #Ignore all errors. Generally bad practice :P
            print("\nCaught Exception: ", E)

        self.Running = False

# ---------- MONITOR THREAD FOR CAPACITIVE PROBES ----------
class CapacitiveProbeMonitor(BaseMonitorClass):
    def __init__(self, Probe, NumberOfReadingsToTake, ReadingInterval):
        """Initialise and start the thread"""
        BaseMonitorClass.__init__(self, Probe, NumberOfReadingsToTake, ReadingInterval)
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """Main part of the thread"""
        NumberOfReadingsTaken = 0

        try:
            while (self.NumberOfReadingsToTake == 0 or NumberOfReadingsTaken < self.NumberOfReadingsToTake):
                Freq = self.Probe.GetLevel()

                self.Queue.append("Time: "+str(datetime.datetime.now())+" Frequency: "+str(Freq))

                NumberOfReadingsTaken += 1

                #Take readings every however often it is.
                #I know we could use a long time.sleep(), but this MUST be responsive to changes in the reading interval.
                Count = 0

                while Count < self.ReadingInterval:
                    #This way, if our reading interval changes, the code will respond to the change immediately.
                    time.sleep(1)
                    Count += 1

        except BaseException as E:
            #Ignore all errors. Generally bad practice :P
            print("\nCaught Exception: ", E)

        self.Running = False

# ---------- MONITOR THREAD FOR FLOAT SWITCHES ----------
class FloatSwitchMonitor(BaseMonitorClass):
    def __init__(self, Probe, NumberOfReadingsToTake, ReadingInterval):
        """Initialise and start the thread"""
        BaseMonitorClass.__init__(self, Probe, NumberOfReadingsToTake, ReadingInterval)
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """Main part of the thread"""
        NumberOfReadingsTaken = 0

        try:
            while (self.NumberOfReadingsToTake == 0 or NumberOfReadingsTaken < self.NumberOfReadingsToTake):
                State = self.Probe.GetState()

                self.Queue.append("Time: "+str(datetime.datetime.now())+" State: "+str(State))

                NumberOfReadingsTaken += 1

                #Take readings every however often it is.
                #I know we could use a long time.sleep(), but this MUST be responsive to changes in the reading interval.
                Count = 0

                while Count < self.ReadingInterval:
                    #This way, if our reading interval changes, the code will respond to the change immediately.
                    time.sleep(1)
                    Count += 1

        except BaseException as E:
            #Ignore all errors. Generally bad practice :P
            print("\nCaught Exception: ", E)

        self.Running = False

