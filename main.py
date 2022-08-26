#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# River System Control and Monitoring Software
# Copyright (C) 2017-2022 Wimborne Model Town
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
balancing water between the wendy butts and the sump. Further functionality
will be added shortly with more control logic functions.

This software runs on all the pis, and the NAS box, and the configuration in
config.py determines (for the most part) what actions are taken on each different
device.

.. module:: main.py
    :platform: Linux
    :synopsis: The main part of the control software.

.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>

"""

import sys
import getopt
import time
import datetime
import logging
import traceback

import config

from Tools import coretools
from Tools import monitortools
from Tools import loggingtools

from Logic import controllogic

#Import RPi.GPIO
try:
    from RPi import GPIO

except ImportError:
    #Only allow import errors if we are testing or on the NAS box.
    if "NAS" not in sys.argv and ("-t" not in sys.argv and "--testing" not in sys.argv):
        sys.exit("Unable to import RPi.GPIO! Did you mean to use testing mode? Exiting...")

    else:
        #Import dummy GPIO class to fake hardware access.
        print("WARNING: Running in test mode - hardware access simulated/disabled")
        from Tools.testingtools import GPIO #pylint: disable=ungrouped-imports

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
    print("       -i <string>, --id=<string>    Specifiies the system ID eg \"G4\". If")
    print("                                     settings for this site aren't found in")
    print("                                     config.py an exception will be thrown.")
    print("                                     Mandatory.\n")
    print("       -t, --testing                 Enable testing mode. Disables certain")
    print("                                     checks on start-up, and hardware access")
    print("                                     via GPIO pins. Useful when running the")
    print("                                     software in test deployments.\n")
    print("       -d, --debug                   Enable debug mode")
    print("       -q, --quiet                   Log only warnings, errors, and critical")
    print("                                     errors.\n")
    print("The WMT River Control System is released under the GNU GPL Version 3")
    print("Version: "+config.VERSION+" ("+config.RELEASEDATE+")")
    print("Copyright (C) Wimborne Model Town 2017-2022")

def handle_cmdline_options():
    """
    This function is used to handle the commandline options passed
    to main.py.

    Valid commandline options to main.py:
        See usage function in source code, or run main.py with the -h flag.

    Returns:
        string system_id.

            The system id.

    Raises:
        AssertionError, if there are unhandled options.

    Usage:

    >>> system_id = handle_cmdline_options()
    """

    system_id = None

    #Check all cmdline options are valid.
    try:
        opts = getopt.getopt(sys.argv[1:], "htdqi:",
                             ["help", "testing", "debug", "quiet", "id="])[0]

    except getopt.GetoptError as err:
        #Invalid option. Show the help message and then exit.
        #Show the error.
        print(str(err))
        usage()
        sys.exit(2)

    #Do setup. o=option, a=argument.
    testing = False

    for opt, arg in opts:
        if opt in ["-i", "--id"]:
            system_id = arg

        elif opt in ("-t", "--testing"):
            #Enable testing mode.
            testing = True
            logger.critical("Running in testing mode, hardware access simulated/disabled...")

        elif opt in ["-d", "--debug"]:
            config.DEBUG = True
            logger.setLevel(logging.DEBUG)
            handler.setLevel(logging.DEBUG)

        elif opt in ["-q", "--quiet"]:
            logger.setLevel(logging.WARNING)
            handler.setLevel(logging.WARNING)

        elif opt in ["-h", "--help"]:
            usage()
            sys.exit()

        else:
            assert False, "unhandled option"

    #Check system ID was specified.
    assert system_id is not None, "You must specify the system ID"

    #Check system ID is valid.
    assert system_id in config.SITE_SETTINGS, "Invalid system ID"

    #Disable test mode if not specified.
    if not testing:
        config.TESTING = False

    return system_id

def run_standalone():
    """
    This is the main part of the program.
    It coordinates setting up the sockets, the device objects, and the
    monitors, and connecting to the database.

    After that, it enters a monitor loop and repeatedly checks for new
    sensor data, updates the database, and calls the control logic function
    to make decisions about what to do based on this data.

    Finally, it coordiates clean shutdown of the river system when requested.

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
    system_id = handle_cmdline_options()
    config.SYSTEM_ID = system_id

    #Reconfigure logging for modules imported before we set the logger up.
    config.reconfigure_logging()

    #The NAS box needs more time to stabilise before we continue.
    #Wait another minute.
    if system_id == "NAS":
        print("Waiting 1 minute for NAS box to finish booting up (CTRL-C to skip)...")
        logger.info("Waiting 1 minute for NAS box to finish booting up (CTRL-C to skip)...")

        try:
            time.sleep(60)

        except KeyboardInterrupt:
            print("Skipping as requested by user...")
            logger.info("Skipping as requested by user...")

    #Welcome message.
    logger.info("River Control System Version "+config.VERSION+" ("+config.RELEASEDATE+")")
    logger.info("System Time: "+str(datetime.datetime.now()))
    logger.info("System startup sequence initiated.")

    print("River Control System Version "+config.VERSION+" ("+config.RELEASEDATE+")")
    print("System Time: ", str(datetime.datetime.now()))
    print("System startup sequence initiated.")

    #If this isn't the NAS box, start synchronising time with the NAS box.
    if system_id != "NAS":
        coretools.SyncTime(system_id)

    #Start monitoring system load.
    coretools.MonitorLoad()

    #Create the socket(s).
    sockets, local_socket = coretools.setup_sockets(system_id)

    if "SocketName" in config.SITE_SETTINGS[system_id]:
        print("Will connect to NAS box as soon as connection is available.")

    #Create the probe(s).
    probes = coretools.setup_devices(system_id)

    #Create the device(s).
    devices = coretools.setup_devices(system_id, dictionary="Devices")

    #Default reading interval for all probes.
    reading_interval = config.SITE_SETTINGS[system_id]["Default Interval"]

    logger.info("Connecting to database...")
    print("Connecting to database...")

    coretools.DatabaseConnection(system_id)
    config.DBCONNECTION.start_thread()

    if system_id != "NAS":
        #Wait a little while for the system tick on boot on everything except the NAS box.
        coretools.wait_for_tick(local_socket)

    time.sleep(5)

    logger.info("Starting to take readings...")
    print("Starting to take readings. Please stand by...")

    monitors = []

    #Start monitor threads for our local probes.
    for probe in probes:
        monitors.append(monitortools.Monitor(probe, reading_interval, system_id))

    #Add monitor for the gate valve if needed.
    if system_id[0] == "V":
        for device in devices:
            monitors.append(monitortools.Monitor(device, reading_interval, system_id))

    #Make a readings dictionary for temporary storage for the control logic function.
    readings = {}

    #Run logic set-up function, if it exists.
    if "ControlLogicSetupFunction" in config.SITE_SETTINGS[system_id]:
        function = getattr(controllogic,
                           config.SITE_SETTINGS[system_id]["ControlLogicSetupFunction"])

        function()

    #Enter main loop.
    try:
        while not config.EXITING:
            #Initialise the database if needed.
            if not config.DBCONNECTION.initialised() and config.DBCONNECTION.is_ready():
                config.DBCONNECTION.initialise_db()

            #Check for new readings from all monitors and the database.
            coretools.get_local_readings(monitors, readings)

            #Run the control logic for this site.
            if "ControlLogicFunction" in config.SITE_SETTINGS[system_id]:
                function = getattr(controllogic,
                                   config.SITE_SETTINGS[system_id]["ControlLogicFunction"])

                reading_interval = function(readings, devices, monitors, reading_interval)

            #Count down the reading interval.
            coretools.wait_for_next_reading_interval(reading_interval, system_id,
                                                     local_socket, sockets)

            #Check if shutdown, reboot, or update have been requested.
            #NOTE: config.EXITING is shut if so, ending the main loop.
            #TODO: Disabled as it isn't behaving reliably, uncomment when working.
            #coretools.prepare_sitewide_actions()

    except KeyboardInterrupt:
        #Shutdown this site.
        logger.info("Caught keyboard interrupt. System shutdown sequence initiated...")
        print("Caught keyboard interrupt. System shutdown sequence initiated...")

    #This triggers shutdown of everything else - no explicit call to each thread is needed.
    #The code below simply makes it easier to monitor what is shutting down.
    config.EXITING = True

    #Shutdown the monitors.
    for monitor in monitors:
        monitor.request_exit()

    logger.info("Waiting for monitor threads to exit...")
    print("Waiting for monitor threads to exit...")

    for monitor in monitors:
        monitor.request_exit(wait=True)

    #Shutdown the sockets.
    logger.info("Waiting for sockets to exit...")
    print("Waiting for sockets to exit...")

    for each_socket in sockets.values():
        each_socket.wait_for_handler_to_exit()
        each_socket.reset()

    #Reset the GPIO pins.
    logger.info("Resetting GPIO pins...")
    print("Resetting GPIO pins...")

    if not config.TESTING and "NAS" not in sys.argv:
        #Reset GPIO pins.
        GPIO.cleanup()

    elif config.TESTING:
        logger.info("TEST MODE: GPIO shutdown skipped.")
        print("TEST MODE: GPIO shutdown skipped.")

    #---------- Do shutdown, update and reboot if needed ----------
    #TODO: Disabled as it isn't behaving reliably, uncomment when working.
    #If there were any sitewide actions to do, the river control system will have
    #shut down after the execution of this last function.
    #coretools.do_sitewide_actions()

    #If we reach this statement, we have shut down due to a user interrupt.
    print("USER INTERRUPT: Sequence complete. Process successful. Shutting down now.")
    logger.info("USER INTERRUPT: Sequence complete. Process successful. Shutting down now.")
    logging.shutdown()

def init_logging():
    """
    Used as part of the logging initialisation process during startup.
    """

    logger = logging.getLogger('River System Control Software') #pylint: disable=redefined-outer-name

    #Remove the console handler.
    logger.handlers = []

    #Set up the timed rotating file handler.
    rotator = loggingtools.CustomLoggingHandler(filename='./logs/rivercontrolsystem.log',
                                                when="midnight")

    logger.addHandler(rotator)

    #Set up the formatter.
    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
                                  datefmt='%d/%m/%Y %H:%M:%S')

    rotator.setFormatter(formatter)

    #Default logging level of INFO.
    logger.setLevel(logging.INFO)
    rotator.setLevel(logging.INFO)

    return logger, rotator

if __name__ == "__main__":
    #---------- SET UP THE LOGGER ----------
    logger, handler = init_logging()

    #Catch any unexpected errors and log them so we know what happened.
    try:
        run_standalone()

    except Exception:
        logger.critical("Unexpected error \n\n"+str(traceback.format_exc())
                        +"\n\nwhile running. Exiting...")

        print("Unexpected error \n\n"+str(traceback.format_exc())+"\n\nwhile running. Exiting...")
