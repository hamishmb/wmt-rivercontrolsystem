#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# River System Control and Monitoring Software Version 0.9.1
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

# TODO Implement setting reading interval across monitors running on different systems.

import RPi.GPIO as GPIO
import time
import sys
import getopt #Proper option handler.
import logging

#Define global variables.
Version = "0.9.1"
ReleaseDate = "5/9/2017" #TODO Update when you make changes.

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

    Tools.coretools.logger = logger
    Tools.sockettools.logger = logger

    #Handle cmdline options.
    FileName = HandleCmdlineOptions()

    #Provide a connection for clients to connect to.
    logger.debug("Creating a socket for clients to connect to, please wait...")
    Socket = SocketTools.Sockets("Socket")
    Socket.SetPortNumber(30000)
    Socket.StartHandler()

    logger.debug("Done!")

    #Greet and get filename.
    FileName, RecordingsFile = CoreTools.greet_and_get_filename("River System Control and Monitoring Software", FileName)

    #Create the devices.
    SumpProbe = SensorObjects.ResistanceProbe("Sump Level")
    AuxMotor = SensorObjects.Motor("Aux Motor") #SSR.

    #Set the devices up.
    SumpProbe.SetActiveState(False)     #Active low.
    SumpProbe.SetPins((15, 17, 27, 22, 23, 24, 10, 9, 25, 11))

    #Aux motor doesn't support PWM.
    AuxMotor.SetPins(5, Input=False) #This is an output.
    AuxMotor.SetPWMAvailable(False, -1)

    #Reading interval.
    ReadingInterval = 300

    logger.info("The client(s) can connect whenever they're ready.")
    print("The client(s) can connect whenever they're ready.")

    logger.info("Starting to take readings...")
    print("Starting to take readings. Please stand by...")

    #Start the monitor thread. Take readings indefinitely.
    SumpProbeMonitorThread = MonitorTools.Monitor("Resistance Probe", SumpProbe, 0, ReadingInterval=ReadingInterval)

    #Wait until the first reading has come in so we are synchronised.
    while not SumpProbeMonitorThread.HasData():
        time.sleep(0.5)

    #Sleep a few more seconds to make sure the client is ready.
    time.sleep(10)

    #Setup. Prevent errors.
    FloatSwitchReading = "Time: None State: True"
    SumpProbeReading = "Time: Empty Time Level: -1mm Pin states: 1111111111"

    #Keep tabs on its progress so we can write new readings to the file.
    try:
        while True:
            #Exit if the resistance probe monitor thread crashes for some reason.
            if not SumpProbeMonitorThread.IsRunning():
                break;

            #Check for new readings from the resistance probe.
            while SumpProbeMonitorThread.HasData():
                SumpProbeReading = SumpProbeMonitorThread.GetReading()

                #Write any new readings to the file and to stdout.
                logger.debug("Resistance Probe: "+SumpProbeReading)
                print("Resistance Probe: "+SumpProbeReading)
                RecordingsFile.write("Resistance Probe: "+SumpProbeReading+"\n")

            #Check for new readings from the float switch.
            while Socket.HasPendingData():
                FloatSwitchReading = Socket.Read()
                Socket.Pop()

                if FloatSwitchReading == "":
                    #Client not ready, ignore this reading, but prevent errors. Assume the butts are full.
                    logger.info("Client not ready for reading butts level. Assuming butts are full for now.")
                    print("Client not ready for reading butts level. Assuming butts are full for now.")
                    FloatSwitchReading = "Time: None State: True"

                else:
                    #Write any new readings to the file and to stdout.
                    logger.debug("Float Switch: "+FloatSwitchReading)
                    print("Float Switch: "+FloatSwitchReading)
                    RecordingsFile.write("Float Switch: "+FloatSwitchReading+"\n")

            #Logic.
            CoreTools.do_control_logic(SumpProbeReading, FloatSwitchReading, AuxMotor, SumpProbeMonitorThread)

            #Wait until it's time to check for another reading.
            time.sleep(ReadingInterval)

    except KeyboardInterrupt:
        #Ask the thread to exit.
        logger.info("Caught keyboard interrupt. Asking monitor thread to exit...")
        print("Caught keyboard interrupt. Asking monitor thread to exit.")
        print("This may take a little while, so please be patient...")

        SumpProbeMonitorThread.RequestExit(wait=True)

    #Always clean up properly.
    logger.info("Cleaning up...")
    print("Cleaning up...")

    RecordingsFile.close()

    Socket.RequestHandlerExit()
    Socket.WaitForHandlerToExit()
    Socket.Reset()

    #Reset GPIO pins.
    GPIO.cleanup()

if __name__ == "__main__":
    logger = logging.getLogger('River System Control Software '+Version)
    logging.basicConfig(filename='./rivercontrolsystem.log', format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
    logger.setLevel(logging.DEBUG)

    RunStandalone()
