#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Monitoring Tools for the River System Control and Monitoring Software
# Copyright (C) 2017-2022 Wimborne Model Town
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

#pylint: disable=logging-not-lazy
#
#Reason (logging-not-lazy): Harder to understand the logging statements that way.

"""
This is the part of the software framework that contains the
monitor thread. This is used to obtain readings from sensors
without causing the main thread to block. It also abstracts
a bit more of the complexity away.

.. module:: monitortools.py
    :platform: Linux
    :synopsis: The part of the framework that contains the monitor tools.

.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>

"""

from collections import deque
import time
import os
import traceback
import datetime
import threading
import logging

import config

from . import coretools
from . import logiccoretools

#Don't ask for a logger name, so this works with both main.py
#and the universal monitor.
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

for handler in logging.getLogger('River System Control Software').handlers:
    logger.addHandler(handler)

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

    Usage:
        >>> monitor = BaseMonitorClass(<system_id>, <probe_id>)

        .. note::
                This won't do anything helpful by itself;
                you need to derive from it.
    """

    def __init__(self, system_id, probe_id):
        """Constructor as documented above"""
        threading.Thread.__init__(self)
        #Check IDs are sane.
        for _id in (system_id, probe_id):
            if ":" in _id \
                or _id == "":

                raise ValueError("Invalid ID: "+_id)

        self.system_id = system_id
        self.probe_id = probe_id

        #The file name the readings file will have (plus the time it was
        #created)
        self.file_name = "readings/"+self.system_id+":"+self.probe_id
        self.current_file_name = None

        #A reference to the file handle of the open readings file.
        self.file_handle = None

        #The time the readings file will expire.
        self.midnight_tonight = None

        #Default reading interval. This will immediately be overridden by the
        #master pi in practice.
        self.reading_interval = 0

        #The outgoing queue for readings collected by this thread.
        self.queue = deque()

        #Queue for readings that couldn't be sent to the database.
        self.db_queue = deque()

        #The latest-but-one reading.
        self.prev_reading = ""

        #Whether the monitor is currently running.
        self.running = False

    #---------- GETTERS ----------
    def get_system_id(self):
        """
        This method returns the system ID of the probe this monitor
        is monitoring.

        Returns:
            string. The system ID.

        Usage:

            >>> <BaseMonitorClassObject>.get_system_id()
            >>> "G4"
        """
        return self.system_id

    def get_probe_id(self):
        """
        This method returns the probe ID of the probe this monitor
        is monitoring.

        Returns:
            string. The probe ID.

        Usage:

            >>> <BaseMonitorClassObject>.get_probe_id()
            >>> "M0"
        """
        return self.probe_id

    def get_reading(self):
        """
        This method returns the oldest reading on the queue (so that
        if there are multiple readings they are read in the correct
        order), and deletes it from the queue.

        The reading ID is a combination of the system ID and the
        sensor ID.

        Throws:
            IndexError, if there is no reading to return.

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
            >>> reading = <BaseMonitorClassObject>.get_previous_reading()
        """

        return self.prev_reading

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

        return bool(len(self.queue))

    #---------- SETTERS ----------
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

    #---------- RUNTIME METHODS ----------
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

        #Create the readings directory if it doesn't exist.
        if not os.path.isdir("readings"):
            logger.debug("Creating readings folder...")
            os.mkdir("readings")

        #Time format: yyyy-mm-dd hh:mm:ss
        the_time = time.strftime("%Y-%m-%d", time.localtime())

        #Open in append mode, just in case the file is already here.
        self.current_file_name = self.file_name+"-"+the_time+".csv"
        self.file_handle = open(self.current_file_name, "a", encoding="utf-8")

        try:
            #Write the start time and the CSV header.
            self.file_handle.write("\n\nStart Time: "+str(datetime.datetime.now())+"\n\n")
            self.file_handle.write("\nTIME,SYSTEM TICK,ID,VALUE,STATUS\n")
            self.file_handle.flush()

        except (OSError, IOError) as error:
            logger.error("Exception \n\n"+str(traceback.format_exc())
                         + "\n\nwhile running!")

            print("Exception \n\n"+str(traceback.format_exc())+"\n\nwhile running!")

            #Make sure the file is closed.
            self.file_handle.close()

            #Raise the error, because we don't want to continue when this fails.
            raise error

        #Set the expiration time to midnight so we can rotate readings files.
        #This uses the datetime class cos it's easier to compare times that way.
        midnight = datetime.time(hour=23, minute=59, second=59)
        current_time = datetime.datetime.now()

        self.midnight_tonight = datetime.datetime.combine(current_time.date(),
                                                          midnight)

    def handle_reading(self, reading, previous_reading):
        """
        This method handles new readings from the device/network, writing them to the
        readings file and logging them. It also flags any errors that occur.

        Args:
            reading (Reading):              The Reading object we are managing.
            previous_reading (Reading):     The last Reading object we managed.

        Returns:
            tuple(Reading, bool).

            Reading: The previous reading.

            bool:
                False -- Everything is fine.
                True -- Failed to write the reading.

        Usage:
            >>> <BaseMonitorClassObject>.handle_reading(<ReadingObject>, <ReadingObject>)
            >>> False

        """

        write_failed = False

        if not hasattr(self, "socket"):
            #Write readings to the database as well as to the files, as long as this
            #isn't just a sockets monitor running on the NAS box.
            #Try to send any queued readings.
            while self.db_queue:
                try:
                    logiccoretools.store_reading(self.db_queue[0])

                except RuntimeError:
                    #Break out after first error rather than trying loads of readings.
                    print("Error: Couldn't store queued reading, trying again later!")
                    logger.error("Error: Couldn't store queued reading, trying again later!")
                    break

                else:
                    self.db_queue.popleft()

            try:
                logiccoretools.store_reading(reading)

            except RuntimeError:
                #Queue to send later.
                self.db_queue.append(reading)

                print("Error: Couldn't store current reading, queueing for later!")
                logger.error("Error: Couldn't store current reading, queueing for later!")

        try:
            if reading == previous_reading:
                #Write a . to the file.
                logger.debug("Monitor for "+self.system_id+":"+self.probe_id
                             + ": New reading, same value as last time.")

                self.file_handle.write(".")

            else:
                #Write it to the readings file.
                logger.debug("Monitor for "+self.system_id+":"+self.probe_id
                             + ": New reading, new value: "+reading.get_value())

                self.file_handle.write("\n"+reading.as_csv())

                previous_reading = reading

            self.file_handle.flush()

        except OSError:
            logger.error("Couldn't write to readings file! "
                         + "Creating a new one...")

            print("Couldn't write to readings file! "
                  + "Creating a new one...")

            write_failed = True

        return previous_reading, write_failed

    def manage_rotation(self, write_failed, previous_reading):
        """
        This method handles rotating the readings file, and recreating it if needed, for
        example if it is missing or cannot be written to.

        Args:
            write_failed (bool):            Whether or not the last write to the readings file
                                            failed.

            previous_reading (Reading):     The last Reading object we managed.

        Returns:
            Reading.

            The previous reading.

        Usage:
            >>> <BaseMonitorClassObject>.manage_rotation(<ReadingObject>)

        """

        #Assume that all is fine by default.
        should_continue = False

        #Check if the readings file is still there.
        readings_file_exists = os.path.isfile(self.current_file_name)

        #Check if it's time to rotate the readings file.
        timediff = datetime.datetime.now() - self.midnight_tonight

        #If it's time, or the previous file is gone, create a new
        #readings file.
        if timediff.days > -1 or \
            not readings_file_exists or \
            write_failed:

            self.file_handle.close()
            self.create_file_handle()
            previous_reading = None

        if not readings_file_exists:
            logger.error("Monitor for "+self.system_id+":"+self.probe_id
                         + ": Readings file gone! Creating new one...")

            print("Monitor for "+self.system_id+":"+self.probe_id
                  + ": Readings file gone! Creating new one...")

            self.file_handle.write("WARNING: Previous readings file was "
                                   + "deleted.\n")

            #Take a new reading immediately.
            should_continue = True

        elif write_failed:
            logger.error("Monitor for "+self.system_id+":"+self.probe_id
                         + ": Can't write to readings file! Creating new one...")

            print("Monitor for "+self.system_id+":"+self.probe_id
                  + ": Can't write to readings file! Creating new one...")

            self.file_handle.write("WARNING: Couldn't write to previous readings file.\n")

            #Take a new reading immediately.
            should_continue = True

        return previous_reading, should_continue

    #----- CONTROL METHODS -----
    def wait_exit(self):
        """
        This method is used to wait for the monitor thread to exit.

        This isn't a mandatory function as the monitor thread will shut down
        automatically when config.EXITING is set to True.

        Usage:
            >>> <BaseMonitorClassObject>.wait_exit()
        """

        #Helps thread to react faster.
        self.reading_interval = 0

        while self.running:
            time.sleep(0.5)

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

        write_failed = False

        #Set up the readings file.
        self.create_file_handle()

        try:
            while not config.EXITING:
                the_reading, status_text = self.reading_func()

                #Construct a Reading object to hold this info.
                #Args in order: Time, Tick, ID, Value, Status
                reading = coretools.Reading(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                            config.TICK,
                                            self.probe.get_id(),
                                            str(the_reading), status_text)

                #Add it to the queue.
                self.queue.append(reading)

                previous_reading, write_failed = self.handle_reading(reading, previous_reading)

                previous_reading, should_continue = self.manage_rotation(write_failed,
                                                                         previous_reading)

                if should_continue:
                    continue

                #Take readings every however often it is.
                #I know we could use a long time.sleep(),
                #but this MUST be responsive to changes in the reading interval.
                count = 0

                while count < self.reading_interval:
                    #This way, if our reading interval changes,
                    #the code will respond to the change immediately.
                    time.sleep(1)
                    count += 1

        except Exception:
            #Log all of these errors to the log file.
            logger.error("Exception \n\n"+str(traceback.format_exc())
                         + "\n\nwhile running!")

            print("Exception \n\n"+str(traceback.format_exc())+"\n\nwhile running!")

        logger.debug("Monitor for "+self.system_id+":"+self.probe_id+": Exiting...")

        self.file_handle.close()
        self.running = False

# ---------- Universal Sockets Monitor ----------
class SocketsMonitor(BaseMonitorClass):
    """
    This is the universal sockets monitor thread that is used to monitor all
    probe types over a socket. It inherits from BaseMonitorClass. This is
    also quite a simple class.

    .. note::
        This class may eventually be removed  as it is no longer used, seeing as
        we now have the database in the NAS box for storing readings.

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

        write_failed = False

        #Set up the readings file.
        self.create_file_handle()

        try:
            while not config.EXITING:
                while self.socket.has_data():
                    try:
                        reading = self.socket.read()

                    except IndexError:
                        break

                    if not isinstance(reading, coretools.Reading):
                        break

                    #Check the reading is from the right probe.
                    #NB: Could check site ID, but we'll have a socket for each one, so a non-issue.
                    if reading.get_sensor_id() == self.probe_id:
                        previous_reading, write_failed = self.handle_reading(reading,
                                                                             previous_reading)

                        previous_reading, should_continue = self.manage_rotation(write_failed,
                                                                                 previous_reading)

                        if should_continue:
                            continue

                        #Remove the reading from the socket's queue.
                        self.socket.pop()

                        #Add it to the queue.
                        self.queue.append(reading)

                    else:
                        #Wait a bit for the other monitor(s) to pick it up.
                        time.sleep(0.1)

                #Check every 1 second (prevent delays in logging at sump pi end).
                time.sleep(1)

        except Exception:
            #Log all of these errors to the log file.
            logger.error("Exception \n\n"+str(traceback.format_exc())
                         + "\n\nwhile running!")

            print("Exception \n\n"+str(traceback.format_exc())+"\n\nwhile running!")

        logger.debug("SocketsMonitor for "+self.system_id+":"+self.probe_id+": Exiting...")

        self.file_handle.close()
        self.running = False
