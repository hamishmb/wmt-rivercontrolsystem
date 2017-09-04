#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Float Switch Monitoring Tools for the River System Control and Monitoring Software Version 0.9.1
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
import threading
import logging

#NOTE: The usage function is shared between these standalone monitors, and is in standalone_shared_functions.py.

def RunStandalone():
    #Allows the progam to run standalone as well as being a module.
    #Do required imports.
    import Tools

    from Tools import standalone_shared_functions as functions
    from Tools import sensorobjects
    from Tools import monitortools
    from Tools import coretools as CoreTools
    from Tools import sockettools as SocketTools

    from Tools.sensorobjects import FloatSwitch
    from Tools.monitortools import Monitor

    Tools.sockettools.logger = logger

    #Handle cmdline options.
    FileName, ServerAddress, NumberOfReadingsToTake = functions.handle_cmdline_options("float_switch_monitor_standalone.py")

    #Connect to server, if any.
    if ServerAddress is not None:
        print("Initialising connection to server, please wait...")
        Socket = SocketTools.Sockets("Plug")
        Socket.SetPortNumber(30000)
        Socket.SetServerAddress(ServerAddress)
        Socket.StartHandler()

        #Wait until the socket is connected and ready.
        while not Socket.IsReady(): time.sleep(0.5)

        print("Done!")

    #Greet and get filename.
    FileName, RecordingsFile = CoreTools.greet_and_get_filename("Hall Effect Device Monitor", FileName)

    print("Starting to take readings. Please stand by...")

    #Create the switch object.
    Probe = FloatSwitch("Switchy")

    #Set the switch up.
    Probe.SetPin(8)

    #Holds the number of readings we've taken.
    NumberOfReadingsTaken = 0

    #Reading interval.
    ReadingInterval = 30

    #Start the monitor thread. Also wait a few seconds to let it initialise. This also allows us to take the first reading before we start waiting.
    MonitorThread = Monitor("Float Switch", Probe, NumberOfReadingsToTake, ReadingInterval=ReadingInterval)
    time.sleep(2)

    #Keep tabs on its progress so we can write new readings to the file.
    while MonitorThread.IsRunning():
        #Check for new readings.
        while MonitorThread.HasData():
            Reading = MonitorThread.GetReading()

            #Write any new readings to the file and to stdout.
            print(Reading)
            RecordingsFile.write(Reading+"\n")

            if ServerAddress is not None:
                Socket.Write(Reading)

        #Wait until it's time to check for another reading.
        time.sleep(ReadingInterval)

    #Always clean up properly.
    print("Cleaning up...")

    RecordingsFile.close()

    if ServerAddress is not None:
        Socket.RequestHandlerExit()
        Socket.WaitForHandlerToExit()
        Socket.Reset()

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
    logger = logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p', level=logging.WARNING)

    RunStandalone()
