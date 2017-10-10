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

import time
import logging
import RPi.GPIO as GPIO

def run_standalone():
    #Do required imports.
    import universal_standalone_monitor_config as config

    import Tools

    from Tools import standalone_shared_functions as functions
    from Tools import sensorobjects
    from Tools import coretools as core_tools
    from Tools import sockettools as socket_tools
    from Tools import monitortools

    from Tools.sensorobjects import CapacitiveProbe
    from Tools.monitortools import Monitor

    Tools.sockettools.logger = logger

    #Handle cmdline options.
    _type, file_name, server_address, num_readings = functions.handle_cmdline_options("universal_standalone_monitor.py")

    logger.debug("Running in "+_type+" mode...")

    #Connect to server, if any.
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
    file_name, file_handle = core_tools.greet_and_get_filename("Universal Monitor ("+_type+")", file_name)
    logger.info("File name: "+file_name+"...")

    #Get settings for this type of monitor from the config file.
    logger.info("Asserting that the specified type is valid...")
    assert _type in config.DATA, "Invalid Type Specified"

    probe, pins, reading_interval = config.DATA[_type]

    logger.info("Setting up the probe...")

    #Create the probe object.
    probe = probe("Probey")

    #Set the probe up.
    probe.set_pins(pins)

    logger.info("Starting the monitor thread...")
    print("Starting to take readings. Please stand by...")

    #Start the monitor thread.
    monitor = Monitor(_type, probe, num_readings, reading_interval)

    #Wait until the first reading has come in so we are synchronised.
    while not monitor.has_data():
        time.sleep(0.5)

    logger.info("You should begin to see readings now...")

    #Keep tabs on its progress so we can write new readings to the file.
    try:
        while monitor.is_running():
            #Check for new readings.
            while monitor.has_data():
                reading = monitor.get_reading()

                #Write any new readings to the file and to stdout.
                logger.info("New reading: "+reading)
                print(reading)
                file_handle.write(reading+"\n")

                if server_address is not None:
                    socket.write(reading)

            #Wait until it's time to check for another reading.
            #I know we could use a long time.sleep(),
            #but this MUST be responsive to changes in the reading interval.
            count = 0

            while count < reading_interval:
                #This way, if our reading interval changes,
                #the code will respond to the change immediately.
                #Check if we have a new reading interval. TODO needs refactoring/optimisation.
                if server_address is not None:
                    if socket.has_data():
                        data = socket.read()

                        if "Reading Interval" in data:
                            reading_interval = int(data.split()[-1])
                            logger.info("New reading interval: "+str(reading_interval))
                            print("New reading interval: "+str(reading_interval))
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
    logger = logging.getLogger('Universal Standalone Monitor 0.9.1')
    logging.basicConfig(filename='./universalmonitor.log', format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
    logger.setLevel(logging.INFO)

    run_standalone()
