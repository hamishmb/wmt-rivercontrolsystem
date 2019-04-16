#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Universal Standalone Monitor for the River System Control and Monitoring Software Version 0.10.0
# Copyright (C) 2017-2018 Wimborne Model Town
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
This is the secondary part of the software. It forms the
universal monitor that is used on the slave/client pis.
Universal in this case means that this same program can be
used for all of the probes this software framework supports.

.. module:: universal_monitor.py
    :platform: Linux
    :synopsis: The secondary part of the control software.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>

"""

import time
import datetime
import logging
import getopt
import sys
import traceback

import config

try:
    #Allow us to generate documentation on non-RPi systems.
    import RPi.GPIO as GPIO

except ImportError:
    pass

VERSION = "0.10.0"

def usage():
    """
    This function is used to output help information to the standard output
    if the user passes invalid/incorrect commandline arguments.

    Usage:

    >>> usage()
    """

    print("\nUsage: universal_standalone_monitor.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:                   Show this help message")
    print("       -i <string>, --id=<string>    Specifiies the system ID eg \"G4\". If settings")
    print("                                     for this site aren't found in config.py an")
    print("                                     exception will be thrown. Mandatory..")
    print("       -n <int>, --num=<int>         Specify number of readings to take before exiting.")
    print("                                     Without this option, readings will be taken until")
    print("                                     the program is terminated with CTRL-C")
    print("       -d, --debug                   Enable debug mode")
    print("       -q, --quiet                   Log only warnings, errors, and critical errors")
    print("universal_standalone_monitor.py is released under the GNU GPL Version 3")
    print("Copyright (C) Wimborne Model Town 2017-2019")

def handle_cmdline_options():
    """
    This function is used to handle the commandline options passed
    to universal_monitor.py.

    Valid commandline options to universal_standalone_monitor.py:
        -h, --help                          Calls the usage() function to display help information
                                            to the user.
        -i <string>, --id=<string>          Specifies the system ID eg "G4". If settings for this
                                            site aren't found in config.py an exception will be
                                            thrown. Mandatory.
        -n <int>, --num=<int>               Specify the number of readings to take before exiting.
                                            if not specified, readings will be taken until
                                            the program is terminated with CTRL-C.
        -d, --debug                         Enable debug mode.
        -q, --quiet                         Show only warnings, errors, and critical errors.

    Returns:
        tuple(string system_id, int num_readings).

            The system id and the number of readings to take.

    Raises:
        AssertionError, if there are unhandled options.

    Usage:

    >>> system_id, num_readings = handle_cmdline_options()
    """

    #Check all cmdline options are valid.
    try:
        opts = getopt.getopt(sys.argv[1:], "hdqi:n:",
                             ["help", "debug", "quiet", "id=", "num="])[0]

    except getopt.GetoptError as err:
        #Invalid option. Show the help message and then exit.
        #Show the error.
        print(str(err))
        usage()
        sys.exit(2)

    #Do setup. o=option, a=argument.
    num_readings = 0 #Take readings indefinitely by default.
    system_id = None

    for opt, arg in opts:
        if opt in ["-n", "--num"]:
            num_readings = int(arg)

        elif opt in ["-i", "--id"]:
            system_id = arg

        elif opt in ("-d", "--debug"):
            logger.setLevel(logging.DEBUG)

        elif opt in ("-q", "--quiet"):
            logger.setLevel(logging.WARNING)

        elif opt in ["-h", "--help"]:
            usage()
            sys.exit()

        else:
            assert False, "unhandled option"

    #Check system ID was specified.
    assert system_id is not None, "You must specify the system ID"

    #Check system ID is valid.
    assert system_id in config.SITE_SETTINGS, "Invalid system ID"

    return system_id, num_readings

def run_standalone():
    """
    This is the main part of the program.
    It imports everything required from the Tools package,
    and sets up the client socket, calls the function to
    greet the user, sets up the sensor objects, and the
    monitors.

    After that, it enters a monitor loop, continuously getting
    new probe data, and then it sends it down the socket to the
    server, if any.

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
    system_id, num_readings = handle_cmdline_options()

    #Do framework imports.
    from Tools import coretools as core_tools
    from Tools import sockettools as socket_tools
    from Tools.monitortools import Monitor

    #Connect to server, if any.
    socket = None

    logger.info("Initialising connection to server, please wait...")
    print("Initialising connection to server, please wait...")
    socket = socket_tools.Sockets("Plug", config.SITE_SETTINGS[system_id]["ServerName"])
    socket.set_portnumber(config.SITE_SETTINGS[system_id]["ServerPort"])
    socket.set_server_address(config.SITE_SETTINGS[system_id]["ServerAddress"])
    socket.start_handler()

    logger.info("Will connect to server as soon as it becomes available.")
    print("Will connect to server as soon as it becomes available.")

    #Print system time.
    print("System Time: ", str(datetime.datetime.now()))

    #Create the probe(s).
    probes = []
    monitors = []

    #Get settings for each type of monitor from the config file.
    logger.info("Setting up the probes...")

    for probe_id in config.SITE_SETTINGS[system_id]["Probes"]:
        probe_settings = config.SITE_SETTINGS[system_id]["Probes"][probe_id]

        _type = probe_settings["Type"]
        probe = probe_settings["Class"]
        pins = probe_settings["Pins"]
        reading_interval = probe_settings["Default Interval"]

        probe = probe(probe_id)
        probe.set_pins(pins)
        probes.append(probe)

        #Start the monitor threads.
        logger.info("Starting the monitor thread for "+probe_id+"...")
        monitors.append(Monitor(probe, num_readings, reading_interval, system_id))

    print("Synchronising with monitor threads...")

    #Wait until the first readings have come in so we are synchronised.
    for monitor in monitors:
        while not monitor.has_data():
            time.sleep(0.5)

    print("Starting to take readings. Please stand by...")

    logger.info("You should begin to see readings now...")

    #Set to sensible defaults to avoid errors.
    old_reading_interval = 0

    #Keep tabs on its progress so we can write new readings to the file.
    try:
        at_least_one_monitor_running = True

        while at_least_one_monitor_running:
            for monitor in monitors:
                if monitor.is_running():
                    #Check for new readings. NOTE: Later on, use the readings returned from this
                    #for state history generation etc.
                    core_tools.get_and_handle_new_reading(monitor, "test",
                                                          config.SITE_SETTINGS
                                                          ["G4"]["ServerAddress"], socket)

            #Wait until it's time to check for another reading.
            #I know we could use a long time.sleep(),
            #but this MUST be responsive to changes in the reading interval.
            count = 0

            while count < reading_interval:
                #This way, if our reading interval changes,
                #the code will respond to the change immediately.
                #Check if we have a new reading interval.
                if socket.has_data():
                    data = socket.read()

                    if "Reading Interval" in data:
                        reading_interval = int(data.split()[-1])

                        #Only add a new line to the log if the reading interval changed.
                        if reading_interval != old_reading_interval:
                            old_reading_interval = reading_interval
                            logger.info("New reading interval: "+str(reading_interval))
                            print("\nNew reading interval: "+str(reading_interval))

                            #Make sure all monitors use the new reading interval.
                            for monitor in monitors:
                                monitor.set_reading_interval(reading_interval)

                    socket.pop()

                time.sleep(1)
                count += 1

            #Check if at least one monitor is running.
            at_least_one_monitor_running = False

            for monitor in monitors:
                if monitor.is_running():
                    at_least_one_monitor_running = True

    except KeyboardInterrupt:
        #Ask the thread to exit.
        logger.info("Caught keyboard interrupt. Asking monitor thread(s) to exit...")
        print("Caught keyboard interrupt. Asking monitor thread(s) to exit.")
        print("This may take a little while, so please be patient...")

    for monitor in monitors:
        monitor.request_exit(wait=True)

    #Always clean up properly.
    logger.info("Cleaning up...")
    print("Cleaning up...")

    socket.request_handler_exit()
    socket.wait_for_handler_to_exit()
    socket.reset()

    #Reset GPIO pins.
    GPIO.cleanup()

if __name__ == "__main__":
    logger = logging.getLogger('Universal Standalone Monitor '+VERSION)
    logging.basicConfig(filename='./logs/universalmonitor.log',
                        format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
                        datefmt='%d/%m/%Y %I:%M:%S %p')

    logger.setLevel(logging.INFO)

    #Catch any unexpected errors and log them so we know what happened.
    try:
        run_standalone()

    except:
        logger.critical("Unexpected error \n\n"+str(traceback.format_exc())
                        +"\n\nwhile running. Exiting...")

        print("Unexpected error \n\n"+str(traceback.format_exc())+"\n\nwhile running. Exiting...")
