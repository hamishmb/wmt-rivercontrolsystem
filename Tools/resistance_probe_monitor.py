#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Resistance Probe Monitoring Tools for the River System Control and Monitoring Software Version 1.0
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

            #Take readings every 5 minutes.
            time.sleep(self.ReadingInterval)

def usage():
    #Only used when running standalone.
    print("\nUsage: resistance_probe_monitor.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:               Show this help message")
    print("       -f, --file:               Specify file to write the recordings to. Default: interactive.")
    print("       -n <int>, --num=<int>     Specify number of readings to take before exiting. Without this option, readings will be taken until the program is terminated")
    print("resistance_probe_monitor.py is released under the GNU GPL Version 3")
    print("Copyright (C) Wimborne Model Town 2017")

def RunStandalone():
    #Allows the progam to run standalone as well as being a module.
    #Do required imports.
    from . import objects

    import objects.ResistanceProbe as ResistanceProbe

    FileName = "Unknown"

    #Check all cmdline options are valid.
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:n:", ["help", "file=", "num="])

    except getopt.GetoptError as err:
        #Invalid option. Show the help message and then exit.
        #Show the error.
        print(unicode(err))
        usage()
        sys.exit(2)

    #Do setup. o=option, a=argument.
    NumberOfReadingsToTake = 0 #Take readings indefinitely by default.

    for o, a in opts:
        if o in ["-n", "--num"]:
            NumberOfReadingsToTake = int(a)

        elif o in ["-f", "--file"]:
            FileName = a

        elif o in ["-h", "--help"]:
            usage()
            sys.exit()
    
        else:
            assert False, "unhandled option"

    print("System Time: ", str(datetime.datetime.now()))

    print("Welcome. This program will quit automatically if you specified a number of readings, otherwise quit with CTRL-C when you wish.\n")

    #Get filename, if one wasn't specified.
    if FileName == "Unknown":
        print("Please enter a filename to save the readings to.")
        print("The file will be appended to.")
        print("Make sure it's somewhere where there's plenty of disk space. Suggested: readings.txt")

        sys.stdout.write("Enter filename and press ENTER: ")

        FileName = raw_input()

        print("\n\nSelected File: "+FileName)
        print("Press CTRL-C if you are not happy with this choice.\n")

        print("Press ENTER to continue...")

        raw_input() #Wait until user presses enter.

    try:
        #Use buffer size of 0 to disable Python's file buffer.
        print("Opening file...")
        RecordingsFile = open(FileName, "a", 0)

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

    #Don't use the thread here: it doesn't write to a file.
    try:
        while (NumberOfReadingsToTake == 0 or (NumberOfReadingsTaken < NumberOfReadingsToTake)):
            Level, StateText = Probe.GetLevel()

            print("Time: ", str(datetime.datetime.now()), "Level: "+str(Level), "mm. Pin states: "+StateText)
            RecordingsFile.write("Time: "+str(datetime.datetime.now())+" Level: "+str(Level)+"mm, Pin states: "+StateText+"\n")

            #Flush the system buffer.
            #Also flush Python's buffer just in case our buffer size argument didn't work as intended.
            RecordingsFile.flush()
            os.fsync(RecordingsFile.fileno())

            NumberOfReadingsTaken += 1

            #Take readings every 5 minutes.
            time.sleep(300)

    except BaseException as E:
        #Ignore all errors. Generally bad practice :P
        print("\nCaught Exception: ", E)

    finally:
        #Always clean up properly.
        print("Cleaning up...")

        RecordingsFile.close()

        #Reset GPIO pins.
        GPIO.cleanup()

if __name__ == "__main__":
    RunStandalone() 
