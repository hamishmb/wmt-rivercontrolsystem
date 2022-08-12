#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#NAS box Control Logic for the River System Control Software
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
This is the naslogic module, which contains control logic for the NAS box.

.. module:: naslogic.py
    :platform: Linux
    :synopsis: Contains NAS box control logic.

.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>
"""

import sys
import os
import logging
import subprocess

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

def nas_logic(readings, devices, monitors, sockets, reading_interval):
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
