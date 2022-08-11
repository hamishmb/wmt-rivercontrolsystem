#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Logic Core Tools for the River System Control and Monitoring Software
# Copyright (C) 2020-2022 Wimborne Model Town
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
This is the logiccoretools module, which contains interfacing code to enable
the control logic to use the database without being coupled directly to the
coretools.DatabaseConnection class.

.. module:: logiccoretools.py
    :platform: Linux
    :synopsis: Code to interface between control logic and DatabaseConnection class.

.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>
"""

import logging

import config

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

def get_latest_reading(site_id, sensor_id, retries=3):
    """
    This method returns the latest reading for the given sensor at the given site.

    Args:
        site_id (str).            The site we want the reading from.
        sensor_id (str).          The sensor we want the reading for.

    KWargs:
        retries[=3] (int).        The number of times to retry before giving up
                                  and raising an error.

    Returns:
        A Reading object.       The latest reading for that sensor at that site.

        OR

        None.                   There is no reading available to return.

    Throws:
        RuntimeError, if the query failed too many times.

    Usage example:
        >>> get_latest_reading("G4", "M0")
        >>> 'Reading at time 2020-09-30 12:01:12.227565, and tick 0, from probe: G4:M0, with value: 350, and status: OK'

    """

    return config.DBCONNECTION.get_latest_reading(site_id, sensor_id, retries)

def get_n_latest_readings(site_id, sensor_id, number, retries=3):
    """
    This method returns last n readings for the given sensor at the given site.
    If the list is empty, or contains fewer readings than was asked for, this
    means there aren't enough readings to return all of them.

    Args:
        site_id.            The site we want the reading from.
        sensor_id.          The sensor we want the reading for.
        number.             The number of readings.

    KWargs:
        retries[=3] (int).        The number of times to retry before giving up
                                  and raising an error.

    Returns:
        List of (Reading objects).       The latest readings for that sensor at that site.

    Throws:
        RuntimeError, if the query failed too many times.

    Usage example:
        >>> get_latest_reading("G4", "M0")
        >>> 'Reading at time 2020-09-30 12:01:12.227565, and tick 0, from probe: G4:M0, with value: 350, and status: OK'

    """

    return config.DBCONNECTION.get_n_latest_readings(site_id, sensor_id, number, retries)

def get_state(site_id, sensor_id, retries=3):
    """
    This method queries the state of the given sensor/device. Information is returned
    such as what (if anything) has been requested, if it is Locked or Unlocked,
    and which pi locked it, if any.

    Args:
        site_id.            The site that holds the device we're interested in.
        sensor_id.          The sensor we want to know about.

    KWargs:
        retries[=3] (int).        The number of times to retry before giving up
                                  and raising an error.

    Returns:
        tuple.      1st element:        Device status (str) ("Locked" or "Unlocked").
                    2nd element:        Request (str) (values depend on device).
                    3rd element:        Locked by (str) (site id as defined in config.py).

        OR

        None.           No data available.

    Throws:
        RuntimeError, if the query failed too many times.

    Usage:
        >>> get_state("VALVE4", "V4")
        >>> ("Locked", "50%", "SUMP")

    """

    return config.DBCONNECTION.get_state(site_id, sensor_id, retries)

def get_status(site_id, retries=3):
    """
    This method queries the status of the given site.

    Args:
        site_id.            The site that we're interested in.

    KWargs:
        retries[=3] (int).        The number of times to retry before giving up
                                  and raising an error.

    Returns:
        tuple.      1st element:        Pi status (str).
                    2nd element:        Sw status (str).
                    3rd element:        Current Action (str).

        OR

        None.           No data available.

    Throws:
        RuntimeError, if the query failed too many times.

    Usage:
        >>> get_status("VALVE4")
        >>> ("Up", "OK", "None")

    """

    return config.DBCONNECTION.get_status(site_id, retries)

def attempt_to_control(site_id, sensor_id, request, retries=3):
    """
    This method attempts to lock the given sensor/device so we can take control.
    First we check if the device is locked. If it isn't locked, or this pi locked it,
    then we take control and note the requested action, and True is returned.

    Otherwise, we don't take control, and False is returned.

    Args:
        site_id.            The site that holds the device we're interested in.
        sensor_id.          The sensor we want to know about.
        request (str).      What state we want the device to be in.

    KWargs:
        retries[=3] (int).        The number of times to retry before giving up
                                  and raising an error.

    Returns:
        boolean.        True - We are now in control of the device.
                        False - The device is locked and in use by another pi.

    Throws:
        RuntimeError, if the query failed too many times.

    Usage:
        >>> attempt_to_control("SUMP", "P0", "On")
        >>> True

    """

    return config.DBCONNECTION.attempt_to_control(site_id, sensor_id, request, retries)

def release_control(site_id, sensor_id, retries=3):
    """
    This method attempts to release the given sensor/device so other pis can
    take control. First we check if we locked the device. If it isn't locked,
    or this pi didn't lock it, we return without doing anything.

    Otherwise, we unlock the device.

    Args:
        site_id.            The site that holds the device we're interested in.
        sensor_id.          The sensor we want to know about.

    KWargs:
        retries[=3] (int).        The number of times to retry before giving up
                                  and raising an error.

    Throws:
        RuntimeError, if the query failed too many times.

    Usage:
        >>> release_control("SUMP", "P0")
        >>>

    """

    return config.DBCONNECTION.release_control(site_id, sensor_id, retries)

def log_event(event, severity="INFO", retries=3):
    """
    This method logs the given event message in the database.

    Use it sparingly, to log events that seem significant.

    Args:
        event (str).                The event to log.

    Kwargs:
        severity[="INFO"] (str).    The severity of the event.
                                    "DEBUG", "INFO", "WARNING", "ERROR", or "CRITICAL".

        retries[=3] (int).          The number of times to retry before giving up
                                    and raising an error.

    Throws:
        RuntimeError, if the query failed too many times.

    Usage:
        >>> log_event("test", "INFO")
        >>>
    """

    return config.DBCONNECTION.log_event(event, severity, retries)

def update_status(pi_status, sw_status, current_action, retries=3):
    """
    This method logs the given statuses and action(s) in the database.

    pi_status can be used to provide useful hardware and OS status.

    sw_status can be used to provide useful information about the status of the
    river control system software, which could include a current state or mode
    of the control logic.

    current_action can be used to describe current physical actions such as
    intended water movements.

    All should be concise.

    Args:
        pi_status (str).            The current status of this pi.
        sw_status (str).            The current status of the software on this pi.
        current_action (str).       The software's current action(s).

    Kwargs:
        retries[=3] (int).          The number of times to retry before giving up
                                    and raising an error.

    Throws:
        RuntimeError, if the query failed too many times.

    Usage:
        >>> update_status("Up", "OK", "None")
        >>>
    """

    return config.DBCONNECTION.update_status(pi_status, sw_status, current_action, retries)

def get_latest_tick(retries=3):
    """
    This method gets the latest tick from the database. Used to restore
    the system tick on NAS bootup.

    .. warning::
            This is only meant to be run from the NAS box. The pis
            get the ticks over the socket - this is a much less
            efficient way to deliver system ticks.

    Kwargs:
        retries[=3] (int).          The number of times to retry before giving up
                                    and raising an error.

    Throws:
        RuntimeError, if the query failed too many times.

    Returns:
        int. The latest system tick.

    Usage:
        >>> tick = get_latest_tick()
    """

    return config.DBCONNECTION.get_latest_tick(retries)

def store_tick(tick, retries=3):
    """
    This method stores the given system tick in the database.

    .. warning::
            This is only meant to be run from the NAS box. It will
            exit immediately with no action if run on another system.

    Args:
        tick (int). The system tick to store.

    Kwargs:
        retries[=3] (int).          The number of times to retry before giving up
                                    and raising an error.

    Throws:
        RuntimeError, if the query failed too many times.

    Usage:
        >>> store_tick(<int>)
        >>>
    """

    return config.DBCONNECTION.store_tick(tick, retries)

def store_reading(reading, retries=3):
    """
    This method stores the given reading in the database.

    Args:
        reading (Reading). The reading to store.

    Kwargs:
        retries[=3] (int).          The number of times to retry before giving up
                                    and raising an error.

    Throws:
        RuntimeError, if the query failed too many times.

    Usage:
        >>> store_reading(<Reading-Obj>)
        >>>
    """

    return config.DBCONNECTION.store_reading(reading, retries)
