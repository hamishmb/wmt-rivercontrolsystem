#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Universal Standalone Monitor for the River System Control and Monitoring Software Version 0.9.1
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
import logging

#NOTE: The usage function is shared between these standalone monitors, and is in standalone_shared_functions.py.

def RunStandalone():
    #Do required imports.
    import universal_standalone_monitor_config as config

    import Tools

    from Tools import standalone_shared_functions as functions
    from Tools import sensorobjects
    from Tools import coretools as CoreTools
    from Tools import sockettools as SocketTools
    from Tools import monitortools

    from Tools.sensorobjects import CapacitiveProbe
    from Tools.monitortools import Monitor

    Tools.sockettools.logger = logger

    #Handle cmdline options.
    _type, FileName, ServerAddress, NumberOfReadingsToTake = functions.handle_cmdline_options("universal_standalone_monitor.py")

    logger.debug("Running in "+_type+" mode...")

    #Connect to server, if any.
    if ServerAddress is not None:
        logger.info("Initialising connection to server, please wait...")
        print("Initialising connection to server, please wait...")
        Socket = SocketTools.Sockets("Plug")
        Socket.SetPortNumber(30000)
        Socket.SetServerAddress(ServerAddress)
        Socket.StartHandler()

        logger.info("Will connect to server as soon as it becomes available.")
        print("Will connect to server as soon as it becomes available.")

    #Greet and get filename.
    logger.info("Greeting user and asking for filename if required...")
    FileName, RecordingsFile = CoreTools.greet_and_get_filename("Universal Monitor ("+_type+")", FileName)
    logger.info("File name: "+FileName+"...")

    #Get settings for this type of monitor from the config file.
    logger.info("Asserting that the specified type is valid...")
    assert _type in config.DATA, "Invalid Type Specified"

    probe, pins, reading_interval = config.DATA[_type]

    logger.info("Setting up the probe...")

    #Create the probe object.
    probe = probe("Probey")

    #Set the probe up.
    probe.SetPins(pins)

    #Holds the number of readings we've taken.
    NumberOfReadingsTaken = 0

    logger.info("Starting the monitor thread...")
    print("Starting to take readings. Please stand by...")

    #Start the monitor thread.
    MonitorThread = Monitor(_type, probe, NumberOfReadingsToTake, ReadingInterval=reading_interval)

    #Wait until the first reading has come in so we are synchronised.
    while not MonitorThread.HasData():
        time.sleep(0.5)

    logger.info("You should begin to see readings now...")

    #Keep tabs on its progress so we can write new readings to the file.
    try:
        while MonitorThread.IsRunning():
            #Check for new readings.
            while MonitorThread.HasData():
                Reading = MonitorThread.GetReading()

                #Write any new readings to the file and to stdout.
                logger.info("New reading: "+Reading)
                print(Reading)
                RecordingsFile.write(Reading+"\n")

                if ServerAddress is not None:
                    Socket.Write(Reading)

            #Wait until it's time to check for another reading.
            time.sleep(reading_interval)

    except KeyboardInterrupt:
        #Ask the thread to exit.
        logger.info("Caught keyboard interrupt. Asking monitor thread to exit...")
        print("Caught keyboard interrupt. Asking monitor thread to exit.")
        print("This may take a little while, so please be patient...")

        MonitorThread.RequestExit(wait=True)

    #Always clean up properly.
    logger.info("Cleaning up...")
    print("Cleaning up...")

    RecordingsFile.close()

    if ServerAddress is not None:
        Socket.RequestHandlerExit()
        Socket.WaitForHandlerToExit()
        Socket.Reset()

    #Reset GPIO pins.
    GPIO.cleanup()

if __name__ == "__main__":
    logger = logging.getLogger('Universal Standalone Monitor 0.9.1')
    logging.basicConfig(filename='./universalmonitor.log', format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
    logger.setLevel(logging.DEBUG)

    RunStandalone()
