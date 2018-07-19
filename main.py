#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# River System Control and Monitoring Software Version 0.9.2
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

"""
This is the main part of the control software, and it currently manages
balancing water between the butts and the sump using a magnetic probe and
a solid state relay to control the butts pump. This software runs on sumppi.
It communicates with buttspi over the network to gather readings.

.. note::
      This program currently has LIMITED FUNCTIONALITY.
      It is a pre-production version that is being used
      to set up a test system that uses 2 RPis, one at
      the sump, with a hall effect probe and 2 SSRs connected
      and the other Pi is installed at the butts, and has
      a float switch. The sump pi will be using this program.
      Sump pi uses the first SSR to control the butts pump, and
      the second one is used to enable/disable the circulation
      pump. It will communicate with the other pi over a socket,
      and the other pi will be running universal_standalone_monitor.py.

.. module:: main.py
    :platform: Linux
    :synopsis: The main part of the control software.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>

"""

import time
import datetime
import logging
import traceback

#Do required imports.
import config

import Tools

from Tools import monitortools as monitor_tools
from Tools import coretools as core_tools
from Tools import sockettools as socket_tools

from Tools.monitortools import SocketsMonitor
from Tools.monitortools import Monitor

try:
    #Allow us to generate documentation on non-RPi systems.
    import RPi.GPIO as GPIO

except ImportError:
    pass

#Define global variables.
VERSION = "0.9.2"
RELEASEDATE = "19/7/2018"

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

    #Get system ID from config.
    system_id = config.SITE_SETTINGS["SUMP"]["ID"]

    #Provide a connection for clients to connect to.
    logger.info("Creating a socket for clients to connect to, please wait...")
    socket = socket_tools.Sockets("Socket")
    socket.set_portnumber(30000)
    socket.start_handler()

    logger.debug("Done!")

    #Greet user.
    core_tools.greet_user("River System Control and Monitoring Software")

    #Create the probe(s).
    probes = []

    for probe_id in config.SITE_SETTINGS["SUMP"]["Probes"]:
        probe_settings = config.SITE_SETTINGS["SUMP"]["Probes"][probe_id]

        _type = probe_settings["Type"]
        probe = probe_settings["Class"]
        pins = probe_settings["Pins"]
        reading_interval = probe_settings["Default Interval"]

        probe = probe(probe_id)
        probe.set_pins(pins)
        probes.append(probe)

    #Create the device(s).
    devices = []

    for device_id in config.SITE_SETTINGS["SUMP"]["Devices"]:
        device_settings = config.SITE_SETTINGS["SUMP"]["Devices"][device_id]

        _type = device_settings["Type"]
        device = device_settings["Class"]
        pins = device_settings["Pins"]

        device = device(device_id)

        #These are all pumps. FIXME make tidy later.
        #NB: PWM is implicitely disabled by default.
        device.set_pins(pins, _input=False)

        devices.append(device)

    #Reading interval.
    reading_interval = 15

    logger.info("Starting to take readings...")
    print("Starting to take readings. Please stand by...")

    logger.info("Waiting for client(s) to connect...")
    print("Waiting for client(s) to connect...")

    #Start monitor threads for the socket (wendy house butts).
    monitors = []

    monitors.append(SocketsMonitor(socket, "G4", "FS0"))
    monitors.append(SocketsMonitor(socket, "G4", "M0"))

    #And for our SUMP probe.
    for probe in probes:
        if probe.get_name() == "M0": #FIXME make id methods like in Reading to fix this issue w/ many probes in diff systems.
            monitors.append(Monitor(probe, 0, reading_interval, system_id))

    #Wait until the first readings have come in so we are synchronised.
    #NB: Will now wait for client connection.
    for each_monitor in monitors:
        while not each_monitor.has_data():
            time.sleep(0.5)

    #Sleep a few more seconds to make sure the client is ready.
    time.sleep(10)

    #Setup. Prevent errors.
    sump_reading = core_tools.Reading(str(datetime.datetime.now()), -1,
                                      "SUMP:M0", "0mm", "OK")
    butts_reading = core_tools.Reading(str(datetime.datetime.now()), -1,
                                       "G4:FS0", "True", "OK")

    #Keep tabs on its progress so we can write new readings to the file.
    try:
        at_least_one_monitor_running = True

        while at_least_one_monitor_running:
            #Check for new readings from all monitors.
            for monitor in monitors:
                if monitor.is_running():
                    #Check for new readings. NOTE: Later on, use the readings returned from this
                    #for state history generation etc.
                    reading = core_tools.get_and_handle_new_reading(monitor, "test")

                    #Keep the G4:FS0 & SUMP:M0 readings (used in control logic).
                    if reading != None:
                        if reading.get_id() == "G4:FS0":
                            butts_reading = reading

                        elif reading.get_id() == "SUMP:M0":
                            sump_reading = reading

            #Logic.
            reading_interval = core_tools.do_control_logic(sump_reading, butts_reading, devices,
                                                           monitors, socket, reading_interval)

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
    logger = logging.getLogger('River System Control Software '+VERSION)
    logging.basicConfig(filename='./logs//rivercontrolsystem.log',
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
