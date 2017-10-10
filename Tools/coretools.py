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

def greet_and_get_filename(module_name, file_name):
    """
    Greets user and gets a file name for readings.
    Usage:

        file-obj GreetAndGetFilename(string module_name)
    """

    print("System Time: ", str(datetime.datetime.now()))
    print(module_name+" is running standalone.")
    print("Welcome. This program will quit automatically if you specified a number of readings.")
    print("otherwise quit by pressing CTRL-C when you wish.\n")

    #Get filename, if one wasn't specified.
    if file_name == "Unknown":
        print("Please enter a filename to save the readings to.")
        print("This isn't a log file. The log file will be created automatically")
        print("and will store debugging information, whereas this file just stores")
        print("Readings.\n")
        print("The file will be appended to.")
        print("Make sure it's somewhere where there's plenty of disk space.")

        sys.stdout.write("Enter filename and press ENTER: ")

        file_name = input()

        print("\n\nSelected File: "+file_name)

        if os.path.isfile(file_name):
            print("*WARNING* This file already exists!")

        print("Press CTRL-C if you are not happy with this choice.\n")

        print("Press ENTER to continue...")

        input() #Wait until user presses enter.

    if os.path.isfile(file_name):
        print("*WARNING* The file chosen already exists!")

    try:
        print("Opening file...")
        recordings_file_handle = open(file_name, "a")

    except BaseException as err:
        #Bad practice :P
        print("Error opening file. Do you have permission to write there?")
        print("Exiting...")
        sys.exit()

    else:
        recordings_file_handle.write("Start Time: "+str(datetime.datetime.now())+"\n\n")
        recordings_file_handle.write("Starting to take readings...\n")
        print("Successfully opened file. Continuing..")

    return file_name, recordings_file_handle

def do_control_logic(sump_reading, butts_reading, butts_pump, monitor, socket):
    """
    Decides what to do based on the readings.

    NOTE: At the moment, this is fine tuned for the was-August-now-September test deployment.

    Usage:
        do_control_logic(string sump_reading, string butts_reading, <sensor-obj> butts_pump, <monitorthread-obj> monitor)
    """

    #Handle errors when interpreting the readings.
    try:
        sump_reading = int(sump_reading.split()[4].replace("m", ""))
        butts_reading = butts_reading.split()[-3]

    except BaseException as err:
        logger.error("Error interpreting readings: "+str(err)+". This indicates a bug in the software. Trying to get new readings...")
        print("Error interpreting readings: "+str(err)+". This indicates a bug in the software.")
        print("Getting new readings to try and recover...")
        return

    if sump_reading > 600:
        #Adjusted to 600mm because the 700mm sensor on the probe is broken at the moment.
        #Level in the sump is getting high.
        #Pump some water to the butts if they aren't full.
        #If they are full, do nothing and let the sump overflow.
        logger.warning("Water level in the sump > 600mm!")
        print("Water level in the sump > 600mm!")

        if butts_reading == "False":
            #Pump to the butts.
            logger.warning("Pumping water to the butts...")
            print("Pumping water to the butts...")
            butts_pump.enable()

            logger.warning("Changing reading interval to 30 seconds so we can keep a close eye on what's happening...")
            print("Changing reading interval to 30 seconds so we can keep a close eye on what's happening...")

            reading_interval = 30

        else:
            #Butts are full. Do nothing, but warn user.
            butts_pump.disable()

            logger.warning("The water butts are full. Allowing the sump to overflow.")
            print("The water butts are full.")
            print("Allowing the sump to overflow.")

            logger.warning("Setting reading interval to 5 minutes...")
            print("Setting reading interval to 5 minutes...")
            reading_interval = 300

    elif sump_reading <= 600 and sump_reading >= 400:
        #Level in the sump is good.
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        logger.debug("Water level in the sump is good. Doing nothing...")
        print("Water level in the sump is good. (600 - 400mm inclusive) Doing nothing...")

        logger.debug("Setting reading interval to 5 minutes...")
        print("Setting reading interval to 5 minutes...")
        reading_interval = 300

    elif sump_reading == 300:
        #Level in the sump is getting low.
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        logger.warning("Water level in the sump is 300mm!")
        logger.warning("Waiting for water to come back from the butts before requesting human intervention...")

        print("Water level in the sump is 300mm!")
        print("Waiting for water to come back from the butts before requesting human intervention...")

        logger.warning("Setting reading interval to 1 minute so we can monitor more closely...")
        print("Setting reading interval to 1 minute so we can monitor more closely...")

        reading_interval = 60

        #We have no choice here but to wait for water to come back from the butts and warn the user.
        #^ Tap is left half-open.

    elif sump_reading == 200:
        #Level in the sump is very low!
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        logger.error("*** NOTICE ***: Water level in the sump is 200mm!")
        logger.error("*** NOTICE ***: HUMAN INTERVENTION REQUIRED: Please add water to the system.")

        print("*** NOTICE ***: Water level in the sump is 200mm!")
        print("*** NOTICE ***: HUMAN INTERVENTION REQUIRED: Please add water to the system.")

        logger.warning("Setting reading interval to 30 seconds for close monitoring...")
        print("Setting reading interval to 30 seconds for close monitoring...")

        reading_interval = 30

    else:
        #Level in the sump is critically low!
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        logger.critical("*** CRITICAL ***: Water level in the sump < 200mm!")
        logger.critical("*** CRITICAL ***: HUMAN INTERVENTION REQUIRED: Please add water to the system.")
        logger.critical("*** CRITICAL ***: The pump might be running dry RIGHT NOW!")

        print("*** CRITICAL ***: Water level in the sump < 200mm!")
        print("*** CRITICAL ***: HUMAN INTERVENTION REQUIRED: Please add water to the system.")
        print("*** CRITICAL ***: The pump might be running dry RIGHT NOW!")

        logger.critical("Setting reading interval to 15 seconds for super close monitoring...")
        print("Setting reading interval to 15 seconds for super close monitoring...")

        reading_interval = 15

    #Set the reading interval in the thread, and send it down the socket to the peer.
    monitor.set_reading_interval(reading_interval)
    socket.write("Reading Interval: "+str(reading_interval))

    return reading_interval
