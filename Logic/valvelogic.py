#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#Gate Valve Logic for the River System Control Software
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
This is the valvelogic module, which contains valve control logic, but not the logic
to control the Matrix pump.

.. module:: valvelogic.py
    :platform: Linux
    :synopsis: Contains valve control logic, but not matrix pump logic.

.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>
.. moduleauthor:: Terry Coles <wmt@hadrian-way.co.uk>
"""

import sys
import os
import logging

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

#----- Valve Control Logic (not for Matrix pump) -----
def valve_logic(devices):
    """
    This control logic is generic and runs on all the gate valves. It does the following:

    - Polls the database and sets valve positions upon request.

    """

    #Get the sensor name for this valve.
    for valve in config.SITE_SETTINGS[config.SITE_ID]["Devices"]:
        valve_id = valve.split(":")[1]

    position = None

    #Check if there's a request for a new valve position.
    try:
        state = logiccoretools.get_state(config.SITE_ID, valve_id)

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
                        logiccoretools.log_event(config.SITE_ID+": New valve position: "
                                                 + str(position))

                    except RuntimeError:
                        print("Error: Couldn't log event!")
                        logger.error("Error: Couldn't log event!")

    if position is not None:
        try:
            logiccoretools.update_status("Up, CPU: "+config.CPU+"%, MEM: "+config.MEM+"%",
                                         "OK", "Position requested: "+str(position))

        except RuntimeError:
            print("Error: Couldn't update site status!")
            logger.error("Error: Couldn't update site status!")

    else:
        try:
            logiccoretools.update_status("Up, CPU: "+config.CPU+"%, MEM: "+config.MEM+"%",
                                         "OK", "None")

        except RuntimeError:
            print("Error: Couldn't update site status!")
            logger.error("Error: Couldn't update site status!")

    return 15
