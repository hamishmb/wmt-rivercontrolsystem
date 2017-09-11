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

import time
import sys
import getopt #Proper option handler.
import logging

import RPi.GPIO as GPIO

#Define global variables.
VERSION = "0.9.1"
RELEASEDATE = "11/9/2017"

def usage():
    print("\nUsage: main.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:               Show this help message")
    print("       -f, --file:               Specify file to write the recordings to.")
    print("                                 If not specified: interactive.")
    print("main.py is released under the GNU GPL Version 3")
    print("Copyright (C) Wimborne Model Town 2017")

def handle_cmdline_options():
    """
    Handles commandline options.
    Usage:

        tuple handle_cmdline_options()
    """

    file_name = "Unknown"

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
    for o, a in opts:
        if o in ["-f", "--file"]:
            file_name = a

        elif o in ["-h", "--help"]:
            usage()
            sys.exit()

        else:
            assert False, "unhandled option"

    return file_name

def run_standalone():
    #Allows the progam to run standalone as well as being a module.
    #Do required imports.
    import Tools

    from Tools import sensorobjects as sensor_objects
    from Tools import monitortools as monitor_tools
    from Tools import coretools as core_tools
    from Tools import sockettools as socket_tools

    Tools.coretools.logger = logger
    Tools.sockettools.logger = logger

    #Handle cmdline options.
    file_name = handle_cmdline_options()

    #Provide a connection for clients to connect to.
    logger.debug("Creating a socket for clients to connect to, please wait...")
    socket = socket_tools.Sockets("Socket")
    socket.set_portnumber(30000)
    socket.start_handler()

    logger.debug("Done!")

    #Greet and get filename.
    file_name, file_handle = core_tools.greet_and_get_filename("River System Control and Monitoring Software", file_name)

    #Create the devices.
    sump_probe = sensor_objects.ResistanceProbe("Sump Level")
    butts_pump = sensor_objects.Motor("Aux Motor") #SSR.

    #Set the devices up.
    sump_probe.set_active_state(False)     #Active low.
    sump_probe.set_pins((15, 17, 27, 22, 23, 24, 10, 9, 25, 11))

    #Butts pump doesn't support PWM.
    butts_pump.set_pins(5, _input=False) #This is an output.
    butts_pump.set_pwm_available(False, -1)

    #Reading interval.
    reading_interval = 300

    logger.info("The client(s) can connect whenever they're ready.")
    print("The client(s) can connect whenever they're ready.")

    logger.info("Starting to take readings...")
    print("Starting to take readings. Please stand by...")

    #Start the monitor thread. Take readings indefinitely.
    monitor = monitor_tools.Monitor("Resistance Probe", sump_probe, 0, reading_interval)

    #Wait until the first reading has come in so we are synchronised.
    while not monitor.has_data():
        time.sleep(0.5)

    #Sleep a few more seconds to make sure the client is ready.
    time.sleep(10)

    #Setup. Prevent errors.
    butts_reading = "Time: None State: True"
    sump_reading = "Time: Empty Time Level: -1mm Pin states: 1111111111"

    #Keep tabs on its progress so we can write new readings to the file.
    try:
        while True:
            #Exit if the resistance probe monitor thread crashes for some reason.
            if not monitor.is_running():
                break

            #Check for new readings from the resistance probe.
            while monitor.has_data():
                sump_reading = monitor.get_reading()

                #Write any new readings to the file and to stdout.
                logger.debug("Resistance Probe: "+sump_reading)
                print("Resistance Probe: "+sump_reading)
                file_handle.write("Resistance Probe: "+sump_reading+"\n")

            #Check for new readings from the float switch.
            while socket.has_data():
                butts_reading = socket.read()
                socket.pop()

                if butts_reading == "":
                    #Client not ready, ignore this reading, but prevent errors.
                    #Assume the butts are full.
                    logger.info("Client not ready for reading butts level. Assuming butts are full for now.")
                    print("Client not ready for reading butts level. Assuming butts are full for now.")
                    butts_reading = "Time: None State: True"

                else:
                    #Write any new readings to the file and to stdout.
                    logger.debug("Float Switch: "+butts_reading)
                    print("Float Switch: "+butts_reading)
                    file_handle.write("Float Switch: "+butts_reading+"\n")

            #Logic.
            core_tools.do_control_logic(sump_reading, butts_reading, butts_pump, monitor, socket)

            #Wait until it's time to check for another reading.
            time.sleep(reading_interval)

    except KeyboardInterrupt:
        #Ask the thread to exit.
        logger.info("Caught keyboard interrupt. Asking monitor thread to exit...")
        print("Caught keyboard interrupt. Asking monitor thread to exit.")
        print("This may take a little while, so please be patient...")

        monitor.request_exit(wait=True)

    #Always clean up properly.
    logger.info("Cleaning up...")
    print("Cleaning up...")

    file_handle.close()

    socket.request_handler_exit()
    socket.wait_for_handler_to_exit()
    socket.reset()

    #Reset GPIO pins.
    GPIO.cleanup()

if __name__ == "__main__":
    logger = logging.getLogger('River System Control Software '+VERSION)
    logging.basicConfig(filename='./rivercontrolsystem.log', format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
    logger.setLevel(logging.DEBUG)

    run_standalone()
