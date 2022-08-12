#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#Wendy Butts Pi Logic for the River System Control Software
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
This is the wbuttspilogic module, which contains the control logic that runs on
Wendy Butts Pi.

.. module:: wbuttspilogic.py
    :platform: Linux
    :synopsis: Contains wendy butts pi control logic

.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>
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

def wbuttspi_logic(readings, devices, monitors, reading_interval):
    """
    This control logic does very little but monitors levels and runs the water backup
    function overnight. It does the following:

    - Updates the pi status in the database.
    - Calls wbuttspi_water_backup_logic() overnight.
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
        pass #return wbuttspi_water_backup_logic(readings, devices, monitors,
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

def wbuttspi_water_backup_logic(readings, devices, monitors, reading_interval):
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

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = wbuttspi_water_backup_logic(<listofreadings>,
        >>>                                                <listofprobes>,
        >>>                                                <areadinginterval>)

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
