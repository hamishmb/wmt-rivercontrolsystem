#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# River System Control and Monitoring Software
# Copyright (C) 2017-2019 Wimborne Model Town
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

#pylint: disable=logging-not-lazy
#
#Reason (logging-not-lazy): Harder to understand the logging statements that way.

"""
This is the main part of the control software, and it currently manages
balancing water between the butts and the sump using a magnetic probe and
a solid state relay to control the butts pump. This software runs on sumppi.
It communicates with buttspi over the network to gather readings.

.. note::
      This program currently has LIMITED FUNCTIONALITY.
      It is a pre-production version that is being used
      to set up a test system that uses 3 RPis, one at
      the sump, with a hall effect probe and 2 SSRs connected
      and the other Pis are installed at the butts. One has
      a float switch and a hall effect probe. The other is used
      to control a gate valve for managing water flow coming
      back from the water butts.

      The sump pi will be using this program.
      Sump pi uses the first SSR to control the butts pump, and
      the second one is used to enable/disable the circulation
      pump. It will communicate with the other pis over sockets,
      and the other pis will be running universal_standalone_monitor.py,
      and gate_valve.py.

.. module:: main.py
    :platform: Linux
    :synopsis: The main part of the control software.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>

"""

import sys
import getopt
import time
import datetime
import logging
import traceback

try:
    #Allow us to generate documentation on non-RPi systems.
    import RPi.GPIO as GPIO

except ImportError:
    pass

def usage():
    """
    This function is used to output help information to the standard output
    if the user passes invalid/incorrect commandline arguments.

    Usage:

    >>> usage()
    """

    print("\nUsage: main.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:                   Show this help message")
    print("       -d, --debug                   Enable debug mode")
    print("       -q, --quiet                   Log only warnings, errors, and critical errors")
    print("universal_standalone_monitor.py is released under the GNU GPL Version 3")
    print("Copyright (C) Wimborne Model Town 2017-2019")

def handle_cmdline_options():
    """
    This function is used to handle the commandline options passed
    to main.py.

    Valid commandline options to universal_standalone_monitor.py:
        -h, --help                          Calls the usage() function to display help information
                                            to the user.
        -d, --debug                         Enable debug mode.
        -q, --quiet                         Show only warnings, errors, and critical errors.

    Returns:
        None

    Raises:
        AssertionError, if there are unhandled options.

    Usage:

    >>> handle_cmdline_options()
    """

    #Check all cmdline options are valid.
    try:
        opts = getopt.getopt(sys.argv[1:], "hdq",
                             ["help", "debug", "quiet"])[0]

    except getopt.GetoptError as err:
        #Invalid option. Show the help message and then exit.
        #Show the error.
        print(str(err))
        usage()
        sys.exit(2)

    #Do setup. o=option, a=argument.
    for opt, arg in opts:
        if opt in ["-d", "--debug"]:
            logger.setLevel(logging.DEBUG)

        elif opt in ["-q", "--quiet"]:
            logger.setLevel(logging.WARNING)

        elif opt in ["-h", "--help"]:
            usage()
            sys.exit()

        else:
            assert False, "unhandled option"

