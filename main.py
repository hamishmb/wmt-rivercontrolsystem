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
This is the executable that is run to start the river control system software.

This software runs on all the sites, and the configuration in
config.py determines what actions are taken on each different
site.

.. module:: main.py
    :platform: Linux
    :synopsis: The executable that starts the control software.

.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>
.. moduleauthor:: Patrick Wigmore <pwbugreports@gmx.com>

"""

import sys
import getopt
import time
import datetime
import logging
import traceback

import config

from Tools import coretools
from Tools.coretools import rcs_print as print #pylint: disable=redefined-builtin
from Tools import dbtools
from Tools import logiccoretools
from Tools import sockettools
from Tools import monitortools
from Tools import loggingtools

from Logic import controllogic

#Import RPi.GPIO
try:
    from RPi import GPIO

except ImportError:
    #Only allow import errors if we are generating docs, testing, or on the NAS box.
    if __name__ == "__main__" and "NAS" not in sys.argv \
        and ("-t" not in sys.argv and "--testing" not in sys.argv):

        print("Unable to import RPi.GPIO! Did you mean to use testing mode? Exiting...",
              level="critical")

        sys.exit()

    else:
        #Import dummy GPIO class to fake hardware access.
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
    print("       -i <string>, --id=<string>    Specifiies the site ID eg \"G4\". If")
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

def inject_coretools_deps():
    """
    This function is used to inject dependencies into coretoolsto fix circular import issues.
    """
    coretools.sockettools = sockettools
    coretools.dbtools = dbtools
    coretools.logiccoretools = logiccoretools

def handle_cmdline_options():
    """
    This function is used to handle the commandline options passed
    to main.py. It also sets config.SITE_ID to the site ID passed
    over the commandline.

    Valid commandline options to main.py:
        See usage function in source code, or run main.py with the -h flag.

    Returns:
        str site_id.

            The site id.

    Raises:
        AssertionError, if there are unhandled options.

    Usage:

    >>> site_id = handle_cmdline_options()
    """

    site_id = None

    #Check all cmdline options are valid.
    try:
        opts = getopt.getopt(sys.argv[1:], "htdqi:",
                             ["help", "testing", "debug", "quiet", "id="])[0]

    except getopt.GetoptError as err:
        #Invalid option. Show the help message and then exit.
        #Show the error.
        print(str(err), level="error")
        usage()
        sys.exit(2)

    #Do setup. o=option, a=argument.
    testing = False

    for opt, arg in opts:
        if opt in ["-i", "--id"]:
            site_id = arg

        elif opt in ("-t", "--testing"):
            #Enable testing mode.
            testing = True
            print("Running in testing mode, hardware access simulated/disabled...",
                  level="critical")

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

    #Check site ID was specified.
    assert site_id is not None, "You must specify the site ID"

    #Check site ID is valid.
    assert site_id in config.SITE_SETTINGS, "Invalid site ID"

    config.TESTING = testing

    config.SITE_ID = site_id

    return site_id

def run():
    """
    This is the main part of the program.
    It coordinates setting up coretools, the sockets, the device objects, and the
    monitors, and connecting to the database.

    After that, it enters a monitor loop and coordinates repeatedly
    checking for new sensor data, updating the database, and calling
    the control logic function to make decisions about what to do based
    on this data.

    Finally, it coordinates clean teardown of the river system software,
    and execution of any site-wide actions, when requested.

    Raises:
        Nothing, hopefully. It's possible that an unhandled exception
        could be propagated through here though, so I recommend that
        you call this function like this at the current time:

        >>> try:
        >>>     run()
        >>>
        >>> except:
        >>>     #Handle the error and put it in the log file for debugging purposes.
        >>>     #Write the error to the standard output.
        >>>     #Exit the program.

    Usage:
        As above.
    """

    #Reconfigure logging for modules imported before we set the logger up.
    config.reconfigure_logging()

    #Inject dependencies for coretools.
    inject_coretools_deps()

    #Handle cmdline options.
    site_id = handle_cmdline_options()

    #Welcome message.
    logger.info("River Control System Version "+config.VERSION+" ("+config.RELEASEDATE+")")
    logger.info("System Time: "+str(datetime.datetime.now()))
    logger.info("System startup sequence initiated.")

    print("River Control System Version "+config.VERSION+" ("+config.RELEASEDATE+")")
    print("System Time:", str(datetime.datetime.now()))
    print("System startup sequence initiated.")

    #Get the default reading interval for this site.
    reading_interval = config.SITE_SETTINGS[site_id]["Default Interval"]

    #Make a readings dictionary for temporary storage for the control logic function.
    readings = {}

    #The NAS box needs more time to stabilise before we continue.
    #Wait another minute.
    if site_id == "NAS":
        print("Waiting 1 minute for NAS box to finish booting up (Press CTRL-C to skip)...")
        logger.info("Waiting 1 minute for NAS box to finish booting up (Press CTRL-C to skip)...")

        try:
            time.sleep(60)

        except KeyboardInterrupt:
            print("\nNAS box wait skipped as requested by user.")
            logger.info("NAS box wait skipped as requested by user.")

    #Run setup code.
    nas_socket, monitors, devices, timesync, loadmonitor = do_setup(site_id, reading_interval)

    logger.info("Entering main loop...")
    print("Entering main loop...")

    #Enter main loop.
    try:
        while not config.EXITING:
            #Initialise the database if needed.
            if not config.DBCONNECTION.initialised() and config.DBCONNECTION.is_ready():
                config.DBCONNECTION.initialise_db()

            #Check for new readings from all monitors and the database.
            coretools.get_local_readings(monitors, readings)

            #Run the control logic for this site.
            if "ControlLogicFunction" in config.SITE_SETTINGS[site_id]:
                function = getattr(controllogic,
                                   config.SITE_SETTINGS[site_id]["ControlLogicFunction"])

                reading_interval = function(readings, devices, monitors, reading_interval)

            #Count down the reading interval.
            coretools.wait_for_next_reading_interval(reading_interval, site_id,
                                                     nas_socket)

            #Check if shutdown, reboot, or update have been requested.
            #NOTE: config.EXITING is shut if so, ending the main loop.
            #TODO: Disabled as it isn't behaving reliably, uncomment when working.
            #coretools.prepare_sitewide_actions()

    except KeyboardInterrupt:
        #Teardown this site.
        logger.info("Caught keyboard interrupt. System teardown sequence initiated...")
        print("\nCaught keyboard interrupt. System teardown sequence initiated...")

    do_teardown(devices, monitors, timesync, loadmonitor)

    #---------- Do shutdown, update and reboot if needed ----------
    #TODO: Disabled as it isn't behaving reliably, uncomment when working.
    #If there were any sitewide actions to do, the river control system will have
    #finish tear down after the execution of this last function.
    #coretools.do_sitewide_actions()

    #If we reach this statement, we have torn down the system due to a user interrupt.
    print("USER INTERRUPT: Sequence complete. Process successful. Software exiting now.")
    logger.info("USER INTERRUPT: Sequence complete. Process successful. Software exiting now.")
    logging.shutdown()

def do_setup(site_id, reading_interval):
    """
    This function starts synchronising the system time with the NAS box,
    sets up the sockets, the device objects, the monitors, and connects
    to the database.

    Args:
        site_id (str):                  The site ID of this pi.
        reading_interval (int):         The default reading interval of this site.

    Returns:
        A list with the following members:

        1. Socket.                      The socket that connects to the NAS box (or False).
        2. list<BaseMonitorClass>.      A list of all the monitors for this site.
        3. list<BaseDeviceClass>.       A list of all the devices for this site.
        4. SyncTime.                    The time syncing thread.
        5. MonitorLoad.                 The load monitoring thread.

    Usage:
        >>> nas_socket, monitors, devices, timesync, loadmonitor = do_teardown("G6", 30)

    """
    #If this isn't the NAS box, start synchronising time with the NAS box.
    if site_id != "NAS":
        timesync = coretools.SyncTime(site_id)

    #Start monitoring system load.
    loadmonitor = coretools.MonitorLoad()

    #Create the socket(s).
    nas_socket = coretools.setup_sockets(site_id)

    #If this pi has a remote socket, log that we're going to start trying to connect now.
    #(As of August 2022, this is every system except the NAS box, and this socket always
    #connects to the NAS box).
    if "SocketName" in config.SITE_SETTINGS[site_id]:
        logger.info("Will connect to NAS box as soon as connection is available.")
        print("Will connect to NAS box as soon as connection is available.")

    #Create the probe(s).
    probes = coretools.setup_devices(site_id)

    #Create the device(s).
    devices = coretools.setup_devices(site_id, dictionary="Devices")

    logger.info("Connecting to database...")
    print("Connecting to database...")

    dbtools.DatabaseConnection(site_id)
    config.DBCONNECTION.start_thread()

    if site_id != "NAS":
        #Wait a little while for the system tick on boot on everything except the NAS box.
        coretools.wait_for_tick(nas_socket)

    #Start monitor threads for our local probes.
    monitors = []

    for probe in probes:
        monitors.append(monitortools.Monitor(probe, reading_interval, site_id))

    #Add monitor for the gate valve actuator if this is a gate valve pi.
    if site_id[0] == "V":
        for device in devices:
            monitors.append(monitortools.Monitor(device, reading_interval, site_id))

    #Run control logic set-up function, if it exists.
    if "ControlLogicSetupFunction" in config.SITE_SETTINGS[site_id]:
        function = getattr(controllogic,
                           config.SITE_SETTINGS[site_id]["ControlLogicSetupFunction"])

        function()

    return nas_socket, monitors, devices, timesync, loadmonitor

def do_teardown(devices, monitors, timesync, loadmonitor):
    """
    This function tears down the system, performing all tasks needed to get the river
    control system ready to be torn down cleanly. This includes the following tasks:

    - Setting config.EXITING to True to request all river control system threads to stop.
    - Waiting for the timesyncing service to stop.
    - Waiting for the load monitoring service to stop.
    - Waiting for the database connection to disconnect.
    - Waiting for all sockets to disconnect.
    - Waiting for any device management threads to stop.
    - Waiting for all device monitors to stop.
    - Cleaning up the GPIO pins (if on a pi).

    Args:
        devices (list<BaseDeviceClass>):        A list of all the devices for this site.
        monitors (list<BaseMonitorClass>):      A list of all the monitors for this site.
        timesync (SyncTime):                    The time syncing thread.
        loadmonitor (MonitorLoad):              The load monitoring thread.

    Usage:
        >>> do_teardown(list<BaseDeviceClass>, list<BaseMonitorClass>,
        >>>             <SyncTime<, <MonitorLoad>)

    """
    #This triggers teardown of everything else - no explicit call to each thread is needed.
    #The rest of the code below simply monitors the progress.
    config.EXITING = True

    #Wait for the timesync service to exit.
    logger.info("Waiting for timesync service to exit...")
    print("Waiting for timesync service to exit...")
    timesync.wait_exit()

    #Wait for load monitoring service to exit.
    logger.info("Waiting for load monitoring service to exit...")
    print("Waiting for load monitoring service to exit...")
    loadmonitor.wait_exit()

    #Wait for the database connection to exit.
    logger.info("Waiting for database connection to exit...")
    print("Waiting for database connection to exit...")
    config.DBCONNECTION.wait_exit()

    #Wait for the sockets to exit.
    logger.info("Waiting for socket(s) to exit...")
    print("Waiting for socket(s) to exit...")

    for each_socket in config.SOCKETSLIST:
        each_socket.wait_exit()

    #Wait for any device management threads to exit.
    logger.info("Waiting for device management thread(s) to exit...")
    print("Waiting for device management thread(s) to exit...")
    for device in devices:
        if device.has_mgmt_thread():
            device.mgmt_thread.wait_exit()

    #Wait for the monitors to exit.
    logger.info("Waiting for monitor(s) to exit...")
    print("Waiting for monitor(s) to exit...")

    for monitor in monitors:
        monitor.wait_exit()

    #Reset the GPIO pins.
    logger.info("Resetting GPIO pins...")
    print("Resetting GPIO pins...")

    if not config.TESTING and "NAS" not in sys.argv:
        #Reset GPIO pins.
        GPIO.cleanup()

    elif config.TESTING:
        logger.info("TEST MODE: GPIO reset skipped.")
        print("TEST MODE: GPIO reset skipped.")

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
        run()

    except Exception:
        logger.critical("Unexpected error \n\n"+str(traceback.format_exc())
                        +"\n\nwhile running. Exiting...")

        print("Unexpected error \n\n"+str(traceback.format_exc())
              + "\n\nwhile running. Exiting...", level="critical")
