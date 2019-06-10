#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Monitoring Tools for the River System Control and Monitoring Software Version 0.10.0
# Copyright (C) 2017-2019 Wimborne Model Town
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

from . import coretools

# ---------- BASE CLASS ----------
class BaseMonitorClass(threading.Thread):
    """
    This is a base monitor class that all other monitors
    inherit from. It contains common functionality and
    instance variables and is used to reduce code duplication.

    Documentatation for constructor for objects of type BaseMonitorClass:

    Absolutely useless by itself, because this class
    is incapable of monitoring a probe without being
    derived from.

    Args:
        system_id (str):            The ID of the pi/system
                                    this monitor is running on eg G4.

        probe_id (str):             The ID of the probe we're looking for.

    Invokes:
        threading.Thread.__init__(self), to initialise
        the subclass deriving from this as a thread.

    Usage:
        >>> monitor = BaseMonitorClass(<system_id>, <probe_id>)

        .. note::
                This won't do anything helpful by itself;
                you need to derive from it.
    """

    def __init__(self, system_id, probe_id):
        """Constructor as documented above"""
        threading.Thread.__init__(self)
        self.system_id = system_id
        self.probe_id = probe_id

        #The file name the readings file will have (plus the time it was
        #created)
        self.file_name = "readings/"+self.system_id+":"+self.probe_id

        #A reference to the file handle of the open readings file.
        self.file_handle = None

        #The time the readings file was created.
        self.file_creation_time = None

        #The interval at which we want to rotate the readings file, in days.
        self.file_rotate_interval = 7

        #Default reading interval. This will immediately be overridden by the
        #master pi in practice.
        self.reading_interval = 0

        #The outgoing queue for readings collected by this thread.
        self.queue = deque()

        #The latest-but-one reading.
        self.prev_reading = ""

        #Whether the monitor is currently running.
        self.running = False

        #Used to ask the monitor thread to exit.
        self.should_exit = False

    def create_file_handle(self):
        """
        This method is used to create / update the
        file containing the readings for this probe.
        The file will be opened in append mode, and
        a CSV header and start time will be written.

        The name for the file will be readings/<system_id>:<probe_name>.csv

        For example: readings/G4:M0.csv

        Usage:
            >>> <BaseMonitorClassObject>.create_file_handle()

        """

        #TODO need a logger here and to catch exceptions.
        #Time format: yyyy-mm-dd hh:mm:ss
        the_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        self.file_handle = open(self.file_name+"-"+the_time+".csv", "a")

        #Write the start time and the CSV header.
        self.file_handle.write("\n\nStart Time: "+the_time+"\n\n")
        self.file_handle.write("\nTIME,SYSTEM TICK,ID,VALUE,STATUS\n")
        self.file_handle.flush()

        #Set the file creation time so we can rotate readings files.
        #This uses the datetime class cos it's easier to compare times that way.
        self.file_creation_time = datetime.datetime.now()

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

        Returns:
            A Reading object (see coretools.Reading).

            .. note::
                  The content of the value attribute differs slightly
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
            A Reading object.

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
        probe (BaseDeviceClass):    A reference to a
                                    probe object.

        reading_interval (int):     The initial reading
                                    interval for the
                                    monitor to use.

        system_id (str):            As defined in BaseMonitorClass'
                                    constructor.

    Invokes:
        Constructor for BaseMonitorClass.
        self.start() - starts the monitor thread.

    Usage:
        >>> monitor = Monitor(<aProbeObject>, <aReadingInterval>, <anID>)
    """

    def __init__(self, probe, reading_interval, system_id):
        BaseMonitorClass.__init__(self, system_id, probe.get_device_id())

        self.probe = probe
        self.reading_interval = reading_interval
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

        previous_reading = None #NB: Just to use here, rather then self.prev_reading,
                                #which is for external users.
        self.running = True

        #Set up the readings file.
        self.create_file_handle()

        try:
            while not self.should_exit:
                the_reading, status_text = self.reading_func()

                #Construct a Reading object to hold this info.
                #Args in order: Time, Tick, ID, Value, Status
                reading = coretools.Reading(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                            -1,
                                            self.probe.get_id(),
                                            str(the_reading), status_text)

                #Add it to the queue.
                self.queue.append(reading)

                if reading == previous_reading:
                    #Write a . to the file.
                    self.file_handle.write(".")

                else:
                    #Write it to the readings file.
                    self.file_handle.write("\n"+reading.as_csv())

                    previous_reading = reading

                self.file_handle.flush()

                #Take readings every however often it is.
                #I know we could use a long time.sleep(),
                #but this MUST be responsive to changes in the reading interval.
                count = 0

                while count < self.reading_interval:
                    #This way, if our reading interval changes,
                    #the code will respond to the change immediately.
                    time.sleep(1)
                    count += 1

                #Check if it's time to rotate the readings file.
                timediff = datetime.datetime.now() - self.file_creation_time

                if timediff.days >= self.file_rotate_interval:
                    self.file_handle.close()
                    self.create_file_handle()
                    previous_reading = None

        except BaseException as err:
            #Ignore all errors. Generally bad practice :P
            print("\nCaught Exception: ", err)

        self.file_handle.close()
        self.running = False

# ---------- Universal Sockets Monitor ----------
class SocketsMonitor(BaseMonitorClass):
    """
    This is the universal sockets monitor thread that is used to monitor all
    probe types over a socket. It inherits from BaseMonitorClass. This is
    also quite a simple class.

    Documentation for constructor for objects of type SocketsMonitor:

    Args:
        socket (Sockets):           The socket to read readings from.

        system_id (str):            As defined in BaseMonitorClass'
                                    constructor.

        probe_id (str):             As defined in BaseMonitorClass'
                                    constructor.

    Invokes:
        Constructor for BaseMonitorClass.
        self.start() - starts the monitor thread.

    Usage:
        >>> monitor = Monitor(<aProbeObject>, <anInteger>, <aReadingInterval>, <anID>)
    """

    def __init__(self, socket, system_id, probe_id):
        BaseMonitorClass.__init__(self, system_id, probe_id)

        self.socket = socket
        self.probe_id = probe_id

        self.start()

    def run(self):
        """
        This method is the body of the thread. It does some setup and then
        enters a monitor loop, where it checks for readings and adds them
        to the queue every second (to avoid delays in logging over the network).

        The loop will continue to run until it is asked to exit.

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

        previous_reading = None #NB: Just to use here, rather then self.prev_reading,
                                #which is for external users.
        self.running = True

        #Set up the readings file.
        self.create_file_handle()

        try:
            while not self.should_exit:

                while self.socket.has_data():
                    try:
                        reading = self.socket.read()

                    except IndexError:
                        break

                    #Check the reading is from the right probe.
                    #NB: Could check site ID, but we'll have a socket for each one, so a non-issue.
                    if reading.get_sensor_id() == self.probe_id:
                        #Remove from socket.
                        self.socket.pop()

                        #Add it to the queue.
                        self.queue.append(reading)

                        if reading == previous_reading:
                            #Write a . to the file.
                            self.file_handle.write(".")

                        else:
                            #Write it to the readings file.
                            self.file_handle.write("\n"+reading.as_csv())

                            previous_reading = reading

                        self.file_handle.flush()

                #Check every 1 second (prevent delays in logging at sump pi end).
                time.sleep(1)

                #Check if it's time to rotate the readings file.
                timediff = datetime.datetime.now() - self.file_creation_time

                if timediff.days >= self.file_rotate_interval:
                    self.file_handle.close()
                    self.create_file_handle()
                    previous_reading = None

        except BaseException as err:
            #Ignore all errors. Generally bad practice :P
            print("\nCaught Exception: ", err)

        self.file_handle.close()
        self.running = False
