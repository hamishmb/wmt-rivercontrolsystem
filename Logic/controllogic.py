#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#Control Logic integration and setup functions for the River System Control Software
#Copyright (C) 2020-2022 Wimborne Model Town
#This program is free software: you can redistribute it and/or modify it
#under the terms of the GNU General Public License version 3 or,
#at your option, any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

#pylint: disable=logging-not-lazy
#pylint: disable=wrong-import-position
#
#Reason (logging-not-lazy): Harder to understand the logging statements that way.
#Reason (wrong-import-position): Pylint is confused by the need to modify sys.path.

"""
This is the controllogic module, which contains control logic integration and setup functions.

.. module:: controllogic.py
    :platform: Linux
    :synopsis: Contains control logic integration and setup functions.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>
.. moduleauthor:: Patrick Wigmore <pwbugreports@gmx.com>
.. moduleauthor:: Terry Coles <wmt@hadrian-way.co.uk>
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

    for _handler in logging.getLogger('River System Control Software').handlers:
        logger.addHandler(_handler)

#----- NAS Control Logic -----
def nas_control_logic(readings, devices, monitors, sockets, reading_interval):
    """
    This control logic runs on the NAS box, and is responsible for:

    - Setting and restoring the system tick.
    - Freeing locks that have expired (locks can only be held for a maximum of TBD minutes).
        - Not yet implemented.

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
            logiccoretools.update_status("Up, HIGH temps: ("+sys_temp+"/"+hdd0_temp
                                         + "/"+hdd1_temp+"), CPU: "+config.CPU
                                         +"%, MEM: "+config.MEM+" MB", "OK", "None")

            logiccoretools.log_event("NAS Box getting hot! Temps: sys: "+sys_temp
                                     +", hdd0: "+hdd0_temp+", hdd1: "+hdd1_temp,
                                     severity="WARNING")

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
                        logiccoretools.log_event(config.SYSTEM_ID+": New valve position: "
                                                 + str(position))

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

    There is a remote manual override feature. If a device state
    has been requested for SUMP:P0 or SUMP:P1 using logiccoretools,
    it will be taken to be a request for a manual override.

    In an override, only the requested pump will be taken out of
    automatic control. The remaining automatic operations will
    continue to occur.

    Request a device state of:

    - 'None' to remove the override (normal operation)
    - 'ON' to manually keep the pump turned on indefinitely
    - 'OFF' to manually keep the pump turned off indefinitely

    If any other device state value is requested an error will be
    logged and the pumps will operate as though no override was
    requested. The outcome is the same if an error occurs when
    trying to determine whether an override has been requested.

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

    #Call sump water backup function if not Opening Hours
    timenow = datetime.now()

    hour = int(timenow.hour)

    if (hour >= config.WATERBACKUPSTART or hour <= config.WATERBACKUPEND):
        #TODO Temporarily disabled, test and enable.
        pass #return sumppi_water_backup_control_logic(readings, devices, monitors,
                                                      #reading_interval)

    #Remove the 'mm' from the end of the reading value and convert to int.
    sump_reading = int(readings["SUMP:M0"].get_value().replace("m", ""))

    try:
        butts_reading = int(logiccoretools.get_latest_reading("G4", "M0") \
                            .get_value().replace("m", ""))

        print(butts_reading)

    except (RuntimeError, AttributeError):
        print("Error: Error trying to get latest G4:M0 reading!")
        logger.error("Error: Error trying to get latest G4:M0 reading!")

        #Default to empty instead.
        butts_reading = 0

    try:
        butts_float_reading = logiccoretools.get_latest_reading("G4", "FS0").get_value()

        print(butts_float_reading)

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

    #Apply manual overrides if requested
    try:
        main_pump_ovr = None
        butts_pump_ovr = None
        #TODO Re-enable after testing.
        #Incompatible with current database format with "Locked" and "Unlocked".
        #main_pump_ovr = logiccoretools.get_state("SUMP", "P1")
        #if main_pump_ovr is not None:
            #get device state from second (1th) element of tuple
            #if main_pump_ovr[1] == "None":
                #main_pump_ovr = None
            #else:
                #main_pump_ovr = main_pump_ovr[1]

        #butts_pump_ovr = logiccoretools.get_state("SUMP", "P0")
        #if butts_pump_ovr is not None:
            #get device state from second (1th) element of tuple
            #if butts_pump_ovr[1] == "None":
                #butts_pump_ovr = None
            #else:
                #butts_pump_ovr = butts_pump_ovr[1]

    except RuntimeError:
        main_pump_ovr = None
        butts_pump_ovr = None
        print("Error: Couldn't check whether or not a manual override has "
              "been requested. No override will be applied.")
        logger.error("Error: Couldn't check whether or not a manual override has "
                     "been requested. No override will be applied.")

    if main_pump_ovr is not None:
        if main_pump_ovr in ("ON", "OFF"):
            logger.warning("*** MAIN CIRCULATION PUMP IS IN MANUAL OVERRIDE ***")
            print("*** MAIN CIRCULATION PUMP IS IN MANUAL OVERRIDE ***")
            if main_pump_ovr == "ON":
                msg = "Holding main circulation pump on."
                logger.info(msg)
                print(msg)
                main_pump.enable()

            else: #must be "OFF"
                msg = "Holding main circulation pump off."
                logger.info(msg)
                print(msg)
                main_pump.disable()

        else:
            msg = ("Received a request to put the main circulation pump "
                + "into manual override, but the requested state (\""
                + main_pump_ovr
                + "\") is not understood. Not overriding.")
            logger.warning(msg)
            print(msg)
            main_pump_ovr = None

    if butts_pump_ovr is not None:
        if butts_pump_ovr in ("ON", "OFF"):
            logger.warning("*** BUTTS PUMP IS IN MANUAL OVERRIDE ***")
            print("*** BUTTS PUMP IS IN MANUAL OVERRIDE ***")
            if butts_pump_ovr == "ON":
                msg = "Holding butts pump on."
                logger.info(msg)
                print(msg)
                butts_pump.enable()

            else: #must be "OFF"
                msg = "Holding butts pump off."
                logger.info(msg)
                print(msg)
                butts_pump.disable()

        else:
            msg = ("Received a request to put the butts pump into manual "
                + "override, but the requested state (\""
                + butts_pump_ovr
                + "\") is not understood. Not overriding.")
            logger.warning(msg)
            print(msg)
            butts_pump_ovr = None

    if sump_reading >= 600:
        #Level in the sump is getting high.
        logger.warning("Water level in the sump ("+str(sump_reading)+") >= 600 mm!")
        print("Water level in the sump ("+str(sump_reading)+") >= 600 mm!")

        #Make sure the main circulation pump is on.
        if main_pump_ovr is None:
            logger.info("Turning the main circulation pump on, if it was off...")
            print("Turning the main circulation pump on, if it was off...")
        elif main_pump_ovr == "OFF":
            logger.info("Not turning the main circulation pump on, due to manual override...")
            print("Not turning the main circulation pump on, due to manual override...")

        #Close the wendy butts gate valve.
        logger.info("Closing the wendy butts gate valve...")
        print("Closing the wendy butts gate valve...")

        try:
            logiccoretools.attempt_to_control("VALVE4", "V4", "0%")

        except RuntimeError:
            print("Error: Error trying to control valve V4!")
            logger.error("Error: Error trying to control valve V4!")

        if main_pump_ovr is None:
            main_pump.enable()
        else:
            logger.warning("A manual override is controlling the main circulation pump.")
            print("A manual override is controlling the main circulation pump.")

        #Pump some water to the butts if they aren't full.
        #If they are full, do nothing and let the sump overflow.
        if butts_float_reading == "False":
            #Pump to the butts.
            if butts_pump_ovr is None:
                logger.warning("Pumping water to the butts...")
                print("Pumping water to the butts...")
                butts_pump.enable()
            else:
                logger.warning("A manual override is controlling the butts pump.")
                print("A manual override is controlling the butts pump.")

            logger.warning("Changing reading interval to 30 seconds so we can "
                           +"keep a close eye on what's happening...")

            print("Changing reading interval to 30 seconds so we can keep a "
                  +"close eye on what's happening...")

            reading_interval = 30

        else:
            #Butts are full. Do nothing, but warn user.
            if butts_pump_ovr is None:
                butts_pump.disable()
            else:
                logger.warning("A manual override is controlling the butts pump.")
                print("A manual override is controlling the butts pump.")

            logger.warning("The water butts are full. Allowing the sump to overflow.")
            print("The water butts are full.")
            print("Allowing the sump to overflow.")

            logger.warning("Setting reading interval to 1 minute...")
            print("Setting reading interval to 1 minute...")

            reading_interval = 60

    elif sump_reading >= 500 and sump_reading < 600:
        #Level is okay.
        #We might be pumping right now, or the level is increasing, but do nothing.
        #Do NOT change the state of the butts pump.
        logger.info("Water level in the sump ("+str(sump_reading)+") between 500 mm and 600 mm.")
        print("Water level in the sump ("+str(sump_reading)+") between 500 mm and 600 mm.")

        #Make sure the main circulation pump is on.
        if main_pump_ovr is None:
            logger.info("Turning the main circulation pump on, if it was off...")
            print("Turning the main circulation pump on, if it was off...")

        elif main_pump_ovr == "OFF":
            logger.info("Not turning the main circulation pump on, due to manual override...")
            print("Not turning the main circulation pump on, due to manual override...")

        #Close gate valve.
        logger.info("Closing wendy butts gate valve...")
        print("Closing wendy butts gate valve...")

        try:
            logiccoretools.attempt_to_control("VALVE4", "V4", "0%")

        except RuntimeError:
            print("Error: Error trying to control valve V4!")
            logger.error("Error: Error trying to control valve V4!")

        if main_pump_ovr is None:
            main_pump.enable()

        else:
            logger.warning("A manual override is controlling the main circulation pump.")
            print("A manual override is controlling the main circulation pump.")

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

    elif sump_reading >= 400 and sump_reading < 500:
        #Level is okay.
        #If the butts pump is on, turn it off.
        if butts_pump_ovr is None:
            butts_pump.disable()

        else:
            logger.warning("A manual override is controlling the butts pump.")
            print("A manual override is controlling the butts pump.")

        logger.info("Water level in the sump ("+str(sump_reading)+") between 400 mm and 500 mm."
                    "Turned the butts pump off, if it was on.")
        print("Water level in the sump ("+str(sump_reading)+") between 400 mm and 500 mm."
              "Turned the butts pump off, if it was on.")

        #Make sure the main circulation pump is on.
        if main_pump_ovr is None:
            logger.info("Turning the main circulation pump on, if it was off...")
            print("Turning the main circulation pump on, if it was off...")

        elif main_pump_ovr == "OFF":
            logger.info("Not turning the main circulation pump on, due to manual override...")
            print("Not turning the main circulation pump on, due to manual override...")

        #Close gate valve.
        logger.info("Closing wendy butts gate valve...")
        print("Closing wendy butts gate valve...")

        try:
            logiccoretools.attempt_to_control("VALVE4", "V4", "0%")

        except RuntimeError:
            print("Error: Error trying to control valve V4!")
            logger.error("Error: Error trying to control valve V4!")

        if main_pump_ovr is None:
            main_pump.enable()

        else:
            logger.warning("A manual override is controlling the main circulation pump.")
            print("A manual override is controlling the main circulation pump.")

        #Pump some water to the butts if they aren't full.
        #If they are full, do nothing and let the sump overflow.
        if butts_float_reading == "False":
            #Pump to the butts.
            logger.warning("Pumping water to the butts...")
            print("Pumping water to the butts...")

            if butts_pump_ovr is None:
                butts_pump.enable()

                logger.warning("Changing reading interval to 30 seconds so we can "
                               +"keep a close eye on what's happening...")

                print("Changing reading interval to 30 seconds so we can keep a "
                      +"close eye on what's happening...")

                reading_interval = 30

            else:
                logger.warning("A manual override is controlling the butts pump.")
                print("A manual override is controlling the butts pump.")

        else:
            #Butts are full. Do nothing, but warn user.
            butts_pump.disable()

            logger.warning("The water butts are full. Allowing the sump to overflow.")
            print("The water butts are full.")
            print("Allowing the sump to overflow.")

            logger.warning("Setting reading interval to 1 minute...")
            print("Setting reading interval to 1 minute...")

            reading_interval = 60

    elif sump_reading >= 300 and sump_reading < 400:
        #Level in the sump is getting low.
        #If the butts pump is on, turn it off.
        if butts_pump_ovr is None:
            butts_pump.disable()

            logger.info("Water level in the sump ("+str(sump_reading)+") between 300 mm and 400 mm."
                        + "Turned the butts pump off, if it was on.")

            print("Water level in the sump ("+str(sump_reading)+") between 300 mm and 400 mm. "
                  + "Turned the butts pump off, if it was on.")

        else:
            logger.warning("A manual override is controlling the butts pump.")
            print("A manual override is controlling the butts pump.")

        #Make sure the main circulation pump is on.
        logger.info("Turning the main circulation pump on, if it was off...")
        print("Turning the main circulation pump on, if it was off...")

        if main_pump_ovr is None:
            logger.info("Turning the main cirulation pump on, if it was off...")
            print("Turning the main circulation pump on, if it was off...")
            main_pump.enable()

        else:
            if main_pump_ovr == "OFF":
                logger.info("Not turning the main circulation pump on, due to manual override...")
                print("Not turning the main circulation pump on, due to manual override...")

            logger.warning("A manual override is controlling the main circulation pump.")
            print("A manual override is controlling the main circulation pump.")

        #Close gate valve.
        logger.info("Opening wendy butts gate valve to 25%.")
        print("Opening wendy butts gate valve to 25%.")

        try:
            logiccoretools.attempt_to_control("VALVE4", "V4", "25%")

        except RuntimeError:
            print("Error: Error trying to control valve V4!")
            logger.error("Error: Error trying to control valve V4!")

        logger.info("Setting reading interval to 1 minute...")
        print("Setting reading interval to 1 minute...")

        reading_interval = 60

    elif sump_reading >= 200 and sump_reading < 300:
        #Level in the sump is very low!
        #If the butts pump is on, turn it off.
        if butts_pump_ovr is None:
            butts_pump.disable()
        else:
            logger.warning("A manual override is controlling the butts pump.")
            print("A manual override is controlling the butts pump.")

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
        if main_pump_ovr is None:
            logger.warning("Disabling the main circulation pump, if it was on...")
            print("Disabling the main circulation pump, if it was on...")
            main_pump.disable()

        else:
            if main_pump_ovr == "ON":
                logger.info("Not turning the main circulation pump off, due to manual override...")
                print("Not turning the main circulation pump off, due to manual override...")

            logger.warning("A manual override is controlling the main circulation pump.")
            print("A manual override is controlling the main circulation pump.")

        logger.warning("Setting reading interval to 30 seconds for close monitoring...")
        print("Setting reading interval to 30 seconds for close monitoring...")

        reading_interval = 30

    else:
        #Level in the sump is critically low!
        #If the butts pump is on, turn it off.
        if butts_pump_ovr is None:
            butts_pump.disable()
        else:
            logger.warning("A manual override is controlling the butts pump.")
            print("A manual override is controlling the butts pump.")

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
            logger.critical("*** CRITICAL ***: HUMAN INTERVENTION REQUIRED: Please add "
                            + "water to system.")

            print("\n\n*** CRITICAL ***: Water level in the sump less than 200 mm!")
            print("*** CRITICAL ***: HUMAN INTERVENTION REQUIRED: Please add water to the "
                  + "system.")

            if main_pump_ovr != "ON":
                logger.critical("*** INFO ***: The pump won't run dry; it has been temporarily "
                                + "disabled.")
                print("*** INFO ***: The pump won't run dry; it has been temporarily disabled.")

            else:
                logger.critical("*** CRITICAL ***: RUNNING THE PUMP **DRY** DUE TO MANUAL "
                                + "OVERRIDE. Damage might occur.")

                print("*** CRITICAL ***: RUNNING THE PUMP **DRY** DUE TO MANUAL OVERRIDE. "
                      + "Damage might occur.")

        #Make sure the main circulation pump is off.
        if main_pump_ovr is None:
            logger.warning("Disabling the main circulation pump, if it was on...")
            print("Disabling the main circulation pump, if it was on...")
            main_pump.disable()

        else:
            if main_pump_ovr == "ON":
                logger.info("Not turning the main circulation pump off, due to manual "
                            + "override...")
                print("Not turning the main circulation pump off, due to manual override...")

            logger.warning("A manual override is controlling the main circulation pump.")
            print("A manual override is controlling the main circulation pump.")

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

        >>> reading_interval = water_backup_control_logic(<listofreadings>,
        >>>                                               <listofprobes>,
        >>>                                               <areadinginterval>)

    """

    #Remove the 'mm' from the end of the reading value and convert to int.
    sump_reading = int(readings["SUMP:M0"].get_value().replace("m", ""))

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
        logger.info("Night Mode: Water level in the sump ("+str(sump_reading)
                    + ") between 300 mm and 600 mm!")

        print("Night Mode: Water level in the sump ("+str(sump_reading)
              + ") between 300 mm and 600 mm!")

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

#----- Wendy Butts Pi Control Logic -----
def wbuttspi_control_logic(readings, devices, monitors, sockets, reading_interval):
    """
    This control logic is does very little but monitors levels and runs the water backup
    function overnight. It does the following:

    - Updates the pi status in the database.
    - Calls wbuttspi_water_backup_control_logic() overnight.
    - In the daytime:
        - Ensures that the Bypass Gate Valve is open - it will have been closed overnight.
        - Ensures that the Backup Pump is off - it may still be running from overnight pumping.

    """

    #Get a reference to the backup pump.
    backup_pump = None

    for device in devices:
        if device.get_id() == "G4:P0":
            backup_pump = device

    #Check that we got a references to the pump.
    assert backup_pump is not None

    #Check that the devices list is not empty.
    assert devices

    #Check that the reading interval is positive, and greater than 0.
    assert reading_interval > 0

    #Call wendy butts water backup function if not Opening Hours
    timenow = datetime.now()

    hour = int(timenow.hour)

    if (hour >= config.WATERBACKUPSTART or hour <= config.WATERBACKUPEND):
        #TODO Disabled until it has been tested.
        pass #return wbuttspi_water_backup_control_logic(readings, devices, monitors,
                                                        #reading_interval)

    else:
        #Opening time. Ensure that the Bypass Gate Valve is open and the Water Backup Pump
        #is off.
        logger.info("Opening the bypass gate valve if it was closed...")
        print("Opening the bypass gate valve if it was closed...")

        try:
            logiccoretools.attempt_to_control("VALVE6", "V6", "100%")

        except RuntimeError:
            print("Error: Error trying to control valve V6!")
            logger.error("Error: Error trying to control valve V6!")

        logger.info("Turning off the backup pump if it was on...")
        print("Turning off the backup pump if it was on...")

        backup_pump.disable()

    try:
        logiccoretools.update_status("Up, CPU: "+config.CPU+"%, MEM: "+config.MEM+" MB",
                                     "OK", "None")

    except RuntimeError:
        print("Error: Couldn't update site status!")
        logger.error("Error: Couldn't update site status!")

    return 15

#----- Wendy Butts Pi Water Backup Control Logic -----
def wbuttspi_water_backup_control_logic(readings, devices, monitors, reading_interval):
    """
    This function is used to move water from the Wendy Butts to the upstream butts
    overnight to minimise loss through leakage and evaporation.  It is called at
    1600 UTC from the wbuttspi_water_backup_control_logic() function and is called
    repeatedly from the main loop to allow readings and other housekeeping actions
    to be performed.

    On entry, the Bypass Gate Valve is closed to allow the Bypass Pump to pump water
    from the Wendy Butts to the Lady Hanham and Stage Butts.  This Valve remains
    closed until it re-opened at 0700 UTC.

    The upstream Gate Valves are then opened in turn to allow the water to be pumped
    up to them.  Once any butts group is full, its associated Gate Valve is closed.

    Readings are monitored and water is moved from the Wendy butts to the upstream
    butts by turning on the Water Backup Pump when the butts level > 300 mm.

    When the Wendy butts level < 300 mm, the Backup Pump is turned off.

    The above process is repeated until the upstream butts are all full or there is
    no more water in the Wendy Butts.

    At 0700 UTC the function is no longer called and normal operation,
    under the control of wbuttspi_control_logic(), is resumed.

    Args:
        readings (list):            A list of the latest readings for
                                    each probe/device.

        devices  (list):            A list of all master pi device
                                    objects.

        monitors (list):            A list of all master pi monitor objects.

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = wbuttspi_water_backup_control_logic(<listofreadings>,
        >>>                                                        <listofprobes>,
        >>>                                                        <areadinginterval>)

    """

    #Remove the 'mm' from the end of the reading value and convert to int.
    wbutts_reading = int(readings["G4:M0"].get_value().replace("m", ""))

    #Read the Lady Hanham and Stage high Float Switches so we can stop pumping
    #when all butts are full.
    try:
        sbutts_float_reading = logiccoretools.get_latest_reading("G6", "FS0").get_value()

    except (RuntimeError, AttributeError):
        print("Error: Error trying to get latest G6:FS0 reading!")
        logger.error("Error: Error trying to get latest G6:FS0 reading!")

        #Default to full instead.
        sbutts_float_reading = "True"

    try:
        lhbutts1_float_reading = logiccoretools.get_latest_reading("G3", "FS0").get_value()

    except (RuntimeError, AttributeError):
        print("Error: Error trying to get latest G3:FS0 reading!")
        logger.error("Error: Error trying to get latest G3:FS0 reading!")

        #Default to full instead.
        lhbutts1_float_reading = "True"

    try:
        lhbutts2_float_reading = logiccoretools.get_latest_reading("G3", "FS1").get_value()

    except (RuntimeError, AttributeError):
        print("Error: Error trying to get latest G3:FS1 reading!")
        logger.error("Error: Error trying to get latest G3:FS1 reading!")

        #Default to full instead.
        lhbutts2_float_reading = "True"

    try:
        lhbutts3_float_reading = logiccoretools.get_latest_reading("G3", "FS2").get_value()

    except (RuntimeError, AttributeError):
        print("Error: Error trying to get latest G3:FS2 reading!")
        logger.error("Error: Error trying to get latest G3:FS2 reading!")

        #Default to full instead.
        lhbutts3_float_reading = "True"

    #Get a reference to the pump.
    backup_pump = None

    for device in devices:
        if device.get_id() == "G4:P0":
            backup_pump = device

    #Check that we got a reference to the pump.
    assert backup_pump is not None

    #Check that the devices list is not empty.
    assert devices

    #Check that all the butts float switch readings are sane.
    assert lhbutts1_float_reading in ("True", "False")
    assert lhbutts2_float_reading in ("True", "False")
    assert lhbutts3_float_reading in ("True", "False")
    assert sbutts_float_reading in ("True", "False")

    #Close the Backup Pump Bypass Gate Valve.
    logger.info("Closing the Backup Pump Bypass Gate Valve...")
    print("Closing the Backup Pump Bypass Gate Valve...")

    try:
        logiccoretools.attempt_to_control("VALVE6", "V6", "0%")

    except RuntimeError:
        print("Error: Error trying to control valve V6!")
        logger.error("Error: Error trying to control valve V6!")

    #Setup the reading_interval based on the upstream capacity.
    num_high_floats = [sbutts_float_reading, lhbutts1_float_reading, lhbutts2_float_reading,
                       lhbutts3_float_reading]

    if num_high_floats == 0:
        #All the butts groups have capacity - set the reading interval to a fairly slow rate
        logger.info("Night Mode: Setting reading interval to 2 minutes...")
        print("Night Mode: Setting reading interval to 2 minutes...")

        reading_interval = 120

    elif num_high_floats == 1:
        #Three of the butts groups have capacity - set the reading interval to a faster rate
        logger.info("Night Mode: Setting reading interval to 1.5 minutes...")
        print("Night Mode: Setting reading interval to 1.5 minutes...")

        reading_interval = 90

    elif num_high_floats == 2:
        #Only Two of the butts groups have capacity - set the reading interval to a faster rate
        logger.info("Night Mode: Setting reading interval to 1 minute...")
        print("Night Mode: Setting reading interval to 1 minute...")

        reading_interval = 60

    else:
        #Only One butts group has capacity - set the reading interval to the fastest rate
        logger.info("Night Mode: Setting reading interval to 30 seconds...")
        print("Night Mode: Setting reading interval to 30 seconds...")

        reading_interval = 30

    #Start moving water
    if wbutts_reading >= 900:
        #Level in the wendy butts is high.
        logger.info("Night Mode: Water level in the wendy butts ("+str(wbutts_reading)
                    + ") >= 900 mm!")

        print("Night Mode: Water level in the wendy butts ("+str(wbutts_reading)+") >= 900 mm!")

        #Pump some water to the upstream butts if they aren't full.
        #If they are full, do nothing and let the wendy butts overflow.
        if sbutts_float_reading == "False":
            #There is capacity in the Stage Butts.
            #Open the Stage Butts Gate Valve and start pumping.
            logger.info("Opening the Stage Butts Gate Valve...")
            print("Opening the Stage Butts Gate Valve...")

            try:
                logiccoretools.attempt_to_control("VALVE12", "V12", "100%")

            except RuntimeError:
                print("Error: Error trying to control valve V12!")
                logger.error("Error: Error trying to control valve V12!")

            #Pump to the stage butts.
            logger.info("Night Mode: Pumping water to the stage butts...")
            print("Night Mode: Pumping water to the stage butts...")

            backup_pump.enable()

        else:
            #Stage butts group G6 is full. Stop pumping and close V12 Gate Valve.
            logger.info("Night Mode: The G6 butts are full.  Close the Gate Valve")
            print("Night Mode: The G6 water butts are full.  Close the Gate Valve")

            try:
                logiccoretools.attempt_to_control("VALVE12", "V12", "0%")

            except RuntimeError:
                print("Error: Error trying to control valve V12!")
                logger.error("Error: Error trying to control valve V12!")

            logger.info("Night Mode: Stop pumping water to the stage butts...")
            print("Night Mode: Stop pumping water to the stage butts...")

            backup_pump.disable()

        if lhbutts1_float_reading == "False":
            #There is capacity in butts group G1 of the Lady Hanham butts.
            #Open the Lady Hanham Butts G1 Gate Valve and pump water.
            logger.info("Opening the Lady Hanham Butts G1 Gate Valve...")
            print("Opening the Lady Hanham Butts G1 Gate Valve...")

            try:
                logiccoretools.attempt_to_control("VALVE1", "V1", "100%")

            except RuntimeError:
                print("Error: Error trying to control valve V1!")
                logger.error("Error: Error trying to control valve V1!")

            logger.info("Night Mode: Pumping water to butts group G1 of the lady "
                        + "hanham butts...")

            print("Night Mode: Pumping water to butts group G1 of the lady hanham butts...")

            backup_pump.enable()

        else:
            #Lady Hanham butts group G1 is full. Stop pumping and close V1 Gate Valve.
            logger.info("Night Mode: The G1 butts are full.  Close the Gate Valve")
            print("Night Mode: The G1 water butts are full.  Close the Gate Valve")

            try:
                logiccoretools.attempt_to_control("VALVE1", "V1", "0%")

            except RuntimeError:
                print("Error: Error trying to control valve V1!")
                logger.error("Error: Error trying to control valve V1!")

            logger.info("Night Mode: Stop pumping water to G1 butts...")
            print("Night Mode: Stop pumping water to G1 butts...")

            backup_pump.disable()

        if lhbutts2_float_reading == "False":
            #There is capacity in butts group G2 of the Lady Hanham butts.
            #Open the Lady Hanham Butts G2 Gate Valve and pump water.
            logger.info("Opening the Lady Hanham Butts G2 Gate Valve...")
            print("Opening the Lady Hanham Butts G2 Gate Valve...")

            try:
                logiccoretools.attempt_to_control("VALVE2", "V2", "100%")

            except RuntimeError:
                print("Error: Error trying to control valve V2!")
                logger.error("Error: Error trying to control valve V2!")

            logger.info("Night Mode: Pumping water to butts group G2 of the lady "
                        + "hanham butts...")

            print("Night Mode: Pumping water to butts group G2 of the lady hanham butts...")

            backup_pump.enable()

        else:
            #Lady Hanham butts group G2 is full. Stop pumping and close V2 Gate Valve.
            logger.info("Night Mode: The G2 butts are full.  Close the Gate Valve")
            print("Night Mode: The G2 water butts are full.  Close the Gate Valve")

            try:
                logiccoretools.attempt_to_control("VALVE2", "V2", "0%")

            except RuntimeError:
                print("Error: Error trying to control valve V2!")
                logger.error("Error: Error trying to control valve V2!")

            logger.info("Night Mode: Stop pumping water to G2 butts...")
            print("Night Mode: Stop pumping water to G2 butts...")

            backup_pump.disable()

        if lhbutts3_float_reading == "False":
            #There is capacity in butts group G3 of the Lady Hanham butts.
            #Open the Lady Hanham Butts G3 Gate Valve and pump water.
            logger.info("Opening the Lady Hanham Butts G3 Gate Valve...")
            print("Opening the Lady Hanham Butts G3 Gate Valve...")

            try:
                logiccoretools.attempt_to_control("VALVE3", "V3", "100%")

            except RuntimeError:
                print("Error: Error trying to control valve V3!")
                logger.error("Error: Error trying to control valve V3!")

            logger.info("Night Mode: Pumping water to butts group G3 of the lady "
                        + "hanham butts...")
            print("Night Mode: Pumping water to butts group G3 of the lady hanham butts...")

            backup_pump.enable()

        else:
            #Lady Hanham butts group G3 is full. Stop pumping and close V1 Gate Valve.
            logger.info("Night Mode: The G3 butts are full.  Close the Gate Valve")
            print("Night Mode: The G3 water butts are full.  Close the Gate Valve")

            try:
                logiccoretools.attempt_to_control("VALVE3", "V3", "0%")

            except RuntimeError:
                print("Error: Error trying to control valve V3!")
                logger.error("Error: Error trying to control valve V3!")

            logger.info("Night Mode: Stop pumping water to G3 butts...")
            print("Night Mode: Stop pumping water to G3 butts...")

            backup_pump.disable()

    elif wbutts_reading >= 300 and wbutts_reading <= 900:
        #Level in the Wendy butts is okay.
        logger.info("Night Mode: Water level in the wendy butts ("+str(wbutts_reading)
                    + ") >= 900 mm!")

        print("Night Mode: Water level in the wendy butts ("+str(wbutts_reading)+") >= 900 mm!")

        #Pump some water to the upstream butts if they aren't full.
        #If they are full, do nothing and let the wendy butts overflow.
        if sbutts_float_reading == "False":
            #There is capacity in the Stage Butts.
            #Open the Stage Butts Gate Valve and start pumping.
            logger.info("Opening the Stage Butts Gate Valve...")
            print("Opening the Stage Butts Gate Valve...")

            try:
                logiccoretools.attempt_to_control("VALVE12", "V12", "100%")

            except RuntimeError:
                print("Error: Error trying to control valve V12!")
                logger.error("Error: Error trying to control valve V12!")

            #Pump to the stage butts.
            logger.info("Night Mode: Pumping water to the stage butts...")
            print("Night Mode: Pumping water to the stage butts...")

            backup_pump.enable()

        else:
            #Stage butts group G6 is full. Stop pumping and close V12 Gate Valve.
            logger.info("Night Mode: The G6 butts are full.  Close the Gate Valve")
            print("Night Mode: The G6 water butts are full.  Close the Gate Valve")

            try:
                logiccoretools.attempt_to_control("VALVE12", "V12", "0%")

            except RuntimeError:
                print("Error: Error trying to control valve V12!")
                logger.error("Error: Error trying to control valve V12!")

            logger.info("Night Mode: Stop pumping water to the stage butts...")
            print("Night Mode: Stop pumping water to the stage butts...")

            backup_pump.disable()

        if lhbutts1_float_reading == "False":
            #There is capacity in butts group G1 of the Lady Hanham butts.
            #Open the Lady Hanham Butts G1 Gate Valve and pump water.
            logger.info("Opening the Lady Hanham Butts G1 Gate Valve...")
            print("Opening the Lady Hanham Butts G1 Gate Valve...")

            try:
                logiccoretools.attempt_to_control("VALVE1", "V1", "100%")

            except RuntimeError:
                print("Error: Error trying to control valve V1!")
                logger.error("Error: Error trying to control valve V1!")

            logger.info("Night Mode: Pumping water to butts group G1 of the lady "
                        + "hanham butts...")

            print("Night Mode: Pumping water to butts group G1 of the lady hanham butts...")

            backup_pump.enable()

        else:
            #Lady Hanham butts group G1 is full. Stop pumping and close V1 Gate Valve.
            logger.info("Night Mode: The G1 butts are full.  Close the Gate Valve")
            print("Night Mode: The G1 water butts are full.  Close the Gate Valve")

            try:
                logiccoretools.attempt_to_control("VALVE1", "V1", "0%")

            except RuntimeError:
                print("Error: Error trying to control valve V1!")
                logger.error("Error: Error trying to control valve V1!")

            logger.info("Night Mode: Stop pumping water to G1 butts...")
            print("Night Mode: Stop pumping water to G1 butts...")

            backup_pump.disable()

        if lhbutts2_float_reading == "False":
            #There is capacity in butts group G2 of the Lady Hanham butts.
            #Open the Lady Hanham Butts G2 Gate Valve and pump water.
            logger.info("Opening the Lady Hanham Butts G2 Gate Valve...")
            print("Opening the Lady Hanham Butts G2 Gate Valve...")

            try:
                logiccoretools.attempt_to_control("VALVE2", "V2", "100%")

            except RuntimeError:
                print("Error: Error trying to control valve V2!")
                logger.error("Error: Error trying to control valve V2!")

            logger.info("Night Mode: Pumping water to butts group G2 of the lady "
                         + "hanham butts...")

            print("Night Mode: Pumping water to butts group G2 of the lady hanham butts...")

            backup_pump.enable()

        else:
            #Lady Hanham butts group G2 is full. Stop pumping and close V2 Gate Valve.
            logger.info("Night Mode: The G2 butts are full.  Close the Gate Valve")
            print("Night Mode: The G2 water butts are full.  Close the Gate Valve")

            try:
                logiccoretools.attempt_to_control("VALVE2", "V2", "0%")

            except RuntimeError:
                print("Error: Error trying to control valve V2!")
                logger.error("Error: Error trying to control valve V2!")

            logger.info("Night Mode: Stop pumping water to G2 butts...")
            print("Night Mode: Stop pumping water to G2 butts...")

            backup_pump.disable()

        if lhbutts3_float_reading == "False":
            #There is capacity in butts group G3 of the Lady Hanham butts.
            #Open the Lady Hanham Butts G3 Gate Valve and pump water.
            logger.info("Opening the Lady Hanham Butts G3 Gate Valve...")
            print("Opening the Lady Hanham Butts G3 Gate Valve...")

            try:
                logiccoretools.attempt_to_control("VALVE3", "V3", "100%")

            except RuntimeError:
                print("Error: Error trying to control valve V3!")
                logger.error("Error: Error trying to control valve V3!")

            logger.info("Night Mode: Pumping water to butts group G3 of the lady "
                        + "hanham butts...")

            print("Night Mode: Pumping water to butts group G3 of the lady hanham butts...")

            backup_pump.enable()

        else:
            #Lady Hanham butts group G3 is full. Stop pumping and close V1 Gate Valve.
            logger.info("Night Mode: The G3 butts are full.  Close the Gate Valve")
            print("Night Mode: The G3 water butts are full.  Close the Gate Valve")

            try:
                logiccoretools.attempt_to_control("VALVE3", "V3", "0%")

            except RuntimeError:
                print("Error: Error trying to control valve V3!")
                logger.error("Error: Error trying to control valve V3!")

            logger.info("Night Mode: Stop pumping water to G3 butts...")
            print("Night Mode: Stop pumping water to G3 butts...")

            backup_pump.disable()

    else:
        #Wendy butts group G4 is nearly empty. Stop pumping.
        logger.info("Night Mode: The G4 butts are nearly empty.  Stop pumping")
        print("Night Mode: The G4 butts are nearly empty.  Stop pumping")

        logger.info("Night Mode: Stop pumping water to the upstream butts...")
        print("Night Mode: Stop pumping water to the upstream butts...")

        backup_pump.disable()

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

    #Pass on readings dictionary to the logic
    temptopuplogic.readings = readings

    #Try to get a reference to the solenoid valve if we don't have one yet
    #(Can't do this in the setup function because it doesn't have access to
    #the devices dictionary.)
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

    #We have to create the CSM here, after the solenoid object has
    #been assigned, rather than in a control logic setup function,
    #otherwise there will be a spurious error message about not being
    #able to control G3:S0.
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
