#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# River System Control and Monitoring Software Version 1.0
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

#NOTE: This program currently has LIMITED FUNCTIONALITY.
#      It is a pre-production version that is being used
#      to set up a test system that uses 2 RPis, one at
#      the sump, with a resistance probe and SSR connected
#      and the other Pi is installed at the butts, and has
#      a float switch. The sump pi will be using this program.
#      It will communicate with the other pi over a socket,
#      and the other pi will be running float_switch_monitor_standalone.py.

import RPi.GPIO as GPIO
import time
import datetime
import sys
import getopt #Proper option handler.
import os
import threading
import logging

def usage():
    print("\nUsage: main.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:               Show this help message")
    print("       -f, --file:               Specify file to write the recordings to. Default: interactive.")
    print("main.py is released under the GNU GPL Version 3")
    print("Copyright (C) Wimborne Model Town 2017")

def HandleCmdlineOptions():
    """
    Handles commandline options.
    Usage:

        tuple HandleCmdlineOptions()
    """

    FileName = "Unknown"

    #Check all cmdline options are valid.
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:", ["help", "file="])

    except getopt.GetoptError as err:
        #Invalid option. Show the help message and then exit.
        #Show the error.
        print(str(err))
        usage()
        sys.exit(2)

    #Do setup. o=option, a=argument.
    NumberOfReadingsToTake = 0 #Take readings indefinitely by default.

    for o, a in opts:
        if o in ["-f", "--file"]:
            FileName = a

        elif o in ["-h", "--help"]:
            usage()
            sys.exit()
    
        else:
            assert False, "unhandled option"

    return FileName

