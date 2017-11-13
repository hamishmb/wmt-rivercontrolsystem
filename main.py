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

"""
This is the main part of the control software, and it currently manages
balancing water between the butts and the sump using a magnetic probe and
a solid state relay to control the butts pump. This software runs on sumppi.
It communicates with buttspi over the network to gather float switch readings.

.. note::
      This program currently has LIMITED FUNCTIONALITY.
      It is a pre-production version that is being used
      to set up a test system that uses 2 RPis, one at
      the sump, with a hall effect probe and SSR connected
      and the other Pi is installed at the butts, and has
      a float switch. The sump pi will be using this program.
      It will communicate with the other pi over a socket,
      and the other pi will be running universal_standalone_monitor.py.

.. module:: main.py
    :platform: Linux
    :synopsis: The main part of the control software.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>

"""

import time
import sys
import getopt #Proper option handler.
import logging
import traceback

#Do required imports.
import Tools

from Tools import sensorobjects as sensor_objects
from Tools import monitortools as monitor_tools
from Tools import coretools as core_tools
from Tools import sockettools as socket_tools

#Define global variables.
VERSION = "0.9.1"
RELEASEDATE = "30/10/2017"

def usage():
    """
    This function is used to output help information to the standard output
    if the user passes invalid/incorrect commandline arguments.

    Usage:

    >>> usage()
    """

    print("\nUsage: main.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:               Show this help message")
    print("       -f, --file:               Specify file to write the recordings to.")
    print("                                 If not specified: interactive.")
    print("main.py is released under the GNU GPL Version 3")
    print("Copyright (C) Wimborne Model Town 2017")

def handle_cmdline_options():
    """
    This function is used to handle the commandline options passed
    to main.py.

    Valid commandline options to main.py:
        -h, --help         Calls the usage() function to display help information to the user.
        -f, --file         Specifies file to write the recordings to. If not specified, the
                           user is asked during execution in the greeting phase.

    Returns:
        string.

            This will be whatever filename the user provided on the commandline.

    Raises:
        AssertionError, if there are unhandled options.

    Usage:

    >>> filename = handle_cmdline_options()
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

def run_standalone(): #TODO Refactor me into lots of smaller functions.
    """
    This is the main part of the program.
    It imports everything required from the Tools package,
    and sets up the server socket, calls the function to
    greet the user, sets up the sensor objects, and the
    monitors.

    After that, it enters a monitor loop and repeatedly checks for new
    sensor data, and then calls the coretools.do_control_logic() function
    to make decisions about what to do based on this data.

    Raises:
        Nothing, hopefully. It's possible that an unhandled exception
        could be propagated through here though, so I recommend that
        you call this function like this at the current time:

        >>> try:
        >>>     run_standalone()
        >>> 
        >>> except:
        >>>     #Handle the error and put it in the log file for debugging purposes.
        >>>     #Write the error to the standard output.
        >>>     #Exit the program.

    Usage:
        As above.
    """

    #Handle cmdline options.
    file_name = handle_cmdline_options()

    #Provide a connection for clients to connect to.
    logger.info("Creating a socket for clients to connect to, please wait...")
    socket = socket_tools.Sockets("Socket")
    socket.set_portnumber(30000)
    socket.start_handler()

    logger.debug("Done!")

    #Greet and get filename.
    file_name, file_handle = core_tools.greet_and_get_filename("River System Control and Monitoring Software", file_name)

    #Create the devices.
    sump_probe = sensor_objects.HallEffectProbe("Sump Level")
    butts_pump = sensor_objects.Motor("Butts Pump") #SSR.

    #Set the devices up.
    #sump_probe.set_active_state(False)     #Active low. Disabled because meaningless for this probe.
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
    monitor = monitor_tools.Monitor("Hall Effect Probe", sump_probe, 0, reading_interval)

    #Wait until the first reading has come in so we are synchronised.
    while not monitor.has_data():
        time.sleep(0.5)

    #Sleep a few more seconds to make sure the client is ready.
    time.sleep(10)

    #Setup. Prevent errors.
    butts_reading_time = butts_reading_status = ""
    butts_reading = "Time: None State: True"
    last_butts_reading = "No Reading"

    sump_reading_time = sump_reading_status = ""
    sump_reading = "Time: Empty Time Level: -1mm Pin states: 1111111111"
    last_sump_reading = "No Reading"

    #Keep tabs on its progress so we can write new readings to the file.
    try:
        while True:
            #Exit if the resistance probe monitor thread crashes for some reason.
            if not monitor.is_running():
                break

            #Check for new readings from the sump probe. TODO What to do here if a fault is detected?
            while monitor.has_data():
                sump_reading_time, sump_reading, sump_reading_status = monitor.get_reading()

                #Check if the reading is different to the last reading.
                if sump_reading == last_sump_reading:
                    #Write a . to each file.
                    logger.info(".")
                    print(".", end='') #Disable newline when printing this message.
                    file_handle.write(".")

                else:
                    #Write any new readings to the file and to stdout.
                    logger.info("Time: "+sump_reading_time+" Sump Probe: "+sump_reading+" Status: "+sump_reading_status)
                    print("Time: "+sump_reading_time+" Sump Probe: "+sump_reading+" Status: "+sump_reading_status)
                    file_handle.write("\nTime: "+sump_reading_time+" Sump Probe: "+sump_reading+" Status: "+sump_reading_status)

                    #Set last sump reading to this reading.
                    last_sump_reading = sump_reading

                #Flush buffers.
                sys.stdout.flush()
                file_handle.flush()

            #Check for new readings from the float switch.
            while socket.has_data():
                butts_readings = socket.read().split(",")

                socket.pop()

                for butts_reading_time, butts_reading, butts_reading_status in butts_readings: 
                    if butts_reading == "":
                        #Client not ready, ignore this reading, but prevent errors.
                        #Assume the butts are full.
                        logger.info("Client not ready for reading butts level. Assuming butts are full for now.")
                        print("Client not ready for reading butts level. Assuming butts are full for now.")
                        butts_reading = "Time: None State: True"

                    else:
                        #Check if the reading is different to the last reading.
                        if butts_reading == last_butts_reading:
                            #Write a . to each file.
                            logger.info(".")
                            print(".", end='') #Disable newline when printing this message.
                            file_handle.write(".")

                        else:
                            #Write any new readings to the file and to stdout.
                            logger.info("Time: "+butts_reading_time+" Float Switch: "+butts_reading+" Status: "+butts_reading_status)
                            print("Time: "+butts_reading_time+" Float Switch: "+butts_reading+" Status: "+butts_reading_status)
                            file_handle.write("Time: "+butts_reading_time+" Float Switch: "+butts_reading+" Status: "+butts_reading_status)

                            #Set last butts reading to this reading.
                            last_butts_reading = butts_reading

            #Logic.
            reading_interval = core_tools.do_control_logic(sump_reading, butts_reading, butts_pump, monitor, socket, reading_interval)

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
    #Import here to prevent errors when generating documentation on non-RPi systems.
    import RPi.GPIO as GPIO

    logger = logging.getLogger('River System Control Software '+VERSION)
    logging.basicConfig(filename='./rivercontrolsystem.log', format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
    logger.setLevel(logging.INFO)

    #Catch any unexpected errors and log them so we know what happened.
    try:
        run_standalone()

    except:
        logger.critical("Unexpected error \n\n"+str(traceback.format_exc())+"\n\nwhile running. Exiting...")
        print("Unexpected error \n\n"+str(traceback.format_exc())+"\n\nwhile running. Exiting...")
