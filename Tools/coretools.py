#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Core Tools for the River System Control and Monitoring Software Version 0.9.1
# Copyright (C) 2017 Wimborne Model Town
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

import datetime
import sys
import os

def greet_and_get_filename(ModuleName, FileName):
    """
    Greets user and gets a file name for readings.
    Usage:

        file-obj GreetAndGetFilename(string ModuleName)
    """

    print("System Time: ", str(datetime.datetime.now()))
    print(ModuleName+" is running standalone.")
    print("Welcome. This program will quit automatically if you specified a number of readings, otherwise quit by pressing CTRL-C twice when you wish.\n")

    #Get filename, if one wasn't specified.
    if FileName == "Unknown":
        print("Please enter a filename to save the readings to.")
        print("This isn't a log file. The log file will be created automatically")
        print("and will store debugging information, whereas this file just stores")
        print("Readings.\n")
        print("The file will be appended to.")
        print("Make sure it's somewhere where there's plenty of disk space. Suggested: readings.txt")

        sys.stdout.write("Enter filename and press ENTER: ")

        FileName = input()

        print("\n\nSelected File: "+FileName)

        if os.path.isfile(FileName):
            print("*WARNING* This file already exists!")

        print("Press CTRL-C if you are not happy with this choice.\n")

        print("Press ENTER to continue...")

        input() #Wait until user presses enter.

    if os.path.isfile(FileName):
        print("*WARNING* The file chosen already exists!")

    try:
        print("Opening file...")
        RecordingsFile = open(FileName, "a",)

    except:
        #Bad practice :P
        print("Error opening file. Do you have permission to write there?")
        print("Exiting...")
        sys.exit()

    else:
        RecordingsFile.write("Start Time: "+str(datetime.datetime.now())+"\n\n")
        RecordingsFile.write("Starting to take readings...\n")
        print("Successfully opened file. Continuing..")

    return FileName, RecordingsFile
