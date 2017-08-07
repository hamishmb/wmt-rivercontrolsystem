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

import RPi.GPIO as GPIO
import time
import datetime
import sys
import getopt #Proper option handler.
import os
import threading
import logging

def usage():
    #Only used when running standalone.
    print("\nUsage: resistance_probe_monitor_standalone.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:               Show this help message")
    print("       -f, --file:               Specify file to write the recordings to. Default: interactive.")
    print("       -c, --controlleraddress:  Specify the DNS name/IP of the controlling server we want to send our level data to, if any.")
    print("       -n <int>, --num=<int>     Specify number of readings to take before exiting. Without this option, readings will be taken until the program is terminated")
    print("resistance_probe_monitor_standalone.py is released under the GNU GPL Version 3")
    print("Copyright (C) Wimborne Model Town 2017")

def RunStandalone():
    #Allows the progam to run standalone as well as being a module.
    #Do required imports.
    import Tools

    from Tools import sensorobjects
    from Tools import monitortools
    from Tools import coretools as CoreTools
    from Tools import sockettools as SocketTools

    from Tools.sensorobjects import ResistanceProbe
    from Tools.monitortools import ResistanceProbeMonitor

    Tools.sockettools.logger = logger

    #Handle cmdline options.
    FileName, ServerAddress, NumberOfReadingsToTake = CoreTools.HandleCmdlineOptions(usage)

    #Connect to server, if any.
    if ServerAddress is not None:
        print("Initialising connection to server, please wait...")
        Socket = SocketTools.Sockets("Plug")
        Socket.SetPortNumber(30000)
        Socket.SetServerAddress("localhost")
        Socket.StartHandler()

        #Wait until the socket is connected and ready.
        while not Socket.IsReady(): time.sleep(0.5)

        print("Done!")

    #Greet and get filename.
    FileName, RecordingsFile = CoreTools.GreetAndGetFilename("Resistance Probe Monitor", FileName)

    print("Starting to take readings. Please stand by...")

    #Create the probe object.
    Probe = ResistanceProbe("Probey")

    #Set the probe up.
    Probe.SetActiveState(False)     #Active low.
    Probe.SetPins((15, 17, 18, 27, 22, 23, 24, 10, 9, 25))

    #Holds the number of readings we've taken.
    NumberOfReadingsTaken = 0

    #Reading interval.
    ReadingInterval = 300

    #Start the monitor thread. Also wait a few seconds to let it initialise. This also allows us to take the first reading before we start waiting.
    MonitorThread = ResistanceProbeMonitor(Probe, NumberOfReadingsToTake, ReadingInterval=ReadingInterval)
    time.sleep(10)

    #Keep tabs on its progress so we can write new readings to the file.
    while MonitorThread.IsRunning():
        #Check for new readings.
        while MonitorThread.HasData():
            Reading = MonitorThread.GetReading()

            #Write any new readings to the file and to stdout.
            print(Reading)
            RecordingsFile.write(Reading)

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

    #Reset GPIO pins.
    GPIO.cleanup()

if __name__ == "__main__":
    logger = logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p', level=logging.WARNING)

    RunStandalone() 
