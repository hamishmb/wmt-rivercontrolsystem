#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Monitoring Tools for the River System Control and Monitoring Software Version 0.9.1
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

"""
This is the part of the software framework that contains the
monitor thread. This is used to obtain readings from sensors
without causing the main thread to block. It also abstracts
a bit more of the complexity away.

.. module:: monitortools.py
    :platform: Linux
    :synopsis: The part of the framework that contains the monitor tools.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>

"""

from collections import deque
import time
import datetime
import threading

VERSION = "0.9.1"

# ---------- BASE CLASS ----------
class BaseMonitorClass(threading.Thread):
    """
    This is a base monitor class that all other monitors
    inherit from. It contains common functionality and
    instance variables and is used to reduce code duplication.

    It might be time to integrate this with Monitor and
    remove it, because we no longer have separate monitors
    for each type of probe, because the probe classes' API
    is now standardised.

    Documentatation for constructor for objects of type BaseMonitorClass:

    Absolutely useless by itself, because this class
    is incapable of monitoring a probe without being
    derived from.

    Args:
        self (BaseMonitorClass):    A self-reference.
                                    Only passed when
                                    helping construct
                                    a subclass.

        probe (BaseDeviceClass):    A reference to a
                                    probe object.

        num_readings (int):         The number of
                                    readings to take.
                                    If 0, take readings
                                    until requested to
                                    exit.

        reading_interval (int):     The initial reading
                                    interval for the
                                    monitor to use.

        system_id (str):            The ID of the pi/system
                                    this monitor is running on eg G4.

    Invokes:
        threading.Thread.__init__(self), to initialise
        the subclass deriving from this as a thread.

    Usage:
        >>> monitor = BaseMonitorClass(<aProbeObject>, <anInteger>, <aReadingInterval>, <anID>)

        ..note::
                This won't do anything helpful by itself;
                you need to derive from it.
    """

    def __init__(self, probe, num_readings, reading_interval, system_id):
        """Constructor as documented above"""
        threading.Thread.__init__(self)
        self.probe = probe
        self.num_readings = num_readings
        self.reading_interval = reading_interval
        self.system_id = system_id
        self.queue = deque()
        self.prev_reading = ""
        self.running = False
        self.should_exit = False

    def is_running(self):
        """
        This method returns True if the monitor is
        running, else False.

        Returns:
            bool. The state:

                True  --    Currently running.
                False --    Not running.

        Usage:
            >>> state = <BaseMonitorClassObject>.is_running()

        """

        return self.running

    def has_data(self):
        """
        This method returns True if the monitor has data sat on
        its readings queue waiting to be read. False if the queue
        is empty.

        Returns:
            bool.

                True  --    Data available.
                False --    No Data available.

        Usage:
            >>> state = <BaseMonitorClassObject>.has_data()
        """

        return int(len(self.queue))

    def get_reading(self):
        """
        This method returns the oldest reading on the queue (so that
        if there are multiple readings they are read in the correct
        order), and deletes it from the queue.

        The reading ID is a combination of the system ID and the
        sensor ID.

        Reading Format:
            tuple (str (reading_id), str (time), str (reading), str (status)).

            For example:

                >>> get_reading()
                >>> ("2017-10-25 22:59:09.439380", "500", "OK")

            .. note::
                  The format of the "reading" section differs slightly
                  between probe types, because they eg don't all measure
                  water depth in mm.

        Usage:

            >>> reading_id, time, reading, status = <BaseMonitorClassObject>.get_reading()
        """

        self.prev_reading = self.queue[0]

        return self.queue.popleft()

    def get_previous_reading(self):
        """
        This method returns the previous (next-to-newest) reading.
        Call it before you get the next reading.

        The reading format differs to the above, because the time
        and status aren't included. Only the value is included eg
        "500".

        Returns:
            string. The reading.

        Usage:
            >>> reading =  <BaseMonitorClassObject>.get_previous_reading()
        """

        return self.prev_reading

    def set_reading_interval(self, interval):
        """
        This method sets the reading interval, with immediate effect (ie, if
        the monitor is currently waiting using the reading interval, it will
        NOT continue to wait for the whole length of the old reading interval).

        Args:
            interval:   New reading interval, in seconds.

        Usage:
            >>> <BaseMonitorClassObject>.set_reading_interval(<AnInteger>)
        """

        self.reading_interval = interval

    def request_exit(self, wait=False):
        """
        This method is used to ask the monitor thread to exit. It can also wait
        for the monitor thread to exit before returning if you specify a special
        argument.

        KWargs:
            wait (bool):    Whether to wait for the thread to exit before returning.
                            Default: False.

        Usage:
            >>> <BaseMonitorClassObject>.request_exit() //Don't wait for thread to exit.

            OR:

            >>> <BaseMonitorClassObject>.request_exit() //Wait for thread to exit.
        """

        self.should_exit = True
        self.reading_interval = 0 #Helps thread to react faster.

        if wait:
            while self.running:
                time.sleep(5)

# ---------- Universal Monitor ----------
class Monitor(BaseMonitorClass):
    """
    This is the universal monitor thread that is used to monitor all probe
    types. It inherits from BaseMonitorClass. This is quite a simple class.

    Documentation for constructor for objects of type Monitor:

    Args:
        probe (BaseDeviceClass):    As defined in BaseMonitorClass'
                                    constructor.

        num_readings (int):         As defined in BaseMonitorClass'
                                    constructor.

        reading_interval (int):     As defined in BaseMonitorClass'
                                    constructor.

        system_id (str):            As defined in BaseMonitorClass'
                                    constructor.

    Invokes:
        Constructor for BaseMonitorClass.
        self.start() - starts the monitor thread.

    Usage:
        >>> monitor = Monitor(<aProbeObject>, <anInteger>, <aReadingInterval>, <anID>)
    """

    def __init__(self, probe, num_readings, reading_interval, system_id):
        BaseMonitorClass.__init__(self, probe, num_readings, reading_interval, system_id)

        self.probe = probe
        self.reading_func = probe.get_reading

        self.start()

    def run(self):
        """
        This method is the body of the thread. It does some setup and then
        enters a monitor loop, where it checks for readings and adds them
        to the queue at every interval of <reading_interval> seconds long.

        The loop will continue to run until either it has taken the number
        of readings that was asked of it, or it is asked to exit.

        Usage:

            .. warning::
                Only call me from within a constructor with start(). Do **NOT** call
                me with run(), and **ABSOLUTELY DO NOT** call me outside a constructor
                for objects of this type.

            .. warning::
                Doing the above could cause any number of strange and unstable
                situations to occcur. Running self.start() is the only way (with the
                threading library) to start a new thread.

            >>> self.start()

        """

        num_readings_taken = 0
        self.running = True

        try:
            while (not self.should_exit) and (self.num_readings == 0 or (num_readings_taken < self.num_readings)):
                the_reading, status_text = self.reading_func()

                #Format: Time, reading, status.
                self.queue.append([self.system_id+":"+self.probe.get_name(),
                                   str(datetime.datetime.now()), str(the_reading), status_text])

                if self.num_readings != 0:
                    num_readings_taken += 1

                #Take readings every however often it is.
                #I know we could use a long time.sleep(),
                #but this MUST be responsive to changes in the reading interval.
                count = 0

                while count < self.reading_interval:
                    #This way, if our reading interval changes,
                    #the code will respond to the change immediately.
                    time.sleep(1)
                    count += 1

        except BaseException as err:
            #Ignore all errors. Generally bad practice :P
            print("\nCaught Exception: ", err)

        self.running = False

