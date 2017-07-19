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

class Monitor(threading.Thread):
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
    from . import sensors

    import sensors.HallEffectDevice as HallEffectDevice

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

    print("System Time: ", str(datetime.datetime.now()))

    print("Welcome. This program will quit automatically if you specified a number of readings, otherwise quit with CTRL-C when you wish.\n")

    #Get filename.
    print("Please enter a filename to save the readings to.")
    print("Any existing file contents will be *OVERWRITTEN*.")
    print("Make sure it's somewhere where there's plenty of disk space. Suggested: readings.txt")
    sys.stdout.write("Enter filename and press ENTER: ")
    FileName = raw_input()

    print("\n\nSelected File: "+FileName)
    print("Press CTRL-C if you are not happy with this choice.\n")

    print("Press ENTER to continue...")
    raw_input() #Wait until user presses enter.

    try:
        print("Opening file...")
        RecordingsFile = open(FileName, "w")

    except:
        #Bad practice :P
        print("Error opening file. Do you have permission to write there?")
        print("Exiting...")
        sys.exit()

    else:
        RecordingsFile.write("Start Time: "+str(datetime.datetime.now())+"\n\n")
        RecordingsFile.write("Starting to take readings...\n")
        print("Successfully opened file. Continuing..")

    print("Starting to take readings. Please stand by...")

    #Create the probe object.
    Probe = ResistanceProbe("Probey")

    #Set the probe up.
    Probe.SetActiveState(False)     #Active low.
    Probe.SetPins((10, 11, 12, 13, 15, 16, 18, 19, 21, 22))

    #Holds the number of readings we've taken.
    NumberOfReadingsTaken = 0

    #Holds number of times we detect a falling edge in 5 seconds (for accuracy).
    Detections = 0

    #Holds the number of readings we've taken.
    NumberOfReadingsTaken = 0

    def Falling_Edge_Detected(channel):
        """Called when a falling edge is detected. Adds 1 to the number of falling edges detected"""
        global Detections
        Detections += 1

    #Automatically call our function when a falling edge is detected.
    GPIO.add_event_detect(10, GPIO.FALLING, callback=Falling_Edge_Detected)

    try:
        while (NumberOfReadingsToTake == 0 or NumberOfReadingsTaken < NumberOfReadingsToTake):
            Detections = 0
            time.sleep(5)

            #Use integer divison '//' because it's fast.
            RevsPer5Sec = Detections // 5 #Because we're measuring over 5 seconds, take the mean average over 5 seconds.

            #Then multiply by 12 to get RPM.
            RPM = RevsPer5Sec * 12

            print("Time: ", str(datetime.datetime.now()), ": "+str(RPM))
            RecordingsFile.write("Time: "+str(datetime.datetime.now())+" RPM: "+str(RPM)+"\n")

            NumberOfReadingsTaken += 1

    except BaseException as E:
        #Ignore all errors. Generally bad practice :P
        print("\nCaught Exception: ", E)

    finally:
        #Always clean up properly.
        print("Cleaning up...")

        #Stop calling our function.
        GPIO.remove_event_detect(10)

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
