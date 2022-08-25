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

.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>
.. moduleauthor:: Patrick Wigmore <pwbugreports@gmx.com>
.. moduleauthor:: Terry Coles <wmt@hadrian-way.co.uk>
"""

import sys
import os
import logging

sys.path.insert(0, os.path.abspath('..'))

import config
from Tools import logiccoretools

#Import logic modules.
from . import valvelogic
from . import naslogic
from . import sumppilogic
from . import wbuttspilogic
from . import stagepilogic
from . import temptopuplogic

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

#----- Generic control logic for pis that only do monitoring -----
def generic_control_logic(readings, devices, monitors, reading_interval):
    """
    This control logic is generic and runs on all the monitoring-only pis.
    It does the following:

    - Updates the pi status in the database.
    - Always returns a reading interval of 15 seconds - always faster than other intervals.

    Args:
        readings (list):            A list of the latest readings for each local probe/device.

        devices  (list):            A list of all local device objects.

        monitors (list):            A list of all local monitor objects.

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = generic_control_logic(<listofreadings>,
        >>>                                          <listofprobes>, <listofmonitors>,
        >>>                                          <areadinginterval)

    """

    try:
        logiccoretools.update_status("Up, CPU: "+config.CPU+"%, MEM: "+config.MEM+" MB",
                                     "OK", "None")

    except RuntimeError:
        print("Error: Couldn't update site status!")
        logger.error("Error: Couldn't update site status!")

    return 15

#---------- Control Logic Setup Functions ----------
#----- Stage Pi Control Logic Setup Function -----
def stagepi_control_logic_setup():
    """
    Set-up function for stagepi's control logic.

    Initialises a StagePiControlLogic object for state persistence.
    """
    #Initialise the control state machine
    stagepilogic.csm = stagepilogic.StagePiControlLogic()

#---------- Control Logic Integration Functions ----------
#----- Valve Control Logic Integration Function -----
def valve_logic(readings, devices, monitors, reading_interval):
    """
    Control logic integration for the gate valves. Just runs the identically-namedlogic at
    Tools/valvelogic.py.

    Args:
        readings (list):            A list of the latest readings for each local probe/device.

        devices  (list):            A list of all local device objects.

        monitors (list):            A list of all local monitor objects.

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = valve_logic(<listofreadings>,
        >>>                                <listofprobes>, <listofmonitors>,
        >>>                                <areadinginterval)
    """

    return valvelogic.valve_logic(devices)

#----- NAS Box Control Logic Integration Function
def nas_logic(readings, devices, monitors, reading_interval):
    """
    Control logic integration for NAS box. Just runs the identically-named logic at
    Tools/naslogic.py.

    Args:
        readings (list):            A list of the latest readings for each probe/device.

        devices  (list):            A list of all local device objects.

        monitors (list):            A list of all local monitor objects.

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = nas_logic(<listofreadings>,
        >>>                              <listofprobes>, <listofmonitors>,
        >>>                              <areadinginterval)
    """

    return naslogic.nas_logic()

#----- Sump Pi Control Logic Integration Function -----
def sumppi_logic(readings, devices, monitors, reading_interval):
    """
    Control logic integration for sumppi. Just runs the identically-named logic at
    Tools/sumppilogic.py.

    Args:
        readings (list):            A list of the latest readings for each local probe/device.

        devices  (list):            A list of all local device objects.

        monitors (list):            A list of all local monitor objects.

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = sumppi_logic(<listofreadings>,
        >>>                                 <listofprobes>, <listofmonitors>,
        >>>                                 <areadinginterval)
    """

    return sumppilogic.sumppi_logic(readings, devices, monitors, reading_interval)

#----- Wendy Butts Pi Control Logic Integration Function -----
def wbuttspi_logic(readings, devices, monitors, reading_interval):
    """
    Control logic integration for wendy butts pi. Just runs the identically-named
    logic at Tools/wbuttspilogic.py.

    Args:
        readings (list):            A list of the latest readings for each local probe/device.

        devices  (list):            A list of all local device objects.

        monitors (list):            A list of all local monitor objects.

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = wbuttspi_logic(<listofreadings>,
        >>>                                   <listofprobes>, <listofmonitors>,
        >>>                                   <areadinginterval)
    """

    return wbuttspilogic.wbuttspi_logic(readings, devices, monitors, reading_interval)

#----- Stage Pi Control Logic Integration Function -----
def stagepi_control_logic(readings, devices, monitors, reading_interval):
    """
    Control logic for stagepi's zone of responsibility.

    This mainly just wraps StagePiControlLogic.doLogic(), but it also contains
    some other integration glue.

    Run stagepi_control_logic_setup once before first running this function.

    See StagePiControlLogic for documentation.

    Args:
        readings (list):            A list of the latest readings for each local probe/device.

        devices  (list):            A list of all local device objects.

        monitors (list):            A list of all local monitor objects.

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = stagepi_control_logic(<listofreadings>,
        >>>                                     <listofprobes>, <listofmonitors>,
        >>>                                     <areadinginterval)

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

#----- Hanham Pi Temporary Top Up Control Logic Integration Function -----
def temptopup_control_logic(readings, devices, monitors, reading_interval):
    """
    Control logic function for the temporary top-up control logic, which
    tops up the G1 butts group with mains water at about 15:00 daily if
    the level is too low.

    This mainly just wraps TempTopUpLogic.doLogic(), but it also contains
    some other integration glue.

    Run temptopup_control_logic_setup once before first running this function.

    See TempTopUpLogic for documentation.

    Args:
        readings (list):            A list of the latest readings for each local probe/device.

        devices  (list):            A list of all local device objects.

        monitors (list):            A list of all local monitor objects.

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = stagepi_control_logic(<listofreadings>,
        >>>                                     <listofprobes>, <listofmonitors>,
        >>>                                     <areadinginterval)
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