def run_standalone(): #TODO Refactor me into lots of smaller functions.
    """
    This is the main part of the program.
    It imports everything required from the Tools package,
    and sets up the server socket, calls the function to
    greet the user, sets up the sensor objects, and the
    monitors.

    After that, it enters a monitor loop and repeatedly checks for new
    sensor data, and then calls the coretools.sumppi_control_logic() function
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
    handle_cmdline_options()

    #Do framework imports.
    import config

    from Tools import coretools as core_tools
    from Tools import sockettools as socket_tools

    #TODO should standardise and do the same way as the above.
    from Tools.monitortools import SocketsMonitor
    from Tools.monitortools import Monitor

    #Get system ID from config.
    system_id = config.SITE_SETTINGS["SUMP"]["ID"]

    #Create all sockets.
    logger.info("Creating sockets...")
    sockets = {}

    for each_socket in config.SITE_SETTINGS["SUMP"]["Sockets"].values():
        socket = socket_tools.Sockets("Socket", each_socket["Name"])
        socket.set_portnumber(each_socket["PortNumber"])
        sockets[each_socket["ID"]] = socket

        socket.start_handler()

    logger.debug("Done!")

    #Print system time.
    print("System Time: ", str(datetime.datetime.now()))

    #Create the probe(s).
    probes = core_tools.setup_devices(system_id)

    #Create the device(s).
    devices = core_tools.setup_devices(system_id, dictionary="Devices")

    #Default reading interval for all probes.
    reading_interval = config.SITE_SETTINGS["SUMP"]["Default Interval"]

    logger.info("Starting to take readings...")
    print("Starting to take readings. Please stand by...")

    logger.info("Waiting for client(s) to connect...")
    print("Waiting for client(s) to connect...")

    #Start monitor threads for the socket (wendy house butts).
    #FIXME Figure out what to do based on what is in config.py, rather
    #than hardcoding it.
    monitors = []

    #Wendy house butts.
    monitors.append(SocketsMonitor(sockets["SOCK4"], "G4", "FS0"))
    monitors.append(SocketsMonitor(sockets["SOCK4"], "G4", "M0"))

    #Gate valve.
    monitors.append(SocketsMonitor(sockets["SOCK14"], "V4", "V4"))

    #And for our SUMP probe.
    for probe in probes:
        if probe.get_id() == "SUMP:M0":
            monitors.append(Monitor(probe, reading_interval, system_id))

    #Wait until the first readings have come in so we are synchronised.
    #NB: Will now wait for client connection.
    for each_monitor in monitors:
        while not each_monitor.has_data():
            time.sleep(0.5)

    #Sleep a few more seconds to make sure the client is ready.
    time.sleep(10)

    #Setup. Prevent errors.
    sump_reading = core_tools.Reading(str(datetime.datetime.now()), 0,
                                      "SUMP:M0", "0mm", "OK")

    butts_reading = core_tools.Reading(str(datetime.datetime.now()), 0,
                                       "G4:FS0", "True", "OK")

    #Keep tabs on its progress so we can write new readings to the file.
    try:
        at_least_one_monitor_running = True

        while at_least_one_monitor_running:
            #Check for new readings from all monitors.
            for monitor in monitors:
                #Skip over any monitors that have stopped.
                #TODO: This should never happen, moan in log file?
                if not monitor.is_running():
                    continue

                #Check for new readings.
                #NOTE: Later on, use the readings returned from this
                #for state history generation etc.
                reading = core_tools.get_and_handle_new_reading(monitor, "test")

                #Ignore empty readings.
                if reading is None:
                    continue

                #Keep the G4:FS0 & SUMP:M0 readings (used in control logic).
                if reading.get_id() == "G4:FS0":
                    butts_float_reading = reading

                elif reading.get_id() == "G4:M0":
                    butts_reading = reading

                elif reading.get_id() == "SUMP:M0":
                    sump_reading = reading

            #Logic.
            reading_interval = core_tools.sumppi_control_logic(sump_reading, butts_reading,
                                                               butts_float_reading, devices,
                                                               monitors, sockets, reading_interval)

            #Wait until it's time to check for another reading.
            time.sleep(reading_interval)

            #Check if at least one monitor is running.
            at_least_one_monitor_running = False

            for monitor in monitors:
                if monitor.is_running():
                    at_least_one_monitor_running = True

    except KeyboardInterrupt:
        #Ask the threads to exit.
        logger.info("Caught keyboard interrupt. Asking monitor threads to exit...")
        print("Caught keyboard interrupt. Asking monitor threads to exit.")
        print("This may take a little while, so please be patient...")

    for monitor in monitors:
        monitor.request_exit()

    logger.info("Waiting for monitor threads to exit...")
    print("Waiting for monitor threads to exit...")

    for monitor in monitors:
        monitor.request_exit(wait=True)

    #Always clean up properly.
    logger.info("Waiting for sockets to exit...")
    print("Waiting for sockets to exit...")

    for each_socket in sockets.values():
        each_socket.request_handler_exit()
        each_socket.wait_for_handler_to_exit()
        each_socket.reset()

    logger.info("Resetting GPIO pins...")
    print("Resetting GPIO pins...")

    #Reset GPIO pins.
    GPIO.cleanup()

if __name__ == "__main__":
    logger = logging.getLogger('River System Control Software')
    logging.basicConfig(filename='./logs/rivercontrolsystem.log',
                        format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
                        datefmt='%d/%m/%Y %I:%M:%S %p')

    #Default logging level of INFO.
    logger.setLevel(logging.INFO)

    #Catch any unexpected errors and log them so we know what happened.
    try:
        run_standalone()

    except:
        logger.critical("Unexpected error \n\n"+str(traceback.format_exc())
                        +"\n\nwhile running. Exiting...")

        print("Unexpected error \n\n"+str(traceback.format_exc())+"\n\nwhile running. Exiting...")
