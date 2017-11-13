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

"""
This is the secondary part of the software. It forms the
universal monitor that is used on the slave/client pis.
Universal in this case means that this same program can be
used for all of the probes this software framework supports.

.. module:: universal_standalone_monitor.py
    :platform: Linux
    :synopsis: The secondary part of the control software.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>

"""

import time
import logging
import getopt
import sys
import traceback

#Do required imports.
import universal_standalone_monitor_config as config

import Tools

from Tools import coretools as core_tools
from Tools import sockettools as socket_tools
from Tools.monitortools import Monitor

VERSION = "0.9.1"

def usage():
    """
    This function is used to output help information to the standard output
    if the user passes invalid/incorrect commandline arguments.

    Usage:

    >>> usage()
    """

    print("\nUsage: universal_standalone_monitor.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:               Show this help message")
    print("       -t <str>, --type=<str>    Type of probe this monitor is for. Must be one of")
    print("                                 'Resistance Probe', 'Hall Effect', 'Hall Effect Probe',")
    print("                                 'Capacitive Probe', 'Float Switch'. Mandatory.")
    print("       -f, --file:               Specify file to write the recordings to.")
    print("                                 If not specified: interactive.")
    print("       -c, --controlleraddress:  Specify the DNS name/IP of the controlling server")
    print("                                 we want to send our level data to, if any.")
    print("       -n <int>, --num=<int>     Specify number of readings to take before exiting.")
    print("                                 Without this option, readings will be taken until")
    print("                                 the program is terminated")
    print("universal_standalone_monitor.py is released under the GNU GPL Version 3")
    print("Copyright (C) Wimborne Model Town 2017")

