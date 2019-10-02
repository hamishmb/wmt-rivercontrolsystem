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

import config

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
    print("       -i <string>, --id=<string>    Specifiies the system ID eg \"G4\". If settings")
    print("                                     for this site aren't found in config.py an")
    print("                                     exception will be thrown. Mandatory.")
    print("       -t, --testing                 Enable testing mode. Disables certain checks on start-up,")
    print("                                     and hardware access via GPIO pins.")
    print("                                     Useful when running the software in test deployments.")
    print("       -d, --debug                   Enable debug mode")
    print("       -q, --quiet                   Log only warnings, errors, and critical errors")
    print("main.py is released under the GNU GPL Version 3")
    print("Version: "+config.VERSION+" ("+config.RELEASEDATE+")")
    print("Copyright (C) Wimborne Model Town 2017-2019")

def handle_cmdline_options():
    """
    This function is used to handle the commandline options passed
    to main.py.

    Valid commandline options to universal_standalone_monitor.py:
        -h, --help                          Calls the usage() function to display help information
                                            to the user.
        -i <string>, --id=<string>          Specifies the system ID eg "G4". If settings for this
                                            site aren't found in config.py an exception will be
                                            thrown. Mandatory.
        -t, --testing                       Enable testing mode. Disables certain checks on start-up,
                                            and hardware access via GPIO pins.
                                            Useful when running the software in test deployments.
        -d, --debug                         Enable debug mode.
        -q, --quiet                         Show only warnings, errors, and critical errors.

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
            logger.setLevel(logging.DEBUG)

        elif opt in ["-q", "--quiet"]:
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

    #Disable test mode if not specified.
    if not testing:
        config.TESTING = False

    return system_id

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
    system_id = handle_cmdline_options()

    #Reconfigure logging for module imported before we set the logger up.
    config.reconfigure_logging()

    #Do framework imports.
    from Tools import coretools as core_tools
    from Tools import sockettools as socket_tools
    from Tools import monitortools as monitor_tools

    #Import RPi.GPIO
    try:
        import RPi.GPIO as GPIO

    except ImportError:
        #Only allow import errors if we are testing.
        if not config.TESTING:
            logger.critical("Unable to import RPi.GPIO! Did you mean to use testing mode?")
            logger.critical("Exiting...")
            logging.shutdown()

            sys.exit("Unable to import RPi.GPIO! Did you mean to use testing mode? Exiting...")

        else:
            #Import dummy class.
            from Tools.testingtools import GPIO

    #Welcome message.
    logger.info("River Control System Version "+config.VERSION+" ("+config.RELEASEDATE+")")
    logger.info("System startup sequence initiated.")

    print("River Control System Version "+config.VERSION+" ("+config.RELEASEDATE+")")
    print("System Time: ", str(datetime.datetime.now()))
    print("System startup sequence initiated.")

    #If this isn't sumppi, start synchronising time with sumppi.
    if system_id != "SUMP":
        core_tools.SyncTime()

    #Create all sockets.
    logger.info("Creating sockets...")
    sockets = {}

    if config.SITE_SETTINGS[system_id]["HostingSockets"]:
        #We are a server, and we are hosting sockets.
        #Use information from the other sites to figure out what sockets to create.
        for site in config.SITE_SETTINGS:
            site_settings = config.SITE_SETTINGS[site]

            #If no server is defined for this site, skip it.
            if "SocketName" not in site_settings:
                continue

            socket = socket_tools.Sockets("Socket", site_settings["SocketName"])
            socket.set_portnumber(site_settings["ServerPort"])
            sockets[site_settings["SocketID"]] = socket

            socket.start_handler()

    #If a server is defined for this pi, connect to it.
    if "SocketName" in config.SITE_SETTINGS[system_id]:
        #Connect to the server.
        logger.info("Initialising connection to server, please wait...")
        print("Initialising connection to server, please wait...")
        socket = socket_tools.Sockets("Plug", config.SITE_SETTINGS[system_id]["ServerName"])
        socket.set_portnumber(config.SITE_SETTINGS[system_id]["ServerPort"])
        socket.set_server_address(config.SITE_SETTINGS[system_id]["ServerAddress"])
        socket.start_handler()

        logger.info("Will connect to server as soon as it becomes available.")
        print("Will connect to server as soon as it becomes available.")

    logger.debug("Done!")

    if system_id[0] == "V":
        #This is a gate valve - setup is different.
        logger.info("Setting up the gate valve...")
        valve = core_tools.setup_valve(system_id)

        probes = []

    else:
        #Create the probe(s).
        probes = core_tools.setup_devices(system_id)

        #Create the device(s).
        devices = core_tools.setup_devices(system_id, dictionary="Devices")

    #Default reading interval for all probes.
    reading_interval = config.SITE_SETTINGS[system_id]["Default Interval"]

    logger.info("Starting to take readings...")
    print("Starting to take readings. Please stand by...")

    logger.info("Waiting for peer(s) to connect...")
    print("Waiting for peer(s) to connect...")

    monitors = []

    #Start monitor threads for the sockets.
    if config.SITE_SETTINGS[system_id]["HostingSockets"]:
        for site in config.SITE_SETTINGS:
            site_settings = config.SITE_SETTINGS[site]

            #If no socket is defined for this site, skip it.
            if "SocketName" not in site_settings:
                continue

            #If there are probes to control, add monitors for all of them.
            if "Probes" in site_settings:
                for probe_name in site_settings["Probes"]:
                    monitors.append(monitor_tools.SocketsMonitor(sockets[site_settings["SocketID"]],
                                                                 probe_name.split(":")[0],
                                                                 probe_name.split(":")[1]))

            elif site_settings["Type"] == "Gate Valve":
                monitors.append(monitor_tools.SocketsMonitor(sockets[site_settings["SocketID"]],
                                                             site, site))

    #And for our SUMP probe.
    for probe in probes:
        monitors.append(monitor_tools.Monitor(probe, reading_interval, system_id))

    #Add monitor for the gate valve if needed.
    if system_id[0] == "V":
        monitors.append(monitor_tools.Monitor(valve, reading_interval, system_id))

    #Wait until the first readings have come in so we are synchronised.
    #TODO: We probably want to remove this - this was only ever meant to be temporary.
    #NB: Will now wait for the client connections.
    for each_monitor in monitors:
        while not each_monitor.has_data():
            time.sleep(0.5)

    #Set to sensible defaults to avoid errors.
    old_reading_interval = 0

    #Make a readings dictionary for temporary storage for the control logic function.
    #TODO Set up with default readings - need discussion first for some of these.
    #NB: datetime.datetime.now() is actually the wrong function to call, fix this.
    readings = {}

    readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "0mm",
                                             "OK")

    readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "True",
                                            "OK")

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
                if "SocketName" in config.SITE_SETTINGS[system_id]:
                    reading = core_tools.get_and_handle_new_reading(monitor, "test",
                                                                    config.SITE_SETTINGS
                                                                    [system_id]["ServerAddress"],
                                                                    socket)

                else:
                    reading = core_tools.get_and_handle_new_reading(monitor, "test")

                #Ignore empty readings.
                if reading is None:
                    continue

                #Keep all the readings we get, for the control logic.
                readings[reading.get_id()] = reading

            #Logic.
            if "ControlLogicFunction" in config.SITE_SETTINGS[system_id]:
                function = getattr(core_tools,
                                   config.SITE_SETTINGS[system_id]["ControlLogicFunction"])

                reading_interval = function(readings, devices, monitors, sockets, reading_interval)

            #Sumppi sets the reading interval, so it doesn't need to check if it is changing.
            #TODO: Do we still want this?
            if system_id == "SUMP":
                #Wait until it's time to check for another reading.
                time.sleep(reading_interval)

            else:
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

                        elif "Valve Position" in data:
                            valve_position = int(data.split()[-1])

                            logger.info("New valve position: "+str(valve_position))
                            print("New valve position: "+str(valve_position))

                            valve.set_position(valve_position)

                        socket.pop()

                    time.sleep(1)
                    count += 1

            #Check if at least one monitor is running.
            at_least_one_monitor_running = False

            for monitor in monitors:
                if monitor.is_running():
                    at_least_one_monitor_running = True

    except KeyboardInterrupt:
        #Ask the threads to exit.
        logger.info("Caught keyboard interrupt. Asking threads to exit...")
        print("Caught keyboard interrupt. Asking threads to exit.")
        print("This may take a little while, so please be patient...")

    #This triggers shutdown of everything else - no explicit call to each thread is needed.
    #The code below simply makes it easier to monitor what is shutting down.
    config.EXITING = True

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
        each_socket.wait_for_handler_to_exit()
        each_socket.reset()

    logger.info("Resetting GPIO pins...")
    print("Resetting GPIO pins...")

    if not config.TESTING:
        #Reset GPIO pins.
        GPIO.cleanup()

def init_logging():
    #NB: Can't use getLogger() any more because we want a custom handler.
    logger = logging.getLogger('River System Control Software')

    #Remove the console handler.
    logger.removeHandler(logger.handlers[0])

    #Set up the timed rotating file handler.
    rotator = logging.handlers.TimedRotatingFileHandler(filename='./logs/rivercontrolsystem.log',
                                                        when="midnight")

    logger.addHandler(rotator)

    #Set up the formatter.
    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
                                  datefmt='%d/%m/%Y %H:%M:%S')

    rotator.setFormatter(formatter)

    #Default logging level of INFO.
    logger.setLevel(logging.INFO)
    rotator.setLevel(logging.INFO)

    return logger

if __name__ == "__main__":
    #---------- SET UP THE LOGGER ----------
    logger = init_logging()

    #Catch any unexpected errors and log them so we know what happened.
    try:
        run_standalone()

    except Exception:
        logger.critical("Unexpected error \n\n"+str(traceback.format_exc())
                        +"\n\nwhile running. Exiting...")

        print("Unexpected error \n\n"+str(traceback.format_exc())+"\n\nwhile running. Exiting...")
