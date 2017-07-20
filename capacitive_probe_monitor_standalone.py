#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Hall Effect Device Monitoring Tools for the River System Control and Monitoring Software Version 1.0
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
import threading

def usage():
    #Only used when running standalone.
    print("\nUsage: capacitive_probe_monitor_standalone.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:               Show this help message")
    print("       -f, --file:               Specify file to write the recordings to. Default: interactive.")
    print("       -n <int>, --num=<int>     Specify number of readings to take before exiting. Without this option, readings will be taken until the program is terminated")
    print("capacitive_rpobe_monitor_standalone.py is released under the GNU GPL Version 3")
    print("Copyright (C) Wimborne Model Town 2017")

def RunStandalone():
    #Allows the progam to run standalone as well as being a module.
    #Do required imports.
    import Tools

    from Tools import sensorobjects
    from Tools import coretools as CoreTools

    from Tools.sensorobjects import CapacitiveProbe

    #Handle cmdline options.
    FileName, NumberOfReadingsToTake = CoreTools.HandleCmdlineOptions(usage)

    #Greet and get filename.
    RecordingsFile = CoreTools.GreetAndGetFilename("Hall Effect Device Monitor", FileName)

    print("Starting to take readings. Please stand by...")

    #Create the probe object.
    Probe = CapacitiveProbe("Probey")

    #Set the probe up.
    Probe.SetPin(10)

    #Holds the number of readings we've taken.
    NumberOfReadingsTaken = 0

    try:
        while (NumberOfReadingsToTake == 0 or NumberOfReadingsTaken < NumberOfReadingsToTake):
            Freq = Probe.GetLevel()

            print("Time: ", str(datetime.datetime.now()), ": "+str(Freq))
            RecordingsFile.write("Time: "+str(datetime.datetime.now())+" Frequency: "+str(Freq)+"\n")

            NumberOfReadingsTaken += 1

            #Wait five minutes between readings.
            time.sleep(300)

    except BaseException as E:
        #Ignore all errors. Generally bad practice :P
        print("\nCaught Exception: ", E)

    finally:
        #Always clean up properly.
        print("Cleaning up...")

        RecordingsFile.close()

        print("Calculating mean average...")
        RecordingsFile = open(FileName, "r")

        Sum = 0
        Count = 0

        #Sum up and keep count of readings.
        while True:
            Line = RecordingsFile.readline()

            if Line == "":
                #EOF.
                break

            try:
                Sum += int(Line.split()[4].replace("\n", ""))
                Count += 1

            except IndexError:
                #Will happen until we reach the lines with the readings.
                pass

        RecordingsFile.close()

        try:
            Mean = Sum / Count

        except ZeroDivisionError:
            Mean = 0

        #Write mean to file.
        RecordingsFile = open(FileName, "a")
        RecordingsFile.write("Mean Average: "+str(Mean))
        RecordingsFile.close()

        print("Mean: "+str(Mean))

        #Reset GPIO pins.
        GPIO.cleanup()

if __name__ == "__main__":
    RunStandalone()