def RunStandalone():
    #Allows the progam to run standalone as well as being a module.
    #Do required imports.
    import Tools

    from Tools import sensorobjects as SensorObjects
    from Tools import monitortools as MonitorTools
    from Tools import coretools as CoreTools
    from Tools import sockettools as SocketTools

    Tools.sockettools.logger = logger

    #Handle cmdline options.
    FileName = HandleCmdlineOptions()

    #Provide a connection for clients to connect to.
    print("Creating a socket for clients to connect to, please wait...")
    Socket = SocketTools.Sockets("Socket")
    Socket.SetPortNumber(30000)
    Socket.StartHandler()

    print("Done!")

    #Greet and get filename.
    FileName, RecordingsFile = CoreTools.GreetAndGetFilename("River System Control and Monitoring Software", FileName)

    print("Starting to take readings. Please stand by...")

    #Create the devices.
    SumpProbe = SensorObjects.ResistanceProbe("Sump Level")
    AuxMotor = SensorObjects.Motor("Aux Motor") #SSR.

    #Set the devices up.
    SumpProbe.SetActiveState(False)     #Active low.
    SumpProbe.SetPins((15, 17, 27, 22, 23, 24, 10, 9, 25, 11))

    #Aux motor doesn't support PWM.
    AuxMotor.SetPWMAvailable(False, -1)

    #Reading interval.
    ReadingInterval = 300

    #Wait until the socket is connected and ready.
    while not Socket.IsReady(): time.sleep(0.5)

    #Start the monitor thread. Take readings indefinitely.
    #Also wait a few seconds to let it initialise. This also allows us to take the first reading before we start waiting.
    SumpProbeMonitorThread = MonitorTools.ResistanceProbeMonitor(SumpProbe, 0, ReadingInterval=ReadingInterval) #FIXME: Must be able to change reading interval as and when required.
    time.sleep(10)

    #Keep tabs on its progress so we can write new readings to the file.
    while True:
        #Exit if the resistance probe monitor thread crashes for some reason.
        if not SumpProbeMonitorThread.IsRunning():
            break;

        #Check for new readings from the resistance probe.
        while SumpProbeMonitorThread.HasData():
            SumpProbeReading = SumpProbeMonitorThread.GetReading()

            #Write any new readings to the file and to stdout.
            print("Resistance Probe: "+SumpProbeReading)
            RecordingsFile.write("Resistance Probe: "+SumpProbeReading)

        #Check for new readings from the float switch.
        while Socket.HasPendingData():
            FloatSwitchReading = Socket.Read()

            #Write any new readings to the file and to stdout.
            print("Float Switch: "+FloatSwitchReading)
            RecordingsFile.write("Float Switch: "+FloatSwitchReading)

        #Logic. TODO: Tidy up. Make the readings more machine-readable. Sort out logging to file. Don't only print status messages.

        if int(SumpProbeReading[4].replace("m", "")) > 700:
            #Level in the sump is getting high.
            #Pump some water to the butts if they aren't full.
            #If they are full, do nothing and let the sump overflow.
            print("Water level in the sump > 700mm!")

            if FloatSwitchReading[-1] == "False":
                #Pump to the butts.
                print("Pumping water to the butts...")
                AuxMotor.TurnOn() #FIXME check return value is True (success).

                print("Changing reading interval to 30 seconds so we can keep a close eye on what's happening...")
                ReadingInterval = 30
                #SumpProbeMonitorThread.SetReadingInterval(ReadingInterval) FIXME

            else:
                #Butts are full. Do nothing, but warn user.
                AuxMotor.TurnOff()

                print("The water butts are full.")
                print("Allowing the sump to overflow.")

                print("Setting reading interval to 5 minutes...")
                ReadingInterval = 300

        elif int(SumpProbeReading[4].replace("m", "")) < 700 and int(SumpProbeReading[4].replace("m", "")) > 500:
            #Level in the sump is good.
            #If the butts pump is on, turn it off.
            AuxMotor.TurnOff()

            print("Water level in the sump is good. Doing nothing...")

            print("Setting reading interval to 5 minutes...")
            ReadingInterval = 300

        elif int(SumpProbeReading[4].replace("m", "")) < 500:
            #Level in the sump is getting low.
            #If the butts pump is on, turn it off.
            AuxMotor.TurnOff()

            print("Water level in the sump < 500mm!")
            print("Waiting for water to come back from the butts before requesting human intervention...")

            print("Setting reading interval to 1 minute so we can monitor more closely...")
            ReadingInterval = 60

            #We have no choice here but to wait for water to come back from the butts and warn the user.
            #^ Tap is left half-open.

        elif int(SumpProbeReading[4].replace("m", "")) < 400:
            #Level in the sump is very low!
            #If the butts pump is on, turn it off.
            AuxMotor.TurnOff()

            print("*** NOTICE ***: Water level in the sump < 400mm!")
            print("*** NOTICE ***: HUMAN INTERVENTION REQUIRED: Please add water to the system.")

            print("Setting reading interval to 30 seconds for close monitoring...")
            ReadingInterval = 30

        else:
            #Level in the sump is critically low!
            #If the butts pump is on, turn it off.
            AuxMotor.TurnOff()

            print("*** CRITICAL ***: Water level in the sump < 300mm!")
            print("*** CRITICAL ***: HUMAN INTERVENTION REQUIRED: Please add water to the system.")
            print("*** CRITICAL ***: The pump might be running dry RIGHT NOW!")

            print("Setting reading interval to 15 seconds for super close monitoring...")
            ReadingInterval = 15

        #Wait until it's time to check for another reading.
        time.sleep(ReadingInterval)

    #Always clean up properly.
    print("Cleaning up...")

    RecordingsFile.close()

    Socket.RequestHandlerExit()
    Socket.WaitForHandlerToExit()
    Socket.Reset()

    #Reset GPIO pins.
    GPIO.cleanup()

if __name__ == "__main__":
    #FIXME: Log to a file in the version we will deploy. Leave as is for the moment for easy debugging in the test installation.
    logger = logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p', level=logging.WARNING)

    RunStandalone() 
