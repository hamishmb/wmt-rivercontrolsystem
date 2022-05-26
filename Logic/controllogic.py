#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Control Logic integration and setup functions for the River System Control and Monitoring Software
# Copyright (C) 2020 Wimborne Model Town
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3 or,
# at your option, any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#pylint: disable=logging-not-lazy
#
#Reason (logging-not-lazy): Harder to understand the logging statements that way.

"""
This is the controllogic module, which contains control logic integration and setup functions.

.. module:: controllogic.py
    :platform: Linux
    :synopsis: Contains control logic integration and setup functions.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>
"""

import sys
import os
import logging
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.abspath('..'))

import config
from Tools import logiccoretools

from . import stagepilogic, temptopuplogic

#Don't ask for a logger name, so this works with all modules.
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

for handler in logging.getLogger('River System Control Software').handlers:
    logger.addHandler(handler)

def reconfigure_logger():
    """
    Reconfigures the logging level for this module.
    """

    logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

    for handler in logging.getLogger('River System Control Software').handlers:
        logger.addHandler(handler)

#----- NAS Control Logic -----
def nas_control_logic(readings, devices, monitors, sockets, reading_interval):
    """
    This control logic runs on the NAS box, and is responsible for:

    - Setting and restoring the system tick.
    - Freeing locks that have expired (locks can only be held for a maximum of TBD minutes). Not yet implemented.
    - Monitoring the temperature of the NAS box and its drives.

    """
    #---------- System tick ----------
    #Restore the system tick from the database if needed.
    if config.TICK == 0:
        #Get the latest tick from the system tick table.
        try:
            config.TICK = logiccoretools.get_latest_tick()

        except RuntimeError:
            print("Error: Couldn't get latest tick!")
            logger.error("Error: Couldn't get latest tick!")

        #Log if we managed to get a newer tick.
        if config.TICK not in (0, None):
            print("Restored system tick from database: "+str(config.TICK))
            logger.info("Restored system tick from database: "+str(config.TICK))

            try:
                logiccoretools.log_event("Restored system tick from database: "+str(config.TICK))

            except RuntimeError:
                print("Error: Couldn't log event saying that tick was restored to "
                      + str(config.TICK)+"!")

                logger.error("Error: Couldn't log event saying that tick was restored to "
                             + str(config.TICK)+"!")

    if config.TICK is None:
        config.TICK = 0

    #Increment the system tick by 1.
    config.TICK += 1

    #Reset tick if we're getting near the limit (2^31, assuming signed integers for safety).
    #(https://docs.oracle.com/cd/E19078-01/mysql/mysql-refman-5.1/data-types.html#numeric-types)
    if config.TICK >= 2147483600:
        print("Reset tick to zero as near limit")
        logger.warning("Reset tick to zero as near limit")

        try:
            logiccoretools.log_event("Reset system tick to zero as near to limit",
                                     severity="WARNING")

        except RuntimeError:
            print("Error: Couldn't log event saying that tick was reset!")
            logger.error("Error: Couldn't log event saying that tick was reset!")

        config.TICK = 0

    try:
        logiccoretools.store_tick(config.TICK)

    except RuntimeError:
        print("Error: Couldn't store current tick!")
        logger.error("Error: Couldn't store current tick!")

    #---------- Free locks that have expired ----------
    #TODO Not yet implemented, do later if needed.

    #---------- Monitor the temperature of the NAS box and the drives ----------
    #System board temp.
    cmd = subprocess.run(["temperature_monitor", "-b"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

    sys_temp = cmd.stdout.decode("UTF-8", errors="ignore").split()[-1]

    #HDD 0 temp.
    cmd = subprocess.run(["temperature_monitor", "-c", "0"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

    hdd0_temp = cmd.stdout.decode("UTF-8", errors="ignore").split()[-1]

    #HDD 1 temp.
    cmd = subprocess.run(["temperature_monitor", "-c", "1"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

    hdd1_temp = cmd.stdout.decode("UTF-8", errors="ignore").split()[-1]

    #Log temperatures and update in system status table.
    #Check if any of the temps are > 50C.
    hot = False

    for temp in (sys_temp, hdd0_temp, hdd1_temp):
        if int(temp) > 50:
            hot = True

    if not hot:
        logger.info("Temperatures: sys: "+sys_temp+", hdd0: "+hdd0_temp+", hdd1: "+hdd1_temp)

        try:
            logiccoretools.update_status("Up, temps: ("+sys_temp+"/"+hdd0_temp+"/"+hdd1_temp
                                         + "), CPU: "+config.CPU+"%, MEM: "+config.MEM+" MB",
                                         "OK", "None")

        except RuntimeError:
            print("Error: Couldn't update site status!")
            logger.error("Error: Couldn't update site status!")

    else:
        logger.warning("High Temperatures! sys: "+sys_temp+", hdd0: "+hdd0_temp
                       + ", hdd1: "+hdd1_temp)

        try:
            logiccoretools.update_status("Up, HIGH temps: ("+sys_temp+"/"+hdd0_temp+"/"+hdd1_temp
                                         + "), CPU: "+config.CPU+"%, MEM: "+config.MEM+" MB",
                                         "OK", "None")

            logiccoretools.log_event("NAS Box getting hot! Temps: sys: "+sys_temp+", hdd0: "+hdd0_temp
                                     + ", hdd1: "+hdd1_temp, severity="WARNING")

        except RuntimeError:
            print("Error: Couldn't update site status or log event!")
            logger.error("Error: Couldn't update site status or log event!")

    #NAS/tick interval is 15 seconds.
    return 15

#----- Generic Valve Control Logic (not for Matrix pump) -----
def valve_control_logic(readings, devices, monitors, sockets, reading_interval):
    """
    This control logic is generic and runs on all the gate valves. It does the following:

    - Polls the database and sets valve positions upon request.

    """

    #Get the sensor name for this valve.
    for valve in config.SITE_SETTINGS[config.SYSTEM_ID]["Devices"]:
        valve_id = valve.split(":")[1]

    position = None

    #Check if there's a request for a new valve position.
    try:
        state = logiccoretools.get_state(config.SYSTEM_ID, valve_id)

    except RuntimeError:
        print("Error: Couldn't get site status!")
        logger.error("Error: Couldn't get site status!")

    else:
        if state is not None:
            request = state[1]

            if request != "None":
                position = int(request.replace("%", ""))

                #There's only one device for gate valve pis, the gate valve, so take a shortcut.
                #Only do anything if the position has changed.
                if position != devices[0].get_requested_position():
                    devices[0].set_position(position)

                    logger.info("New valve position: "+str(position))
                    print("New valve position: "+str(position))

                    try:
                        logiccoretools.log_event(config.SYSTEM_ID+": New valve position: "+str(position))

                    except RuntimeError:
                        print("Error: Couldn't log event!")
                        logger.error("Error: Couldn't log event!")

    if position is not None:
        try:
            logiccoretools.update_status("Up, CPU: "+config.CPU+"%, MEM: "+config.MEM+" MB",
                                         "OK", "Position requested: "+str(position))

        except RuntimeError:
            print("Error: Couldn't update site status!")
            logger.error("Error: Couldn't update site status!")

    else:
        try:
            logiccoretools.update_status("Up, CPU: "+config.CPU+"%, MEM: "+config.MEM+" MB",
                                         "OK", "None")

        except RuntimeError:
            print("Error: Couldn't update site status!")
            logger.error("Error: Couldn't update site status!")

    #Unsure how to decide the interval, so just setting to 15 seconds TODO.
    return 15

#----- Generic control logic for pis that only do monitoring -----
def generic_control_logic(readings, devices, monitors, sockets, reading_interval):
    """
    This control logic is generic and runs on all the monitoring-only pis. It does the following:

    - Updates the pi status in the database.

    """

    try:
        logiccoretools.update_status("Up, CPU: "+config.CPU+"%, MEM: "+config.MEM+" MB",
                                     "OK", "None")

    except RuntimeError:
        print("Error: Couldn't update site status!")
        logger.error("Error: Couldn't update site status!")

    #Unsure how to decide the interval, so just setting to 15 seconds TODO.
    return 15

#----- Sump Pi Control Logic -----
#NB: All in here because this is old-style logic that doesn't
#make use of setup and integration functions, unlike Patrick's logic (below).
def sumppi_control_logic(readings, devices, monitors, sockets, reading_interval):
    """
    This function is used to decides what action to take based
    on the readings it is passed.

    The butts pump is turned on when the sump level >= 600 mm, and
    turned off when it reaches 400 mm. The circulation pump is
    turned on when the sump level >= 300, and otherwise the
    circulation pump will be turned off.

    The reading intervals at both the sumppi and the buttspi end
    are controlled and set here as well.

    .. note::
        Just added support for SSR 2 (circulation pump).
    .. note 2:
        Added support for water backup strategy (TJC, 27/04/2022)

    Otherwise, nothing currently happens because there is nothing
    else we can take control of at the moment.

    Args:
        readings (list):                A list of the latest readings for each probe/device.

        devices  (list):                A list of all master pi device objects.

        monitors (list):                A list of all master pi monitor objects.

        sockets (list of Socket):       A list of Socket objects that represent
                                        the data connections between pis. Passed
                                        here so we can control the reading
                                        interval at that end.

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = sumppi_control_logic(<listofreadings>,
        >>>                                         <listofprobes>, <listofmonitors>,
        >>>                                         <listofsockets>, <areadinginterval)

    """

    # Call water backup function if not Opening Hours
    timenow = datetime.now()
    
    hour = int(timenow.hour)
    
    if (hour >= 16 or hour <= 7):
        return sumppi_water_backup_control_logic(readings, devices, monitors, reading_interval)

    #Remove the 'mm' from the end of the reading value and convert to int.
    sump_reading = int(readings["SUMP:M0"].get_value().replace("m", ""))

    try:
        butts_reading = int(logiccoretools.get_latest_reading("G4", "M0").get_value().replace("m", ""))

    except (RuntimeError, AttributeError):
        print("Error: Error trying to get latest G4:M0 reading!")
        logger.error("Error: Error trying to get latest G4:M0 reading!")

        #Default to empty instead.
        butts_reading = 0

    try:
        butts_float_reading = logiccoretools.get_latest_reading("G4", "FS0").get_value()

    except (RuntimeError, AttributeError):
        print("Error: Error trying to get latest G4:FS0 reading!")
        logger.error("Error: Error trying to get latest G4:FS0 reading!")

        #Default to empty instead.
        butts_float_reading = "False"

    #Get a reference to both pumps.
    main_pump = None
    butts_pump = None

    for device in devices:
        if device.get_id() == "SUMP:P0":
            butts_pump = device

        elif device.get_id() == "SUMP:P1":
            main_pump = device

    #Check that we got references to both pumps.
    assert main_pump is not None
    assert butts_pump is not None

    #Check that the devices list is not empty.
    assert devices

    #Check that the reading interval is positive, and greater than 0.
    assert reading_interval > 0

    #Check that the butts float switch reading is sane.
    assert butts_float_reading in ("True", "False")

    if sump_reading >= 600:
        #Level in the sump is getting high.
        logger.warning("Water level in the sump ("+str(sump_reading)+") >= 600 mm!")
        print("Water level in the sump ("+str(sump_reading)+") >= 600 mm!")

        #Make sure the main circulation pump is on.
        logger.info("Turning the main circulation pump on, if it was off...")
        print("Turning the main circulation pump on, if it was off...")

        #Close the wendy butts gate valve.
        logger.info("Closing the wendy butts gate valve...")
        print("Closing the wendy butts gate valve...")

        try:
            logiccoretools.attempt_to_control("VALVE4", "V4", "0%")

        except RuntimeError:
            print("Error: Error trying to control valve V4!")
            logger.error("Error: Error trying to control valve V4!")

        main_pump.enable()

        #Pump some water to the butts if they aren't full.
        #If they are full, do nothing and let the sump overflow.
        if butts_float_reading == "False":
            #Pump to the butts.
            logger.warning("Pumping water to the butts...")
            print("Pumping water to the butts...")
            butts_pump.enable()

            logger.warning("Changing reading interval to 30 seconds so we can "
                           +"keep a close eye on what's happening...")

            print("Changing reading interval to 30 seconds so we can keep a "
                  +"close eye on what's happening...")

            reading_interval = 30

        else:
            #Butts are full. Do nothing, but warn user.
            butts_pump.disable()

            logger.warning("The water butts are full. Allowing the sump to overflow.")
            print("The water butts are full.")
            print("Allowing the sump to overflow.")

            logger.warning("Setting reading interval to 1 minute...")
            print("Setting reading interval to 1 minute...")
            
            reading_interval = 60

    elif sump_reading >= 500 and sump_reading <= 600:
        #Level is okay.
        #We might be pumping right now, or the level is increasing, but do nothing.
        # Do NOT change the state of the butts pump.
        logger.info("Water level in the sump ("+str(sump_reading)+") between 500 mm and 600 mm.")
        print("Water level in the sump ("+str(sump_reading)+") between 500 mm and 600 mm.")

        #Make sure the main circulation pump is on.
        logger.info("Turning the main circulation pump on, if it was off...")
        print("Turning the main circulation pump on, if it was off...")

        #Close gate valve.
        logger.info("Closing wendy butts gate valve...")
        print("Closing wendy butts gate valve...")

        try:
            logiccoretools.attempt_to_control("VALVE4", "V4", "0%")

        except RuntimeError:
            print("Error: Error trying to control valve V4!")
            logger.error("Error: Error trying to control valve V4!")

        main_pump.enable()

        #Pump some water to the butts if they aren't full.
        #If they are full, do nothing and let the sump overflow.
        if butts_float_reading == "False":
            #Pump to the butts.
            logger.warning("Pumping water to the butts...")
            print("Pumping water to the butts...")
            butts_pump.enable()

            logger.warning("Changing reading interval to 30 seconds so we can "
                           +"keep a close eye on what's happening...")

            print("Changing reading interval to 30 seconds so we can keep a "
                  +"close eye on what's happening...")

            reading_interval = 30

        else:
            #Butts are full. Do nothing, but warn user.
            butts_pump.disable()

            logger.warning("The water butts are full. Allowing the sump to overflow.")
            print("The water butts are full.")
            print("Allowing the sump to overflow.")

            logger.warning("Setting reading interval to 1 minute...")
            print("Setting reading interval to 1 minute...")
            
            reading_interval = 60

    elif sump_reading >= 400 and sump_reading <= 500:
        #Level is okay.
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        logger.info("Water level in the sump ("+str(sump_reading)+") between 400 mm and 500 mm."
                    "Turned the butts pump off, if it was on.")
        print("Water level in the sump ("+str(sump_reading)+") between 400 mm and 500 mm."
              "Turned the butts pump off, if it was on.")

        #Make sure the main circulation pump is on.
        logger.info("Turning the main circulation pump on, if it was off...")
        print("Turning the main circulation pump on, if it was off...")

        #Close gate valve.
        logger.info("Closing wendy butts gate valve...")
        print("Closing wendy butts gate valve...")

        try:
            logiccoretools.attempt_to_control("VALVE4", "V4", "0%")

        except RuntimeError:
            print("Error: Error trying to control valve V4!")
            logger.error("Error: Error trying to control valve V4!")

        main_pump.enable()

        #Pump some water to the butts if they aren't full.
        #If they are full, do nothing and let the sump overflow.
        if butts_float_reading == "False":
            #Pump to the butts.
            logger.warning("Pumping water to the butts...")
            print("Pumping water to the butts...")
            butts_pump.enable()

            logger.warning("Changing reading interval to 30 seconds so we can "
                           +"keep a close eye on what's happening...")

            print("Changing reading interval to 30 seconds so we can keep a "
                  +"close eye on what's happening...")

            reading_interval = 30

        else:
            #Butts are full. Do nothing, but warn user.
            butts_pump.disable()

            logger.warning("The water butts are full. Allowing the sump to overflow.")
            print("The water butts are full.")
            print("Allowing the sump to overflow.")

            logger.warning("Setting reading interval to 1 minute...")
            print("Setting reading interval to 1 minute...")
            
            reading_interval = 60

    elif sump_reading >= 300 and sump_reading <= 400:
        #Level in the sump is good.
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        logger.info("Water level in the sump ("+str(sump_reading)+") between 300 mm and 400 mm."
                    + "Turned the butts pump off, if it was on.")

        print("Water level in the sump ("+str(sump_reading)+") between 300 mm and 400 mm. "
              + "Turned the butts pump off, if it was on.")

        #Make sure the main circulation pump is on.
        logger.info("Turning the main circulation pump on, if it was off...")
        print("Turning the main circulation pump on, if it was off...")

        #Close gate valve.
        logger.info("Opening wendy butts gate valve to 25%.")
        print("Opening wendy butts gate valve to 25%.")

        try:
            logiccoretools.attempt_to_control("VALVE4", "V4", "25%")

        except RuntimeError:
            print("Error: Error trying to control valve V4!")
            logger.error("Error: Error trying to control valve V4!")

        main_pump.enable()

        logger.info("Setting reading interval to 1 minute...")
        print("Setting reading interval to 1 minute...")
        
        reading_interval = 60

    elif sump_reading >= 200 and sump_reading <= 300:
        #Level in the sump is very low!
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        logger.info("Water level in the sump ("+str(sump_reading)+") between 200 mm and 300 mm."
                    + "Turned the butts pump off, if it was on.")

        print("Water level in the sump ("+str(sump_reading)+") between 200 mm and 300 mm. "
              + "Turned the butts pump off, if it was on.")

        if butts_reading >= 300:
            logger.info("Opening wendy butts gate valve to 50%...")
            print("Opening wendy butts gate valve to 50%...")

            try:
                logiccoretools.attempt_to_control("VALVE4", "V4", "50%")

            except RuntimeError:
                print("Error: Error trying to control valve V4!")
                logger.error("Error: Error trying to control valve V4!")

        else:
            logger.error("Insufficient water in wendy butts...")
            print("Insufficient water in wendy butts...")

            try:
                logiccoretools.attempt_to_control("VALVE4", "V4", "0%")

            except RuntimeError:
                print("Error: Error trying to control valve V4!")
                logger.error("Error: Error trying to control valve V4!")

            logger.error("*** NOTICE ***: Water level in the sump is between 200 and 300 mm!")
            logger.error("*** NOTICE ***: HUMAN INTERVENTION REQUIRED: "
                         + "Please add water to the system.")

            print("\n\n*** NOTICE ***: Water level in the sump is between 200 and 300 mm!")
            print("*** NOTICE ***: HUMAN INTERVENTION REQUIRED: Please add water to the system.")

        #Make sure the main circulation pump is off.
        logger.warning("Disabling the main circulation pump, if it was on...")
        print("Disabling the main circulation pump, if it was on...")

        main_pump.disable()

        logger.warning("Setting reading interval to 30 seconds for close monitoring...")
        print("Setting reading interval to 30 seconds for close monitoring...")

        reading_interval = 30

    else:
        #Level in the sump is critically low!
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        if butts_reading >= 300:
            logger.info("Opening wendy butts gate valve to 100%...")
            print("Opening wendy butts gate valve to 100%...")

            try:
                logiccoretools.attempt_to_control("VALVE4", "V4", "100%")

            except RuntimeError:
                print("Error: Error trying to control valve V4!")
                logger.error("Error: Error trying to control valve V4!")

        else:
            logger.warning("Insufficient water in wendy butts...")
            print("Insufficient water in wendy butts...")

            try:
                logiccoretools.attempt_to_control("VALVE4", "V4", "0%")

            except RuntimeError:
                print("Error: Error trying to control valve V4!")
                logger.error("Error: Error trying to control valve V4!")

            logger.critical("*** CRITICAL ***: Water level in the sump less than 200 mm!")
            logger.critical("*** CRITICAL ***: HUMAN INTERVENTION REQUIRED: Please add water to system.")
            logger.critical("*** INFO ***: The pump won't run dry; it has been temporarily disabled.")

            print("\n\n*** CRITICAL ***: Water level in the sump less than 200 mm!")
            print("*** CRITICAL ***: HUMAN INTERVENTION REQUIRED: Please add water to the system.")
            print("*** INFO ***: The pump won't run dry; it has been temporarily disabled.")

        #Make sure the main circulation pump is off.
        logger.warning("Disabling the main circulation pump, if it was on...")
        print("Disabling the main circulation pump, if it was on...")

        main_pump.disable()

        logger.critical("Setting reading interval to 15 seconds for super close monitoring...")
        print("Setting reading interval to 15 seconds for super close monitoring...")

        reading_interval = 15

    #Set the reading interval in the monitors, and send it down the sockets to the peers.
    for monitor in monitors:
        monitor.set_reading_interval(reading_interval)

    try:
        logiccoretools.update_status("Up, CPU: "+config.CPU+"%, MEM: "+config.MEM+" MB",
                                     "OK", "None")

    except RuntimeError:
        print("Error: Couldn't update site status!")
        logger.error("Error: Couldn't update site status!")

    return reading_interval

#----- Sump Pi Water Backup Control Logic -----
def sumppi_water_backup_control_logic(readings, devices, monitors, reading_interval):
    """
    This function is used to move water from the sump to the butts
    overnight to minimise loss through leakage and evaproration.  It
    is called at 1600 UTC from the sumppi_control_logic() function
    and is called repeatedly from the main loop to allow readings and
    other housekeeping actions to be performed.
    
    On entry, the wendy butts gate valve is also turned off to
    prevent water running back into the sump. At this point the
    main circulation pump remains in the state it was in before the
    function was called.  
    
    Readings are monitored and water is moved from the sump to the
    butts by turning on the butts pump when the sump level > 300 mm,
    and turning it off when it goes below that level.
    
    When the sump level < 300 mm, the main circulation pump is turned
    on.  This allows the majority of the water in the bog garden and
    the river beds to run into the sump, filling it again.
    
    The above process is repeated until the butts are full or there is
    no more water in the sump.
    
    At 0700 UTC the function is no longer called and normal operation,
    under the control of sumppi_control_logic(), is resumed.

    Args:
        readings (list):             A list of the latest readings for
                                     each probe/device.

        devices  (list):             A list of all master pi device
                                     objects.

        monitors (list):                A list of all master pi monitor objects.

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>>               water_backup_control_logic(<listofreadings>,
        >>>                                         <listofprobes>,
                                                    <areadinginterval>)

    """

    #Remove the 'mm' from the end of the reading value and convert to int.
    sump_reading = int(readings["SUMP:M0"].get_value().replace("m", ""))

    try:
        butts_reading = int(logiccoretools.get_latest_reading("G4", "M0").get_value().replace("m", ""))

    except (RuntimeError, AttributeError):
        print("Error: Error trying to get latest G4:M0 reading!")
        logger.error("Error: Error trying to get latest G4:M0 reading!")

        #Default to empty instead.
        butts_reading = 0

    try:
        butts_float_reading = logiccoretools.get_latest_reading("G4", "FS0").get_value()

    except (RuntimeError, AttributeError):
        print("Error: Error trying to get latest G4:FS0 reading!")
        logger.error("Error: Error trying to get latest G4:FS0 reading!")

        #Default to empty instead.
        butts_float_reading = "False"

    #Get a reference to both pumps.
    main_pump = None
    butts_pump = None

    for device in devices:
        if device.get_id() == "SUMP:P0":
            butts_pump = device

        elif device.get_id() == "SUMP:P1":
            main_pump = device

    #Check that we got references to both pumps.
    assert main_pump is not None
    assert butts_pump is not None

    #Check that the devices list is not empty.
    assert devices

    #Check that the butts float switch reading is sane.
    assert butts_float_reading in ("True", "False")

    #Close the wendy butts gate valve.
    logger.info("Closing the wendy butts gate valve...")
    print("Closing the wendy butts gate valve...")

    try:
        logiccoretools.attempt_to_control("VALVE4", "V4", "0%")

    except RuntimeError:
        print("Error: Error trying to control valve V4!")
        logger.error("Error: Error trying to control valve V4!")

    if sump_reading >= 600:
        #Level in the sump is high.
        logger.info("Night Mode: Water level in the sump ("+str(sump_reading)+") >= 600 mm!")
        print("Night Mode: Water level in the sump ("+str(sump_reading)+") >= 600 mm!")

        #Make sure the main circulation pump is on.
        logger.info("Night Mode: Turning the main circulation pump on, if it was off...")
        print("Night Mode: Turning the main circulation pump on, if it was off...")

        main_pump.enable()

        #Pump some water to the butts if they aren't full.
        #If they are full, do nothing and let the sump overflow.
        if butts_float_reading == "False":
            #Pump to the butts.
            logger.info("Night Mode: Pumping water to the butts...")
            print("Night Mode: Pumping water to the butts...")

            butts_pump.enable()

            logger.info("Night Mode: Changing reading interval to 30 seconds so we can "
                           +"keep a close eye on what's happening...")

            print("Night Mode: Changing reading interval to 30 seconds so we can keep a "
                  +"close eye on what's happening...")

            reading_interval = 30

        else:
            #Butts are full. Do nothing, but warn user.
            butts_pump.disable()

            logger.info("Night Mode: The water butts are full. Allowing the sump to overflow.")
            print("Night Mode: The water butts are full.")
            print("Night Mode: Allowing the sump to overflow.")

            logger.info("Night Mode: Setting reading interval to 1 minute...")
            print("Night Mode: Setting reading interval to 1 minute...")

            reading_interval = 60

    elif sump_reading >= 300 and sump_reading <= 600:
        #Level is okay.
        logger.info("Night Mode: Water level in the sump ("+str(sump_reading)+") between 300 mm and 600 mm!")
        print("Night Mode: Water level in the sump ("+str(sump_reading)+") between 300 mm and 600 mm!")

        #Make sure the main circulation pump is on.
        logger.info("Night Mode: Turning the main circulation pump on, if it was off...")
        print("Night Mode: Turning the main circulation pump on, if it was off...")

        main_pump.enable()

        #Pump some water to the butts if they aren't full.
        #If they are full, do nothing and let the sump overflow.
        if butts_float_reading == "False":
            #Pump to the butts.
            logger.info("Night Mode: Pumping water to the butts...")
            print("Night Mode: Pumping water to the butts...")

            butts_pump.enable()

        else:
            #Butts are full. Do nothing, but warn user.
            butts_pump.disable()

            logger.info("Night Mode: The water butts are full. Allowing the sump to overflow.")
            print("Night Mode: The water butts are full.")
            print("Night Mode: Allowing the sump to overflow.")

            logger.info("Night Mode: Setting reading interval to 1 minute...")
            print("Night Mode: Setting reading interval to 1 minute...")

        reading_interval = 60

    else:
        #Level in the sump is very low!
        #If the butts pump is on, turn it off.
        logger.info("Night Mode: Disabling the butts pump, if it was on...")
        print("Night Mode: Disabling the butts pump, if it was on...")

        butts_pump.disable()

        #Make sure the main circulation pump is off.
        logger.info("Night Mode: Disabling the main circulation pump, if it was on...")
        print("Night Mode: Disabling the main circulation pump, if it was on...")

        main_pump.disable()

        logger.info("Night Mode: Setting reading interval to 30 seconds for close monitoring...")
        print("Night Mode: Setting reading interval to 30 seconds for close monitoring...")

        reading_interval = 30

    #Set the reading interval in the monitors, and send it down the sockets to the peers.
    for monitor in monitors:
        monitor.set_reading_interval(reading_interval)

    try:
        logiccoretools.update_status("Up, CPU: "+config.CPU+"%, MEM: "+config.MEM+" MB",
                                     "OK", "None")

    except RuntimeError:
        print("Error: Couldn't update site status!")
        logger.error("Error: Couldn't update site status!")

    return reading_interval

#----- Stage Pi Control Logic Inegration Function -----
def stagepi_control_logic(readings, devices, monitors, sockets, reading_interval):
    """
    Control logic for stagepi's zone of responsibility.

    This mainly just wraps StagePiControlLogic.doLogic(), but it also contains
    some other integration glue.

    Run stagepi_control_logic_setup once before first running this function.

    See StagePiControlLogic for documentation.

    Args:
        readings (list):                A list of the latest readings for each probe/device.

        devices  (list):                A list of all master pi device objects.

        monitors (list):                A list of all master pi monitor objects.

        sockets (list of Socket):       A list of Socket objects that represent
                                        the data connections between pis. Passed
                                        here so we can control the reading
                                        interval at that end.

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = stagepi_control_logic(<listofreadings>,
        >>>                                     <listofprobes>, <listofmonitors>,
        >>>                                     <listofsockets>, <areadinginterval)

    """
    #Check that the reading interval is positive, and greater than 0.
    assert reading_interval > 0

    try:
        #TODO: write a test that checks that none of the control state
        #      names is long enough to cause this string to exceed the
        #      maximum accepted by the database
        software_status = "OK, in " + stagepilogic.csm.getCurrentStateName()

    except AttributeError:
        software_status = "OUT COLD. No CSM."
    
    msg = ("Stage Pi Control Logic status: " + software_status)
    print(msg)
    logger.info(msg)
    
    try:
        logiccoretools.update_status("Up, CPU: " + config.CPU
                                     +"%, MEM: " + config.MEM + " MB",
                                     software_status,
                                     "None")
        #TODO: implement current_action status other than "None" by extending
        #      ControlStateABC with a currentAction member to be overriden by
        #      each state class.

    except RuntimeError:
        print("Error: Couldn't update site status!")
        logger.error("Error: Couldn't update site status!")

    try:
        return stagepilogic.csm.doLogic(reading_interval)

    except AttributeError:
        if not isinstance(stagepilogic.csm, stagepilogic.StagePiControlLogic):
            msg  = ("CRITICAL ERROR: Stage Pi logic has not been initialised. "
                "Check whether the setup function has been run.")
            print(msg)
            logger.critical(msg)
            
        else:
            raise

        return reading_interval

#----- Stage Pi Control Logic Setup Function -----
def stagepi_control_logic_setup():
    """
    Set-up function for stagepi's control logic.

    Initialises a StagePiControlLogic object for state persistence.
    """
    #Initialise the control state machine
    stagepilogic.csm = stagepilogic.StagePiControlLogic()


def temptopup_control_logic(readings, devices, monitors, sockets, reading_interval):
    """
    Control logic function for the temporary top-up control logic, which
    tops up the G1 butts group with mains water at about 15:00 daily if
    the level is too low.
    
    This mainly just wraps TempTopUpLogic.doLogic(), but it also contains
    some other integration glue.

    Run temptopup_control_logic_setup once before first running this function.

    See TempTopUpLogic for documentation.

    Args:
        readings (list):                A list of the latest readings for each probe/device.

        devices  (list):                A list of all master pi device objects.

        monitors (list):                A list of all master pi monitor objects.

        sockets (list of Socket):       A list of Socket objects that represent
                                        the data connections between pis. Passed
                                        here so we can control the reading
                                        interval at that end.

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = stagepi_control_logic(<listofreadings>,
        >>>                                     <listofprobes>, <listofmonitors>,
        >>>                                     <listofsockets>, <areadinginterval)
    """
    #Check that the reading interval is positive, and greater than 0.
    assert reading_interval > 0
    
    # Pass on readings dictionary to the logic
    temptopuplogic.readings = readings
    
    # Try to get a reference to the solenoid valve if we don't have one yet
    # (Can't do this in the setup function because it doesn't have access to
    # the devices dictionary.)
    if temptopuplogic.solenoid is None:
        for device in devices:
            if device.get_id() == "G3:S0":
                temptopuplogic.solenoid = device
        
        if temptopuplogic.solenoid is None:
            msg = "CRITICAL ERROR: Could not find solenoid valve device."
            print(msg)
            logger.critical(msg)
            software_status = "Error: No solenoid. In "
        
        else:
            software_status = "OK, in "
    
    else:
        software_status = "OK, in "
    
    # We have to create the CSM here, after the solenoid object has
    # been assigned, rather than in a control logic setup function,
    # otherwise there will be a spurious error message about not being
    # able to control G3:S0.
    if temptopuplogic.csm is None:
        temptopuplogic.csm = temptopuplogic.TempTopUpControlLogic()
    
    try:
        software_status = (software_status +
                           temptopuplogic.csm.getCurrentStateName())

    except AttributeError:
        software_status = "OUT COLD. No CSM."
    
    msg = ("Temporary Top Up Control Logic status: " + software_status)
    print(msg)
    logger.info(msg)
    
    try:
        logiccoretools.update_status("Up, CPU: " + config.CPU
                                     +"%, MEM: " + config.MEM + " MB",
                                     software_status,
                                     "None")

    except RuntimeError:
        print("Error: Couldn't update site status!")
        logger.error("Error: Couldn't update site status!")
    
    if temptopuplogic.solenoid is not None:
        try:
            return temptopuplogic.csm.doLogic(reading_interval)

        except AttributeError:
            if not isinstance(temptopuplogic.csm,
                            temptopuplogic.TempTopUpControlLogic):
                msg  = ("CRITICAL ERROR: Temporary Top Up Pi logic has not "
                        "been initialised. Check whether the setup function "
                        "has been run.")
                print(msg)
                logger.critical(msg)
                
            else:
                raise

    return reading_interval
