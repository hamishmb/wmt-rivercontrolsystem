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
import os
import shutil
import subprocess
import getopt
import time
import datetime
import logging
import traceback

import config
from Tools import loggingtools
from Tools import logiccoretools

from Logic import controllogic

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
    It imports everything required from the Tools package,
    and sets up the sockets, sets up the sensor objects, and the
    monitors, and connects to the database.

    After that, it enters a monitor loop and repeatedly checks for new
    sensor data, and then calls the control logic function
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

    #Do framework imports.
    from Tools import coretools as core_tools
    from Tools import sockettools as socket_tools
    from Tools import monitortools as monitor_tools

    #Import RPi.GPIO
    try:
        from RPi import GPIO

    except ImportError:
        #Only allow import errors if we are testing or on the NAS box.
        if not config.TESTING and "NAS" not in sys.argv:
            logger.critical("Unable to import RPi.GPIO! Did you mean to use testing mode?")
            logger.critical("Exiting...")
            logging.shutdown()

            sys.exit("Unable to import RPi.GPIO! Did you mean to use testing mode? Exiting...")

        else:
            #Import dummy GPIO class to fake hardware access.
            from Tools.testingtools import GPIO

    #Welcome message.
    logger.info("River Control System Version "+config.VERSION+" ("+config.RELEASEDATE+")")
    logger.info("System startup sequence initiated.")

    print("River Control System Version "+config.VERSION+" ("+config.RELEASEDATE+")")
    print("System Time: ", str(datetime.datetime.now()))
    print("System startup sequence initiated.")

    #If this isn't the NAS box, start synchronising time with the NAS box.
    if system_id != "NAS":
        core_tools.SyncTime(system_id)

    #Start monitoring system load.
    core_tools.MonitorLoad()

    #Create all sockets.
    logger.info("Creating sockets...")
    sockets = {}

    if config.SITE_SETTINGS[system_id]["HostingSockets"]:
        #We are a server, and we are hosting sockets.
        #Use info ation from the other sites to figure out what sockets to create.
        for site in config.SITE_SETTINGS:
            site_settings = config.SITE_SETTINGS[site]

            #If no server is defined for this site, skip it.
            if "SocketName" not in site_settings:
                continue

            socket = socket_tools.Sockets("Socket", system_id, site_settings["SocketName"])
            socket.set_portnumber(site_settings["ServerPort"])
            socket.set_server_address(site_settings["IPAddress"])
            sockets[site_settings["SocketID"]] = socket

            socket.start_handler()

    #If a server is defined for this pi, connect to it.
    if "SocketName" in config.SITE_SETTINGS[system_id]:
        #Connect to the server.
        logger.info("Initialising connection to server, please wait...")
        print("Initialising connection to server, please wait...")
        socket = socket_tools.Sockets("Plug", system_id,
                                      config.SITE_SETTINGS[system_id]["ServerName"])

        socket.set_portnumber(config.SITE_SETTINGS[system_id]["ServerPort"])
        socket.set_server_address(config.SITE_SETTINGS[system_id]["ServerAddress"])
        socket.start_handler()

        sockets[config.SITE_SETTINGS[system_id]["SocketID"]] = socket

        logger.info("Will connect to server as soon as it becomes available.")
        print("Will connect to server as soon as it becomes available.")

    logger.debug("Done!")

    #Create the probe(s).
    probes = core_tools.setup_devices(system_id)

    #Create the device(s).
    devices = core_tools.setup_devices(system_id, dictionary="Devices")

    #Default reading interval for all probes.
    reading_interval = config.SITE_SETTINGS[system_id]["Default Interval"]

    logger.info("Connecting to database...")
    print("Connecting to database...")

    core_tools.DatabaseConnection(system_id)
    config.DBCONNECTION.start_thread()

    if system_id != "NAS":
        #Request the latest system tick value and wait 180 seconds for it to come in.
        logger.info("Waiting up to 180 seconds for the system tick...")
        print("Waiting up to 180 seconds for the system tick...")

        if config.TESTING:
            logger.info("Running in test mode, waiting up to 27 seconds instead...")
            print("Running in test mode, waiting up to 27 seconds instead...")

        count = 0

        while config.TICK == 0 and count < 18:
            socket.write("Tick?")

            if socket.has_data():
                data = socket.read()

                if "Tick:" in data:
                    #Store tick sent from the NAS box.
                    config.TICK = int(data.split(" ")[1])

                    print("New tick: "+data.split(" ")[1])
                    logger.info("New tick: "+data.split(" ")[1])

                socket.pop()

            #Timeout almost instantly if in testing mode.
            if not config.TESTING:
                time.sleep(10)

            else:
                time.sleep(1.5)

            count += 1

        if config.TICK != 0:
            logger.info("Received tick")
            print("Received tick")

        else:
            logger.error("Could not get tick within 180 seconds!")
            print("Could not get tick within 180 seconds!")

    time.sleep(5)

    #Do this after system tick to allow database extra time to connect on first boot.
    if config.DBCONNECTION.is_ready():
        try:
            config.DBCONNECTION.initialise_db()

        except RuntimeError:
            print("Error: Couldn't initialise database!")
            logger.error("Error: Couldn't initialise database!")

    logger.info("Starting to take readings...")
    print("Starting to take readings. Please stand by...")

    monitors = []

    #Start monitor threads for our local probes.
    for probe in probes:
        monitors.append(monitor_tools.Monitor(probe, reading_interval, system_id))

    #Add monitor for the gate valve if needed.
    if system_id[0] == "V":
        for device in devices:
            monitors.append(monitor_tools.Monitor(device, reading_interval, system_id))

    #Make a readings dictionary for temporary storage for the control logic function.
    readings = {}

    readings["SUMP:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "SUMP:M0", "0mm",
                                             "OK")

    readings["G4:M0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:M0", "0mm",
                                           "OK")

    readings["G4:FS0"] = core_tools.Reading(str(datetime.datetime.now()), 0, "G4:FS0", "True",
                                            "OK")

    #Make a reading intervals dictionary for temporary storage of the reading intervals.
    #Assume 15 seconds by default.
    reading_intervals = {}

    for _siteid in config.SITE_SETTINGS:
        reading_intervals[_siteid] = 15

    #Run logic set-up function, if it exists.
    if "ControlLogicSetupFunction" in config.SITE_SETTINGS[system_id]:
        function = getattr(controllogic,
                           config.SITE_SETTINGS[system_id]["ControlLogicSetupFunction"])

        function()

    #Keep tabs on its progress so we can write new readings to the file.
    try:
        while not config.EXITING:
            #Check for new readings from all monitors and the database.
            for monitor in monitors:
                #Skip over any monitors that have stopped.
                if not monitor.is_running():
                    logger.error("Monitor for "+monitor.get_system_id()+":"+monitor.get_probe_id()
                                 + " is not running!")

                    print("Monitor for "+monitor.get_system_id()+":"+monitor.get_probe_id()
                          + " is not running!")

                    logiccoretools.log_event("Monitor for "+monitor.get_system_id()+":"
                                             + monitor.get_probe_id()+" is not running!",
                                             severity="ERROR")

                    continue

                #Check for new readings.
                #NOTE: Later on, use the readings returned from this
                #for state history generation etc.
                reading = core_tools.get_and_handle_new_reading(monitor, "test")

                #Ignore empty readings.
                if reading is None:
                    continue

                #Keep all the readings we get, for the control logic.
                readings[reading.get_id()] = reading

            #Initialise the database if possible.
            if not config.DBCONNECTION.initialised() and config.DBCONNECTION.is_ready():
                config.DBCONNECTION.initialise_db()

            #Logic.
            if "ControlLogicFunction" in config.SITE_SETTINGS[system_id]:
                function = getattr(controllogic,
                                   config.SITE_SETTINGS[system_id]["ControlLogicFunction"])

                reading_interval = function(readings, devices, monitors, sockets, reading_interval)

            #Keep watching for new messages from the socket while we could down the
            #reading interval.
            asked_for_tick = False
            count = 0

            while count < reading_interval:
                #This way, if our reading interval changes,
                #the code will respond to the change immediately.
                #Check if we have a new reading interval.
                if not asked_for_tick and (reading_interval - count) < 10 and system_id != "NAS":
                    #Get the latest system tick if we're in the last 10 seconds of the interval.
                    asked_for_tick = True
                    socket.write("Tick?")

                for _socket in sockets.values():
                    if _socket.has_data():
                        data = _socket.read()

                        if not isinstance(data, str):
                            continue

                        #-------------------- READING INTERVAL HANDLING --------------------
                        if "Interval:" in data:
                            #Save the reading interval to our list.
                            #Get the site id that this interval corresponds to.
                            _site = data.split(" ")[1]

                            #Save the interval to our list.
                            reading_intervals[_site] = int(data.split(" ")[2])

                            print("Received new interval from "+_site+": "+data.split(" ")[2])
                            logger.info("Received new interval from "+_site+": "+data.split(" ")[2])

                        elif "Interval?:" in data and system_id == "NAS":
                            #NAS box only: reply with the reading interval we have for that site.
                            requested_site = data.split(" ")[1]

                            _socket.write("Interval: "+requested_site+" "
                                          + str(reading_intervals[requested_site]))

                            print("Received new interval request for "+requested_site)
                            logger.info("Received new interval request for "+requested_site)

                        #-------------------- SYSTEM TICK HANDLING --------------------
                        elif data == "Tick?" and system_id == "NAS":
                            #NAS box only: reply with the current system tick when asked.
                            _socket.write("Tick: "+str(config.TICK))

                            print("Received request for current system tick")
                            logger.info("Received request for current system tick")

                        elif "Tick:" in data and system_id != "NAS":
                            #Everything except NAS box: store tick sent from the NAS box.
                            config.TICK = int(data.split(" ")[1])

                            print("New tick: "+data.split(" ")[1])
                            logger.info("New tick: "+data.split(" ")[1])

                        _socket.pop()

                time.sleep(1)
                count += 1

            #Check if shutdown, reboot, or update have been requested.
            #Database.
            try:
                state = logiccoretools.get_state(config.SYSTEM_ID, config.SYSTEM_ID)

            except RuntimeError:
                print("Error: Couldn't check for requested site actions!")
                logger.error("Error: Couldn't check for requested site actions!")

            else:
                if state is not None:
                    request = state[1]

                    if request.upper() == "SHUTDOWN":
                        config.SHUTDOWN = True

                    elif request.upper() == "SHUTDOWNALL":
                        config.SHUTDOWN = True
                        config.SHUTDOWNALL = True

                    elif request.upper() == "REBOOT":
                        config.REBOOT = True

                    elif request.upper() == "REBOOTALL":
                        config.REBOOT = True
                        config.REBOOTALL = True

                    elif request.upper() == "UPDATE":
                        config.UPDATE = True

            #Local files.
            config.SHUTDOWN = config.SHUTDOWN or os.path.exists("/tmp/.shutdown") or os.path.exists("/tmp/.shutdownall")

            config.SHUTDOWNALL = config.SHUTDOWNALL or os.path.exists("/tmp/.shutdownall")

            config.REBOOT = config.REBOOT or os.path.exists("/tmp/.reboot") or os.path.exists("/tmp/.rebootall")

            config.REBOOTALL = config.REBOOTALL or os.path.exists("/tmp/.rebootall")

            config.UPDATE = config.UPDATE or os.path.exists("/tmp/.update")

            #If this is the NAS box, make the update available to pis and signal that they
            #should update using the database.
            if config.UPDATE and system_id == "NAS":
                #Make the update available to the pis at
                #http://192.168.0.25/rivercontrolsystem.tar.gz
                logger.info("Making new software available to all pis using webserver...")
                cmd = subprocess.run(["ln", "-s", "/mnt/HD/HD_a2/rivercontrolsystem.tar.gz",
                                      "/var/www"],
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     check=False)

                stdout = cmd.stdout.decode("UTF-8", errors="ignore")

                if cmd.returncode != 0:
                    print("Error! Unable to host software update on webserver. "
                          + "Error was:\n"+stdout+"\n")

                    logger.critical("Error! Unable to host software update on webserver. "
                                    + "Error was:\n"+stdout+"\n")

                #Signal that we are updating.
                try:
                    logiccoretools.log_event("Updating...")
                    logiccoretools.update_status("Up, CPU: "+config.CPU+"%, MEM: "
                                                 +config.MEM+" MB", "OK", "Updating")

                except RuntimeError:
                    print("Error: Couldn't update site status or event log!")
                    logger.error("Error: Couldn't update site status or event log!")

                for site_id in config.SITE_SETTINGS:
                    try:
                        logiccoretools.attempt_to_control(site_id, site_id, "Update")

                    except RuntimeError:
                        print("Error: Couldn't request update for "+site_id+"!")
                        logger.error("Error: Couldn't request update for "+site_id+"!")

            elif config.UPDATE and system_id != "NAS":
                #Download the update from the NAS box.
                logger.info("Downloading software update from NAS box...")
                cmd = subprocess.run(["wget", "-O", "/tmp/rivercontrolsystem.tar.gz",
                                      "http://192.168.0.25/rivercontrolsystem.tar.gz"],
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

                stdout = cmd.stdout.decode("UTF-8", errors="ignore")

                if cmd.returncode != 0:
                    print("Error! Unable to download software update. "
                          + "Error was:\n"+stdout+"\n")

                    logger.critical("Error! Unable to download software update. "
                                    + "Error was:\n"+stdout+"\n")

                #Signal that we got it.
                try:
                    logiccoretools.log_event("Updating...")
                    logiccoretools.update_status("Up, CPU: "+config.CPU+"%, MEM: "
                                                 +config.MEM+" MB", "OK", "Updating")

                except RuntimeError:
                    print("Error: Couldn't update site status or event log!")
                    logger.error("Error: Couldn't update site status or event log!")

            elif config.REBOOT:
                try:
                    logiccoretools.log_event("Rebooting...")
                    logiccoretools.update_status("Down for reboot", "N/A", "Rebooting")

                except RuntimeError:
                    print("Error: Couldn't update site status or event log!")
                    logger.error("Error: Couldn't update site status or event log!")

                if system_id == "NAS" and config.REBOOTALL:
                    for site_id in config.SITE_SETTINGS:
                        try:
                            logiccoretools.attempt_to_control(site_id, site_id, "Reboot")

                        except RuntimeError:
                            print("Error: Couldn't request reboot for "+site_id+"!")
                            logger.error("Error: Couldn't request reboot for "+site_id+"!")

            elif config.SHUTDOWN:
                try:
                    logiccoretools.log_event("Shutting down...")
                    logiccoretools.update_status("Off (shutdown requested)", "N/A", "Shutting Down")

                except RuntimeError:
                    print("Error: Couldn't update site status or event log!")
                    logger.error("Error: Couldn't update site status or event log!")

                if system_id == "NAS" and config.SHUTDOWNALL:
                    for site_id in config.SITE_SETTINGS:
                        try:
                            logiccoretools.attempt_to_control(site_id, site_id, "Shutdown")

                        except RuntimeError:
                            print("Error: Couldn't request poweroff for "+site_id+"!")
                            logger.error("Error: Couldn't request poweroff for "+site_id+"!")

            if config.SHUTDOWN or config.REBOOT or config.UPDATE:
                try:
                    os.remove("/tmp/.shutdown")

                except (OSError, IOError):
                    pass

                try:
                    os.remove("/tmp/.shutdownall")

                except (OSError, IOError):
                    pass

                try:
                    os.remove("/tmp/.reboot")

                except (OSError, IOError):
                    pass

                try:
                    os.remove("/tmp/.rebootall")

                except (OSError, IOError):
                    pass

                try:
                    os.remove("/tmp/.update")

                except (OSError, IOError):
                    pass

                config.EXITING = True

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

    if not config.TESTING and "NAS" not in sys.argv:
        #Reset GPIO pins.
        GPIO.cleanup()

    #---------- Do shutdown, update and reboot if needed ----------
    if config.SHUTDOWN:
        print("Shutting down...")
        logger.info("Shutting down...")

        if system_id == "NAS" and not config.SHUTDOWNALL:
            subprocess.run(["ash", "/home/admin/shutdown.sh"], check=False)

        elif system_id == "NAS" and config.SHUTDOWNALL:
            #Wait until all the pis have started to shut down.
            #Restart database thread to check.
            config.EXITING = False
            core_tools.DatabaseConnection(system_id)
            config.DBCONNECTION.start_thread()

            print("Waiting for pis to begin shutting down...")
            logger.info("Waiting for pis to begin shutting down...")

            done = []

            while True:
                for site_id in config.SITE_SETTINGS:
                    if site_id == "NAS" or site_id in done:
                        continue

                    try:
                        status = logiccoretools.get_status(site_id)

                    except RuntimeError:
                        print("Error: Couldn't get "+site_id+" site status!")
                        logger.error("Error: Couldn't get "+site_id+" site status!")

                    else:
                        if status is not None:
                            action = status[2]

                            if action.upper() == "SHUTTING DOWN":
                                print("Done: "+site_id)
                                logger.info("Done: "+site_id)
                                done.append(site_id)

                #When all have shut down (ignoring NAS), break out.
                if done and len(done) == len(config.SITE_SETTINGS.keys()) - 1:
                    break

                time.sleep(5)

            subprocess.run(["ash", "/home/admin/shutdown.sh"], check=False)

        else:
            subprocess.run(["poweroff"], check=False)

    elif config.REBOOT:
        print("Restarting...")
        logger.info("Restarting...")

        if system_id == "NAS" and not config.REBOOTALL:
            subprocess.run(["ash", "/home/admin/reboot.sh"], check=False)

        elif system_id == "NAS" and config.REBOOTALL:
            #Wait until all the pis have started to reboot.
            #Restart database thread to check.
            config.EXITING = False
            core_tools.DatabaseConnection(system_id)
            config.DBCONNECTION.start_thread()

            print("Waiting for pis to begin rebooting...")
            logger.info("Waiting for pis to begin rebooting...")

            done = []

            while True:
                for site_id in config.SITE_SETTINGS:
                    if site_id == "NAS" or site_id in done:
                        continue

                    try:
                        status = logiccoretools.get_status(site_id)

                    except RuntimeError:
                        print("Error: Couldn't get "+site_id+" site status!")
                        logger.error("Error: Couldn't get "+site_id+" site status!")

                    else:
                        if status is not None:
                            action = status[2]

                            if action.upper() == "REBOOTING":
                                print("Done: "+site_id)
                                logger.info("Done: "+site_id)
                                done.append(site_id)

                #When all have rebooted (ignoring NAS), break out.
                if done and len(done) == len(config.SITE_SETTINGS.keys()) - 1:
                    break

                time.sleep(5)

            subprocess.run(["ash", "/home/admin/reboot.sh"], check=False)

        else:
            subprocess.run(["reboot"], check=False)

    elif config.UPDATE:
        print("Applying update...")
        logger.info("Applying update...")

        if system_id == "NAS":
            #Wait until all the pis have downloaded the update.
            #Restart database thread to check.
            config.EXITING = False
            core_tools.DatabaseConnection(system_id)
            config.DBCONNECTION.start_thread()

            print("Waiting for pis to download the update...")
            logger.info("Waiting for pis to download the update...")

            done = []

            while True:
                for site_id in config.SITE_SETTINGS:
                    if site_id == "NAS" or site_id in done:
                        continue

                    try:
                        status = logiccoretools.get_status(site_id)

                    except RuntimeError:
                        print("Error: Couldn't get "+site_id+" site status!")
                        logger.error("Error: Couldn't get "+site_id+" site status!")

                    else:
                        if status is not None:
                            action = status[2]

                            if action.upper() == "UPDATING":
                                print("Done: "+site_id)
                                logger.info("Done: "+site_id)
                                done.append(site_id)

                #When all have grabbed the file (ignoring NAS), break out.
                if done and len(done) == len(config.SITE_SETTINGS.keys()) - 1:
                    break

                time.sleep(5)

            #Move files into place.
            if os.path.exists("/mnt/HD/HD_a2/rivercontrolsystem.old"):
                logger.info("Removing old software backup...")
                shutil.rmtree("/mnt/HD/HD_a2/rivercontrolsystem.old")

            logger.info("Backing up existing software to rivercontrolsystem.old...")
            cmd = subprocess.run(["mv", "/mnt/HD/HD_a2/rivercontrolsystem",
                                  "/mnt/HD/HD_a2/rivercontrolsystem.old"],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

            stdout = cmd.stdout.decode("UTF-8", errors="ignore")

            if cmd.returncode != 0:
                print("Error! Unable to backup existing software. "
                      + "Error was:\n"+stdout+"\n")

                logger.critical("Error! Unable to backup existing software. "
                                + "Error was:\n"+stdout+"\n")

            logger.info("Extracting new software...")
            cmd = subprocess.run(["tar", "-xf", "/mnt/HD/HD_a2/rivercontrolsystem.tar.gz", "-C",
                                  "/mnt/HD/HD_a2"], stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, check=False)

            stdout = cmd.stdout.decode("UTF-8", errors="ignore")

            if cmd.returncode != 0:
                print("Error! Unable to extract new software. "
                      + "Error was:\n"+stdout+"\n")

                logger.critical("Error! Unable to extract new software. "
                                + "Error was:\n"+stdout+"\n")

            #Clean up.
            if os.path.exists("/mnt/HD/HD_a2/rivercontrolsystem.tar.gz"):
                logger.info("Removing software tarball...")
                os.remove("/mnt/HD/HD_a2/rivercontrolsystem.tar.gz")

            #Reboot.
            print("Restarting...")
            logger.info("Restarting...")
            subprocess.run(["ash", "/home/admin/reboot.sh"], check=False)

        else:
            #Move files into place.
            if os.path.exists("/mnt/HD/HD_a2/rivercontrolsystem.old"):
                logger.info("Removing old software backup...")
                shutil.rmtree("/mnt/HD/HD_a2/rivercontrolsystem.old")

            logger.info("Backing up existing software to rivercontrolsystem.old...")
            cmd = subprocess.run(["mv", "/home/pi/rivercontrolsystem",
                                  "/home/pi/rivercontrolsystem.old"],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

            stdout = cmd.stdout.decode("UTF-8", errors="ignore")

            if cmd.returncode != 0:
                print("Error! Unable to backup existing software. "
                      + "Error was:\n"+stdout+"\n")

                logger.critical("Error! Unable to backup existing software. "
                                + "Error was:\n"+stdout+"\n")

            logger.info("Extracting new software...")
            cmd = subprocess.run(["tar", "-xf", "/tmp/rivercontrolsystem.tar.gz", "-C",
                                  "/home/pi"],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

            stdout = cmd.stdout.decode("UTF-8", errors="ignore")

            if cmd.returncode != 0:
                print("Error! Unable to extract new software. "
                      + "Error was:\n"+stdout+"\n")

                logger.critical("Error! Unable to extract new software. "
                                + "Error was:\n"+stdout+"\n")

            #Clean up.
            if os.path.exists("/mnt/HD/HD_a2/rivercontrolsystem.tar.gz"):
                logger.info("Removing software tarball...")
                os.remove("/mnt/HD/HD_a2/rivercontrolsystem.tar.gz")

            #Reboot.
            print("Restarting...")
            logger.info("Restarting...")
            subprocess.run(["reboot"], check=False)

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