def handle_cmdline_options():
    """
    This function is used to handle the commandline options passed
    to universal_standalone_monitor.py.

    Valid commandline options to universal_standalone_monitor.py:
        -h, --help                          Calls the usage() function to display help information
                                            to the user.
        -t <str>, --type=<str>              Type of probe this monitor is for. Must be one of
                                            'Resistance Probe', 'Hall Effect', 'Hall Effect Probe'
                                            'Capacitive Probe', or 'Float Switch'. Mandatory.
                                            Specify multiple times for multiple probes.
        -f, --file                          Specifies file to write the recordings to. If not
                                            specified, the user is asked during execution in
                                            the greeting phase.
        -c, --controlleraddress             Specify the DNS name/IP of the controlling server
                                            to which we want to send our level data to, if any.
        -n <int>, --num=<int>               Specify the number of readings to take before exiting.
                                            if not specified, readings will be taken until
                                            the program is terminated with CRTL-C.

    Returns:
        tuple (list types, string file_name, string server_address, int num_readings).

            This will be whatever arguments the user provided on the commandline.
            If any arguments were missing, default values will be provided instead
            as discussed above.

    Raises:
        AssertionError, if there are unhandled options.

    Usage:

    >>> types, file_name, server_address, num_readings = handle_cmdline_options()
    """

    types = []
    file_name = "Unknown"
    server_address = None

    #Check all cmdline options are valid.
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ht:f:c:n:", ["help", "type=", "file=", "controlleraddress=", "num="])

    except getopt.GetoptError as err:
        #Invalid option. Show the help message and then exit.
        #Show the error.
        print(str(err))
        usage()
        sys.exit(2)

    #Do setup. o=option, a=argument.
    num_readings = 0 #Take readings indefinitely by default.

    for o, a in opts:
        if o in ["-t", "--type"]:
            types.append(a)

        elif o in ["-f", "--file"]:
            file_name = a

        elif o in ["-c", "--controlleraddress"]:
            server_address = a

        elif o in ["-n", "--num"]:
            num_readings = int(a)

        elif o in ["-h", "--help"]:
            usage()
            sys.exit()

        else:
            assert False, "unhandled option"

    if types == []:
        assert False, "You must specify the type(s) of probe(s) you want to monitor."

    return types, file_name, server_address, num_readings

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
    types, file_name, server_address, num_readings = handle_cmdline_options()

    if len(types) == 1:
        logger.debug("Running in "+types[0]+" mode...")

    else:
        logger.debug("Monitoring multiple probes...")

    #Connect to server, if any.
    socket = None

    if server_address is not None:
        logger.info("Initialising connection to server, please wait...")
        print("Initialising connection to server, please wait...")
        socket = socket_tools.Sockets("Plug")
        socket.set_portnumber(30000)
        socket.set_server_address(server_address)
        socket.start_handler()

        logger.info("Will connect to server as soon as it becomes available.")
        print("Will connect to server as soon as it becomes available.")

    #Greet and get filename.
    logger.info("Greeting user and asking for filename if required...")
    file_name, file_handle = core_tools.greet_and_get_filename("Universal Monitor", file_name)
    logger.info("File name: "+file_name+"...")

    #Get settings for each type of monitor from the config file.
    logger.info("Setting up the probes...")

    monitors = []

    for _type in types:
        logger.info("Asserting that the specified type is valid...")
        assert _type in config.DATA, "Invalid Type Specified"

        probe, pins, reading_interval = config.DATA[_type]

        #Create the probe object.
        probe = probe(_type)

        #Set the probe up.
        probe.set_pins(pins)

        logger.info("Starting the monitor thread for "+_type+"...")

        #Start the monitor threads.
        #Keep references to these, but no need to with the probes.
        monitors.append(Monitor(_type, probe, num_readings, reading_interval))

    print("Synchronising with monitor threads...")

    #Wait until the first readings have come in so we are synchronised.
    for monitor in monitors:
        while not monitor.has_data():
            time.sleep(0.5)

    print("Starting to take readings. Please stand by...")

    logger.info("You should begin to see readings now...")

    #Set to sensible defaults to avoid errors.
    reading_time = reading_status = ""
    last_reading = "No Reading"
    old_reading_interval = 0

    #Keep tabs on its progress so we can write new readings to the file. TODO Sections of this code are duplicated w/ main.py, fix that. TODO Refactor while we're at it.
    try:
        for monitor in monitors:
            while monitor.is_running():
                #Check for new readings. NOTE: Later on, use the readings returned from this
                #for state history generation etc.
                core_tools.get_and_handle_new_reading(monitor, types[monitors.index(monitor)], file_handle, server_address, socket)

            #Wait until it's time to check for another reading.
            #I know we could use a long time.sleep(),
            #but this MUST be responsive to changes in the reading interval.
            count = 0

        while count < reading_interval:
            #This way, if our reading interval changes,
            #the code will respond to the change immediately.
            #Check if we have a new reading interval.
            if server_address is not None and socket.has_data():
                data = socket.read()

                if "Reading Interval" in data:
                    reading_interval = int(data.split()[-1])

                    #Only add a new line to the log if the reading interval changed.
                    if reading_interval != old_reading_interval:
                        old_reading_interval = reading_interval
                        logger.info("New reading interval: "+str(reading_interval))
                        print("New reading interval: "+str(reading_interval))

                        #Make sure all monitors use the new reading interval.
                        for monitor in monitors:
                            monitor.set_reading_interval(reading_interval)

                socket.pop()

            time.sleep(1)
            count += 1

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

    if server_address is not None:
        socket.request_handler_exit()
        socket.wait_for_handler_to_exit()
        socket.reset()

    #Reset GPIO pins.
    GPIO.cleanup()

if __name__ == "__main__":
    #Import here to prevent errors when generating documentation on non-RPi systems.
    import RPi.GPIO as GPIO

    logger = logging.getLogger('Universal Standalone Monitor '+VERSION)
    logging.basicConfig(filename='./universalmonitor.log', format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
    logger.setLevel(logging.INFO)

    #Catch any unexpected errors and log them so we know what happened.
    try:
        run_standalone()

    except:
        logger.critical("Unexpected error \n\n"+str(traceback.format_exc())+"\n\nwhile running. Exiting...")
        print("Unexpected error \n\n"+str(traceback.format_exc())+"\n\nwhile running. Exiting...")
