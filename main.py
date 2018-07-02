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
It communicates with buttspi over the network to gather float switch readings.

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
import sys
import logging
import traceback

#Do required imports.
import config

import Tools

from Tools import sensorobjects as sensor_objects
from Tools import monitortools as monitor_tools
from Tools import coretools as core_tools
from Tools import sockettools as socket_tools 

from Tools.monitortools import SocketsMonitor

try:
    #Allow us to generate documentation on non-RPi systems.
    import RPi.GPIO as GPIO

except ImportError:
    pass

#Define global variables.
VERSION = "0.9.2"
RELEASEDATE = "2/7/2018"

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
    system_id = config.SUMP_SITE_ID

    #Provide a connection for clients to connect to.
    logger.info("Creating a socket for clients to connect to, please wait...")
    socket = socket_tools.Sockets("Socket")
    socket.set_portnumber(30000)
    socket.start_handler()

    logger.debug("Done!")

    #Greet user.
    core_tools.greet_user("River System Control and Monitoring Software")

    #Create the devices.
    sump_probe = sensor_objects.HallEffectProbe("M0")
    butts_pump = sensor_objects.Motor("P0 (Butts Pump)") #SSR 1.
    main_pump = sensor_objects.Motor("P1 (Circulation Pump") #SSR 2.

    #Set the devices up.
    sump_probe.set_pins((15, 17, 27, 22, 23, 24, 10, 9, 25, 11))

    #Butts pump doesn't support PWM.
    butts_pump.set_pins(5, _input=False) #This is an output.
    butts_pump.set_pwm_available(False, -1)

    #Main pump doen't support PWM (no hardware yet).
    main_pump.set_pins(18, _input=False) #This is an output.
    main_pump.set_pwm_available(False, -1)

    #Reading interval.
    reading_interval = 300

    logger.info("The client(s) can connect whenever they're ready.")
    print("The client(s) can connect whenever they're ready.")

    logger.info("Starting to take readings...")
    print("Starting to take readings. Please stand by...")

    #Start the monitor thread. Take readings indefinitely.
    monitor = monitor_tools.Monitor(sump_probe, 0, reading_interval, system_id)

    #Start monitor threads for the socket (wendy house butts).
    monitors = []

    monitors.append(SocketsMonitor(socket, reading_interval, "G4", "FS0"))
    monitors.append(SocketsMonitor(socket, reading_interval, "G4", "M0"))

    #Wait until the first reading has come in so we are synchronised.
    while not monitor.has_data():
        time.sleep(0.5)

    #Sleep a few more seconds to make sure the client is ready.
    time.sleep(10)

    #Setup. Prevent errors.
    sump_reading = None
    butts_reading = None
    last_sump_reading = None

    #Keep tabs on its progress so we can write new readings to the file.
    try:
        while True:
            #Exit if the resistance probe monitor thread crashes for some reason.
            if not monitor.is_running():
                break

            #Check for new readings from the sump probe. TODO What to do if a fault is detected?
            while monitor.has_data():
                sump_reading = monitor.get_reading()

                #Check if the reading is different to the last reading.
                if sump_reading == last_sump_reading:
                    #Write a . to each file.
                    logger.info(".")
                    print(".", end='') #Disable newline when printing this message.

                else:
                    #Write any new readings to the file and to stdout.
                    logger.info(str(sump_reading))

                    print(sump_reading)

                    #Set last sump reading to this reading.
                    last_sump_reading = sump_reading

                #Flush buffers.
                sys.stdout.flush()

            #Check for new readings from buttspi.
            for wendy_butts_monitor in monitors:
                if wendy_butts_monitor.is_running():
                    #Check for new readings. NOTE: Later on, use the readings returned from this
                    #for state history generation etc.
                    reading = core_tools.get_and_handle_new_reading(wendy_butts_monitor, "test")

                    if reading != None:
                        if reading.get_id() == "G4:M0":
                            butts_reading = reading
                   
            #Logic.
            reading_interval = core_tools.do_control_logic(sump_reading, butts_reading, butts_pump,
                                                           main_pump, monitor, socket,
                                                           reading_interval)

            #Wait until it's time to check for another reading.
            time.sleep(reading_interval)

    except KeyboardInterrupt:
        #Ask the thread to exit.
        logger.info("Caught keyboard interrupt. Asking monitor thread to exit...")
        print("Caught keyboard interrupt. Asking monitor thread to exit.")
        print("This may take a little while, so please be patient...")

        monitor.request_exit(wait=True)

        for wendy_butts_monitor in monitors:
            wendy_butts_monitor.request_exit(wait=True)

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
