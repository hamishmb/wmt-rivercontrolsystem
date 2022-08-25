#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#Sump Pi Logic for the River System Control Software
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
This is the sumppilogic module, which contains control logic for Sump Pi.

.. module:: sumppilogic.py
    :platform: Linux
    :synopsis: Contains control logic for Sump Pi.

.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>
.. moduleauthor:: Patrick Wigmore <pwbugreports@gmx.com>
.. moduleauthor:: Terry Coles <wmt@hadrian-way.co.uk>
"""

import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.abspath('..'))

import config
from Tools import logiccoretools

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

def sumppi_logic(readings, devices, monitors, reading_interval):
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

        reading_interval (int):         The current reading interval, in
                                        seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = sumppi_logic(<listofreadings>,
        >>>                                 <listofprobes>, <listofmonitors>,
        >>>                                 <areadinginterval)

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
        #We might be pumping right now, or the level might be increasing, but do nothing.
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

        #Stop pumping to the butts if they are full, but don't start pumping at this level.
        #If they are full, do nothing and let the sump overflow.
        if butts_float_reading == "False":
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

        logger.info("Setting reading interval to 1 minute...")
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

        #Always open the gate valve, regardless of buttspi level.
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
