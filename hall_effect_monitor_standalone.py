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
    print("\nUsage: hall_effect_monitor.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:    Show this help message")
    print("       <integer>      Specify number of readings to take before exiting. Without this option, readings will be taken until the program is terminated")
    print("hall_effect_monitor.py is released under the GNU GPL Version 3")
    print("Copyright (C) Wimborne Model Town 2017")

def RunStandalone():
    #Allows the progam to run standalone as well as being a module.
    #Do required imports.
    import Tools

    from Tools import sensors
    from Tools import core as CoreTools

    from Tools.sensors import HallEffectDevice

    #Check all cmdline options are valid and do setup.
    try:
        if len(sys.argv) == 1:
            #No extra options specified. Nothing to do.
            NumberOfReadingsToTake = 0 #Take readings indefinitely.

        elif sys.argv[1] in ("-h", "--help"):
            usage()
            sys.exit()

        elif sys.argv[1].isdigit():
            NumberOfReadingsToTake = int(sys.argv[1])

        else:
            raise RuntimeError

    except RuntimeError:
        usage()
        print("Invalid option. Exiting...")
        sys.exit()

    #Greet and get filename.
    RecordingsFile = CoreTools.GreetAndGetFilename("Hall Effect Device Monitor", FileName)

    print("Starting to take readings. Please stand by...")

    #Create the probe object.
    Probe = HallEffectDevice("Probey")

    #Set the probe up.
    Probe.SetPin(10)

    #Holds the number of readings we've taken.
    NumberOfReadingsTaken = 0

    try:
        while (NumberOfReadingsToTake == 0 or NumberOfReadingsTaken < NumberOfReadingsToTake):
            RPM = Probe.GetRPM()

            print("Time: ", str(datetime.datetime.now()), ": "+str(RPM))
            RecordingsFile.write("Time: "+str(datetime.datetime.now())+" RPM: "+str(RPM)+"\n")

            NumberOfReadingsTaken += 1

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
