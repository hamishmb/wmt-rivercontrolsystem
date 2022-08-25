#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Core Tools for the River System Control and Monitoring Software
# Copyright (C) 2017-2022 Wimborne Model Town
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
#pylint: disable=wrong-import-position
#
#Reason (logging-not-lazy): Harder to understand the logging statements that way.
#Reason (wrong-import-position): Pylint is confused by the need to modify sys.path.

"""
This is the coretools module, which contains tools used in various other places
in the software framework. Currently this also contains the control logic, but
this is likely to move to some new files once we have the new algorithms.

.. module:: coretools.py
    :platform: Linux
    :synopsis: Contains tools used by all parts of the software.

.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>
.. moduleauthor:: Patrick Wigmore <pwbugreports@gmx.com>
"""

#Standard imports
import sys
import time
import threading
import subprocess
import logging
from collections import deque
import datetime
import os.path

#Extra imports.
import MySQLdb as mysql
import psutil

#Import modules.
sys.path.insert(0, os.path.abspath('..'))

import config
from Tools import sockettools

#Don't ask for a logger name, so this works with both main.py
#and the universal monitor.
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

for handler in logging.getLogger('River System Control Software').handlers:
    logger.addHandler(handler)

class Reading:
    """
    This class is used to represent a reading. Each reading has an ID, a time,
    a value, and a status. This is subject to change later on, but I shall try
    to maintain backward compatibility if desired.

    Documentation for the constructor for objects of type Reading:

    Args:
        self (Reading):             A self-reference. Only used when helping
                                    construct a subclass. There are no
                                    subclasses of Reading at this time.

        reading_time (String):      The time of the reading. Format as returned
                                    from running str(datetime.datetime.now()).

        reading_tick (int):         The system tick number at the time the reading
                                    was taken. A positive integer.

        reading_id (String):        The ID for the reading. Format: Two
                                    characters to identify the group, followed
                                    by a colon, followed by two more characters
                                    to identify the probe. Example: "G4:M0".

        reading_value (String):     The value of the reading. Format differs
                                    depending on probe type at the moment.
                                    Ideally, these would all be values in mm like:
                                    "400mm".

        reading_status (String):    The status of the probe at the time the reading
                                    was taken. If there is no fault, this should be
                                    "OK". Otherwise, it should be "FAULT DETECTED: "
                                    followed by some sensor-dependant information
                                    about the fault.

    Usage:
        The constructor for this class takes four arguments as specified above.

        >>> my_reading = core_tools.Reading(<a_time>, <a_tick>, <an_id>, <a_value>, <a_status>)

    .. note::
        Equality methods have been implemented for this class so you can do things like:

        >>> reading_1 == reading_2

        AND:

        >>> reading_2 != reading_3

        With ease.
    """

    # ---------- CONSTRUCTORS ----------
    def __init__(self, reading_time, reading_tick, reading_id, reading_value, reading_status): #pylint: disable=too-many-arguments
        """This is the constructor as defined above"""
        #Set some semi-private variables.
        #Check the time is a string.
        if not isinstance(reading_time, str):
            raise ValueError("reading_time argument must be of type str")

        self._time = reading_time

        #Check the tick is valid.
        if not isinstance(reading_tick, int) or \
            isinstance(reading_tick, bool):

            raise ValueError("reading_tick argument must be of type int")

        if not reading_tick >= 0:
            raise ValueError("reading_tick argument must be a positive int")

        self._tick = reading_tick

        #Check the ID is valid.
        if not isinstance(reading_id, str) \
            or ":" not in reading_id \
            or len(reading_id.split(":")) != 2 \
            or reading_id.split(":")[0] == "" \
            or reading_id.split(":")[1] == "":

            raise ValueError("Invalid ID: "+str(reading_id))

        self._id = reading_id

        #Check the value is valid.
        if not isinstance(reading_value, str):
            raise ValueError("reading_value argument must be of type str")

        self._value = reading_value

        #Check the status is valid.
        if not isinstance(reading_status, str):
            raise ValueError("reading_status argument must be of type str")

        self._status = reading_status

    # ---------- INFO GETTER METHODS ----------
    def get_id(self):
        """
        This method returns the **full** ID for this reading, consisting of
        the group ID, and then the sensor ID.

        Usage:
            >>> <Reading-Object>.get_id()
            >>> "G4:FS0"
        """

        return self._id

    def get_group_id(self):
        """
        This method returns the **group** ID for this reading.

        Usage:
            >>> <Reading-Object>.get_group_id()
            >>> "G4"
        """

        return self._id.split(":")[0]

    def get_sensor_id(self):
        """
        This method returns the **sensor** ID for this reading.

        Usage:
            >>> <Reading-Object>.get_sensor_id()
            >>> "M0"
        """

        return self._id.split(":")[1]

    def get_tick(self):
        """
        This method returns the tick when this reading was taken.

        Usage:
            >>> <Reading-Object>.get_tick()
            >>> 101
        """

        return self._tick

    def get_time(self):
        """
        This method returns the time when this reading was taken.

        Usage:
            >>> <Reading-Object>.get_time()
            >>> "2018-04-11 21:51:36.821528"
        """

        return self._time

    def get_value(self):
        """
        This method returns the value for this reading.

        Usage:
            >>> <Reading-Object>.get_value()
            >>> "600mm"
        """

        return self._value

    def get_status(self):
        """
        This method returns the status for this reading.

        Usage:
            >>> <Reading-Object>.get_status()
            >>> "OK"                        //No faults.

            OR:

            >>> <Reading-Object>.get_status()
            >>> "FAULT DETECTED: <detail>"  //Fault(s) detected.
        """

        return self._status

    # ---------- EQUALITY COMPARISON METHODS ----------
    def __eq__(self, other):
        """
        This method is used to compare objects of type Reading.

        Currently, objects are equal if all their attributes and values
        are the same (ignoring the time and tick), and neither object is None.

        Usage:
            >>> reading_1 == reading_2
            >>> False

            OR:

            >>> reading_3 == reading_4
            >>> True
        """

        #If the other object is None then it isn't equal.
        if other is None:
            return False

        try:
            #This will return True if all the attributes and values are equal,
            #ignoring the time the reading was taken and the tick.
            return (self._id == other.get_id()
                    and self._value == other.get_value()
                    and self._status == other.get_status())

        except AttributeError:
            return False

    def __ne__(self, other):
        """
        This method is used to compare objects of type Reading.

        It simply does the same as the __eq__ method and then uses a
        boolean NOT on it.

        Usage:
            >>> reading_1 != reading_2
            >>> True

            OR:

            >>> reading_3 != reading_4
            >>> False
        """

        return not self == other

    # ---------- OTHER CONVENIENCE METHODS ----------
    def __str__(self):
        """
        Just like a Java toString() method.

        Usage:
            >>> print(reading_1)
            >>> Reading at time 2018, and tick 101, from probe: G4:M0, with value: 500, and status: FAULT DETECTED
        """

        return ("Reading at time " + self._time
                + ", and tick " + str(self._tick)
                + ", from probe: " + self._id
                + ", with value: " + self._value
                + ", and status: " + self._status)

    def as_csv(self):
        """
        Returns a representation of the Reading object in CSV format.
        (Comma-Separated Values).

        Returns:
            A String - the comma-separated values.

            Format:
                >>> TIME,TICK,FULL_ID,VALUE,STATUS

        Usage:
            >>> reading_1.as_csv()
            >>> 2018-06-11 11:04:01.635548,101,G4:M0,500,OK
        """
        return (self._time
                + "," + str(self._tick)
                + "," + self._id
                + "," + self._value
                + "," + self._status)

class SyncTime(threading.Thread):
    """
    This class starts a thread that repeatedly synchronises the system time of
    all the pis with Sump Pi's hardware clock every day. Note that special permissions
    need to have been granted to normal users for this to work when not run as root.

    Constructor args:
        system_id (String):             The system ID of this pi.
    """

    def __init__(self, system_id):
        """The constructor"""
        threading.Thread.__init__(self)
        self.system_id = system_id

        self.start()

    def run(self):
        """The main body of the thread"""
        while not config.EXITING:
            cmd = subprocess.run(["sudo", "rdate", config.SITE_SETTINGS["NAS"]["IPAddress"]],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

            stdout = cmd.stdout.decode("UTF-8", errors="ignore")

            if cmd.returncode != 0:
                logger.error("Unable to sync system time with NAS box. Error was: "+str(stdout))
                print("Unable to sync system time with NAS box. Error was: "+str(stdout))

                #If this isn't Sump Pi, try to sync with Sump Pi instead.
                if self.system_id != "SUMP":
                    logger.error("Falling back to Sump Pi...")

                    cmd = subprocess.run(["sudo", "rdate",
                                          config.SITE_SETTINGS["SUMP"]["IPAddress"]],
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         check=False)

                    stdout = cmd.stdout.decode("UTF-8", errors="ignore")

                    if cmd.returncode != 0:
                        logger.error("Unable to sync system time with Sump Pi. Error was: "
                                     + str(stdout))

                        print("Unable to sync system time with Sump Pi. Error was: "
                              + str(stdout))

                        logger.error("Retrying time sync in 10 seconds...")
                        sleep = 10

                    else:
                        logger.error("Retrying time sync in 10 seconds...")
                        sleep = 10

                else:
                    logger.error("Retrying time sync in 10 seconds...")
                    sleep = 10

            else:
                logger.info("System time synchronised, now set to "+str(stdout))
                print("System time synchronised, now set to "+str(stdout))
                sleep = 86400

            #Respond to system shutdown quickly.
            count = 0

            while count < sleep and not config.EXITING:
                count += 1
                time.sleep(1)

class MonitorLoad(threading.Thread):
    """
    This class starts a thread that repeatedly monitors system load every 30
    seconds and logs this information in the log file.
    """

    def __init__(self):
        """The constructor"""
        threading.Thread.__init__(self)

        self.start()

    def run(self):
        """The main body of the thread"""
        #First time around, this returns a meaningless value, so discard it.
        psutil.cpu_percent()

        while not config.EXITING:
            try:
                cpu_percent = str(round(psutil.cpu_percent(), 2))
                used_memory_pct = str(psutil.virtual_memory().percent)

            except Exception:
                pass

            else:
                logger.info("\n\nCPU Usage: "+cpu_percent
                            + "\nMemory Usage: "+used_memory_pct
                            +"\n\n")

                print("\nCPU Usage: "+cpu_percent+"%"
                      + " Memory Usage: "+used_memory_pct+"%"
                      + "\n")

                #Save to global variables.
                config.CPU = cpu_percent
                config.MEM = used_memory_pct

            #Respond to system shutdown quickly.
            sleep = 30
            count = 0

            while count < sleep and not config.EXITING:
                count += 1
                time.sleep(1)

class DatabaseConnection(threading.Thread):
    """
    This class represents each pi's connection to the database. Only this thread talks
    directly to the DB server to prevent concurrent access. This also provides various
    convenience methods to avoid errors and make it easy to use the database.

    The methods that just send data to the database run asynchronously - the thread
    requesting the operation is not made to wait. Methods that return data will cause
    the calling thread to wait, though.

    Constructor documentation:

    Args:
        site_id (str).          The site ID of this pi.
    """

    def __init__(self, site_id):
        """The constructor"""
        threading.Thread.__init__(self)

        #Check this is a valid site ID.
        if not isinstance(site_id, str) or \
            site_id not in config.SITE_SETTINGS:

            raise ValueError("Invalid site ID: "+str(site_id))

        self.site_id = site_id

        #As the thread itself sets up the connection to the database, we need
        #a flag to show whether it's ready or not.
        self.is_connected = False
        self.init_done = False

        #A flag to show if the DB thread is running or not.
        self.is_running = False

        #Stop us filling up the event log with identical events and statuses.
        self.last_event = None
        self.last_pi_status = None
        self.last_sw_status = None
        self.last_current_action = None

        #We need a queue for the asynchronous database write operations.
        self.in_queue = deque()

        #We need a variable to hold results from fetch queries.
        self.result = None

        #We also need a flag for when we fetch data - we need to make sure the
        #other thread has got the data it needs before moving on to process
        #any other queries.
        self.client_thread_done = True

        #Used to store a reference to the DB thread so we can handle external
        #and internal queries to the database correctly.
        self.db_thread = None

        #We also need a lock, in case multiple clients try to fetch data
        #at the same time.
        self.client_lock = threading.RLock()

        config.DBCONNECTION = self

    def start_thread(self):
        """Called to start the database thread"""
        self.start()

    def run(self):
        """The main body of the thread"""
        self.db_thread = threading.current_thread()

        self.is_running = True

        #Setup to avoid errors.
        database = cursor = None
        count = 0

        #First we need to find our connection settings from the config file.
        user = config.SITE_SETTINGS[self.site_id]["DBUser"]
        passwd = config.SITE_SETTINGS[self.site_id]["DBPasswd"]
        host = config.SITE_SETTINGS[self.site_id]["DBHost"]
        port = config.SITE_SETTINGS[self.site_id]["DBPort"]

        while not config.EXITING:
            while not self.is_connected and not config.EXITING:
                #Attempt to connect to the database server.
                logger.info("DatabaseConnection: Attempting to connect to database...")

                if self.peer_alive():
                    database, cursor = self._connect(user, passwd, host, port)

                #Avoids duplicating the initialisation commands in the queue.
                if not self.is_connected:
                    print("Could not connect to database! Retrying...")
                    logger.error("DatabaseConnection: Could not connect! Retrying...")

                    #Set the query result to "Error" to stop excessive hangs when
                    #trying to execute queries when there is no connection.
                    self.result = "Error"

                    #Keep clearing the queue until we're reconnected as well.
                    self.in_queue.clear()

                    time.sleep(10)
                    continue

                #Otherwise, we are now connected.
                print("Connected to database.")
                logger.info("DatabaseConnection: Done!")
                self.is_connected = True

                #Clear old stuff out of the queue to prevent errors.
                self.in_queue.clear()
                self.result = None

            #If we're exiting, break out of the loop.
            #This prevents us from executing tons of queries at this point and delaying exit.
            if config.EXITING:
                continue

            #Check if peer is alive roughly every 60 seconds.
            if count > 60:
                count = 0

                if not self.peer_alive():
                    #We need to reconnect.
                    print("Database connection lost! Reconnecting...")
                    logger.error("DatabaseConnection: Connection lost! Reconnecting...")

                    #Drop the queries so we can try again or move on without deadlocking.
                    self.result = "Error"
                    self.in_queue.clear()

                    self.is_connected = False
                    self._cleanup(database, cursor)
                    continue

            #Do any requested operations on the queue.
            while self.in_queue:
                #Check for each query, because database.commit() does not have a
                #way of setting a reasonable timeout.
                if not self.peer_alive():
                    #We need to reconnect.
                    print("Database connection lost! Reconnecting...")
                    logger.error("DatabaseConnection: Connection lost! Reconnecting...")

                    #Drop the queries so we can try again or move on without deadlocking.
                    self.result = "Error"
                    self.in_queue.clear()

                    self.is_connected = False
                    self._cleanup(database, cursor)
                    break

                query = self.in_queue[0]

                try:
                    if "SELECT" not in query:
                        #Nothing to return, can do this the usual way.
                        logger.debug("DatabaseConnection: Executing query: "+query+"...")
                        self.client_thread_done = False

                        cursor.execute(query)
                        database.commit()

                        #If there's no error by this point, we succeeded.
                        self.result = "Success"

                        while not self.client_thread_done:
                            time.sleep(0.01)

                        #Make sure the result is cleared at this point.
                        self.result = None

                    else:
                        #We need to return data now, so we must be careful.
                        logger.debug("DatabaseConnection: Executing query: "+query
                                     + ", and returning data...")

                        self.client_thread_done = False

                        cursor.execute(query)
                        self.result = cursor.fetchall()

                        while not self.client_thread_done:
                            time.sleep(0.01)

                        #Make sure the result is cleared at this point.
                        self.result = None

                except mysql._exceptions.Error as error:
                    print("DatabaseConnection: Error executing query "+query+"! "
                          + "Error was: "+str(error))

                    logger.error("DatabaseConnection: Error executing query "+query+"! "
                                 + "Error was: "+str(error))

                    #Drop the query so we can try again or move on without deadlocking.
                    self.result = "Error"
                    self.in_queue.popleft()

                    while not self.client_thread_done:
                        time.sleep(0.01)

                    #Break out so we can check the connection again.
                    self.is_connected = False
                    self._cleanup(database, cursor)

                    break

                else:
                    logger.debug("DatabaseConnection: Done.")
                    self.in_queue.popleft()

            count += 1
            time.sleep(1)

        #Do clean up.
        self._cleanup(database, cursor)

        self.is_running = False

    #-------------------- PRIVATE SETUP METHODS -------------------
    def peer_alive(self):
        """
        Used to ping peer once at other end of the connection to check if it is still up.

        Used on first connection, and periodically so we know if a host goes down.

        Returns:
            boolean.        True = peer is online
                            False = peer is offline

        Usage:
            >>> <DatabaseConnection-Obj>.peer_alive()
            >>> True
        """
        try:
            #Ping the peer one time.
            subprocess.run(["ping", "-c", "1", "-W", "2",
                            config.SITE_SETTINGS[self.site_id]["DBHost"]],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)

            #If there was no error, this was fine.
            logger.debug("DatabaseConnection.peer_alive(): ("+self.name+"): Peer is up...")
            return True

        except subprocess.CalledProcessError:
            #Non-zero exit status.
            logger.warning("DatabaseConnection.peer_alive(): ("+self.name+"): Peer is down!")

            return False

    def _connect(self, user, passwd, host, port):
        """
        PRIVATE, implementation detail.

        Used to connect to the database.
        """

        if not isinstance(user, str) or \
            user == "":

            raise ValueError("Invalid username: "+str(user))

        if not isinstance(passwd, str) or \
            passwd == "":

            raise ValueError("Invalid password: "+str(passwd))

        #Check the IP address is valid (basic check).
        if not isinstance(host, str) or \
            len(host.split(".")) != 4 or \
            host == "0.0.0.0":

            raise ValueError("Invalid IPv4 address: "+str(host))

        #Advanced checks.
        #Check that each octet is a integer and between 0 and 255 (exclusive).
        for octet in host.split("."):
            if not octet.isdigit() or \
                int(octet) > 254 or \
                int(octet) < 0:

                raise ValueError("Invalid IPv4 address: "+str(host))

        #Check the port number is valid.
        if (not isinstance(port, int)) or \
            isinstance(port, bool) or \
            port <= 0 or \
            port > 65535:

            raise ValueError("Invalid port number: "+str(port))

        database = cursor = None

        try:
            database = mysql.connect(host=host, port=port, user=user, passwd=passwd,
                                     connect_timeout=30, db="rivercontrolsystem")

            cursor = database.cursor()


        except mysql._exceptions.Error as error:
            logger.error("DatabaseConnection: Failed to connect! Error was: "+str(error)
                         + "Retrying in 10 seconds...")

            self._cleanup(database, cursor)

            time.sleep(10)

        except Exception:
            logger.error("DatabaseConnection: Unexpected error while connecting: "+str(error)
                         + "Retrying in 10 seconds...")

            self._cleanup(database, cursor)

            time.sleep(10)

        else:
            #We are connected!
            self.is_connected = True

        return (database, cursor)

    def initialise_db(self):
        """
        Used to make sure that required records for this pi are present, and
        resets them if needed eg by clearing locks and setting initial status.
        """

        #It doesn't matter that these aren't done immediately - every query is done on
        #a first-come first-served basis.

        # -- NAS box: Repair system status and system tick tables in case of corruption --
        if self.site_id == "NAS":
            self.do_query("""REPAIR TABLE `SystemStatus`;""", 0)
            self.do_query("""REPAIR TABLE `SystemTick`;""", 0)

        #----- Remove and reset the status entry for this device, if it exists -----
        query = """DELETE FROM `SystemStatus` """ \
                + """ WHERE `System ID` = '"""+self.site_id+"""';"""

        self.do_query(query, 0)

        query = """INSERT INTO `SystemStatus`(`System ID`, `Pi Status`, """ \
                + """`Software Status`, `Current Action`) VALUES('"""+self.site_id \
                + """', 'Up', 'Initialising...', 'None');"""

        self.do_query(query, 0)

        #----- NAS box: Clear any locks we're holding and create control entries for devices -----
        if self.site_id == "NAS":
            for site_id in config.SITE_SETTINGS:
                #-- Repair all site-specific tables in case of corruption --
                self.do_query("""REPAIR TABLE `"""+site_id+"""Control`;""", 0)

                if site_id != "NAS":
                    self.do_query("""REPAIR TABLE `"""+site_id+"""Readings`;""", 0)

                query = """DELETE FROM `"""+site_id+"""Control`;"""

                self.do_query(query, 0)

                query = """INSERT INTO `"""+site_id+"""Control`(`Device ID`, """ \
                            + """`Device Status`, `Request`, `Locked By`) VALUES('""" \
                            + site_id+"""', 'Unlocked', 'None', 'None');"""

                self.do_query(query, 0)

                for device in config.SITE_SETTINGS[site_id]["Devices"]:
                    query = """INSERT INTO `"""+site_id+"""Control`(`Device ID`, """ \
                            + """`Device Status`, `Request`, `Locked By`) VALUES('""" \
                            + device.split(":")[1]+"""', 'Unlocked', 'None', 'None');"""

                    self.do_query(query, 0)

        self.init_done = True

    def _cleanup(self, database, cursor):
        """
        PRIVATE, implementation detail.

        Used to do clean up when connection is closed, or dies.
        """

        try:
            cursor.close()

        except Exception:
            pass

        try:
            database.close()

        except Exception:
            pass

    #-------------------- GETTER METHODS --------------------
    def is_ready(self):
        """
        This method returns True if the database is ready to use (connected), otherwise False.
        """

        return self.is_connected

    def initialised(self):
        """
        This method returns True if the database has been initialised, otherwise False.
        """

        return self.init_done

    def thread_running(self):
        """
        This method returns True if the database thread is running, otherwise False.
        """

        return self.is_running

    #-------------------- CONVENIENCE READER METHODS --------------------
    def do_query(self, query, retries):
        """
        This method executes the query with the specified number of retries.

        Args:
            query (str).            The query to execute.
            retries (int).          The number of retries.

        Returns:
            result (str).           The result.

        Throws:
            RuntimeError, if the query failed too many times, or if we aren't
            connected to the database.
        """

        if not self.is_connected:
            raise RuntimeError("Database not connected")

        count = 0

        while count <= retries and self.is_connected:
            if threading.current_thread() is not self.db_thread:
                #Acquire the lock for fetching data.
                self.client_lock.acquire()

            self.in_queue.append(query)

            #Wait until the query is processed.
            while self.result is None:
                time.sleep(0.01)

            #Store the results.
            result = self.result
            self.result = None

            #Signal that the database thread can safely continue.
            self.client_thread_done = True

            if threading.current_thread() is not self.db_thread:
                self.client_lock.release()

            #Keep trying until we succeed or we hit the maximum number of retries.
            if result == "Error":
                count += 1

            else:
                break

        #Throw RuntimeError if the query still failed.
        if result == "Error":
            raise RuntimeError("Query Failed")

        return result

    def get_latest_reading(self, site_id, sensor_id, retries=3):
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
        #NOTE: argument validation done in get_n_latest_readings.
        result = self.get_n_latest_readings(site_id, sensor_id, 1, retries)

        if result:
            return result[0]

        return None

    def get_n_latest_readings(self, site_id, sensor_id, number, retries=3):
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

        if not isinstance(site_id, str) or \
            site_id == "" or \
            site_id not in config.SITE_SETTINGS:

            raise ValueError("Invalid site ID: "+str(site_id))

        if not isinstance(sensor_id, str) or \
            sensor_id == "" or \
            (site_id+":"+sensor_id not in config.SITE_SETTINGS[site_id]["Devices"] and \
             site_id+":"+sensor_id not in config.SITE_SETTINGS[site_id]["Probes"]):

            raise ValueError("Invalid sensor ID: "+str(sensor_id))

        if not isinstance(number, int) or \
            number < 0 or \
            number == 0:

            raise ValueError("Invalid number of readings: "+str(number))

        query = """SELECT * FROM `"""+site_id+"""Readings` WHERE `Probe ID` = '"""+sensor_id \
                + """' ORDER BY ID DESC LIMIT 0, """+str(number)+""";"""

        result = self.do_query(query, retries)

        readings = []

        for reading_data in result:
            #Do some checks on each dataset before we use it.
            if len(reading_data) != 6 or \
                reading_data[1] != sensor_id:

                continue

            try:
                #Convert the result to a Reading object.
                readings.append(Reading(str(reading_data[3]), reading_data[2],
                                        site_id+":"+reading_data[1], reading_data[4],
                                        reading_data[5]))

            except (IndexError, TypeError, ValueError):
                #Values must be invalid. Ignore and deliver as many good readings as possible.
                pass

        return readings

    def get_state(self, site_id, sensor_id, retries=3):
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

        if not isinstance(site_id, str) or \
            site_id == "" or \
            site_id not in config.SITE_SETTINGS:

            raise ValueError("Invalid site ID: "+str(site_id))

        if not isinstance(sensor_id, str) or \
            sensor_id == "" or \
            (site_id+":"+sensor_id not in config.SITE_SETTINGS[site_id]["Devices"] and \
             site_id+":"+sensor_id not in config.SITE_SETTINGS[site_id]["Probes"] and \
             site_id != sensor_id):

            raise ValueError("Invalid sensor ID: "+str(sensor_id))

        query = """SELECT * FROM `"""+site_id+"""Control` WHERE `Device ID` = '""" \
                + sensor_id+"""' LIMIT 0, 1;"""

        result = self.do_query(query, retries)

        #Store the part of the results that we want.
        try:
            result = result[0][2:]

        except IndexError:
            result = None

        return result

    def get_status(self, site_id, retries=3):
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

        if not isinstance(site_id, str) or \
            site_id == "" or \
            site_id not in config.SITE_SETTINGS:

            raise ValueError("Invalid site ID: "+str(site_id))

        query = """SELECT * FROM `SystemStatus` WHERE `System ID` = '""" \
                + site_id+"""';"""

        result = self.do_query(query, retries)

        #Store the part of the results that we want.
        try:
            result = result[0][2:]

        except IndexError:
            result = None

        return result

    #-------------------- CONVENIENCE WRITER METHODS --------------------
    def attempt_to_control(self, site_id, sensor_id, request, retries=3):
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

        if not isinstance(site_id, str) or \
            site_id == "" or \
            site_id not in config.SITE_SETTINGS:

            raise ValueError("Invalid site ID: "+str(site_id))

        if not isinstance(sensor_id, str) or \
            sensor_id == "" or \
            (site_id+":"+sensor_id not in config.SITE_SETTINGS[site_id]["Devices"] and \
             site_id+":"+sensor_id not in config.SITE_SETTINGS[site_id]["Probes"] and \
             site_id != sensor_id):

            raise ValueError("Invalid sensor ID: "+str(sensor_id))

        if not isinstance(request, str) or \
            (sensor_id == site_id and \
             request not in ("Manual", "Update", "Reboot", "Shutdown")):

            raise ValueError("Invalid request: "+str(request))

        state = self.get_state(site_id, sensor_id)

        #If it's locked and we didn't lock it, return False.
        if state is None or \
            (state[0] == "Locked" and \
             state[2] != self.site_id):

            return False

        #If everything is already as we want it then don't do anything but return True.
        if state[0] == "Locked" and state[1] == request and \
            state[2] == self.site_id:

            return True

        #Otherwise we may now take control.
        query = """UPDATE `"""+site_id+"""Control` SET `Device Status` = 'Locked', """ \
                + """`Request` = '"""+request+"""', `Locked By` = '"""+self.site_id \
                + """' WHERE `Device ID` = '"""+sensor_id+"""';"""

        self.do_query(query, retries)

        #Log the event as well.
        self.log_event("Taking control of "+site_id+":"+sensor_id
                       + ", Request: "+request)

        return True

    def release_control(self, site_id, sensor_id, retries=3):
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

        if not isinstance(site_id, str) or \
            site_id == "" or \
            site_id not in config.SITE_SETTINGS:

            raise ValueError("Invalid site ID: "+str(site_id))

        if not isinstance(sensor_id, str) or \
            sensor_id == "" or \
            (site_id+":"+sensor_id not in config.SITE_SETTINGS[site_id]["Devices"] and \
             site_id+":"+sensor_id not in config.SITE_SETTINGS[site_id]["Probes"] and \
             site_id != sensor_id):

            raise ValueError("Invalid sensor ID: "+str(sensor_id))

        state = self.get_state(site_id, sensor_id)

        #If it isn't locked, or we didn't lock it, return.
        if state is None or \
            state[0] == "Unlocked" or \
            state[2] != self.site_id:

            return

        #Otherwise unlock it.
        query = """UPDATE `"""+site_id+"""Control` SET `Device Status` = 'Unlocked', """ \
                + """`Request` = 'None', `Locked By` = 'None' WHERE `Device ID` = '""" \
                + sensor_id+"""';"""

        self.do_query(query, retries)

        #Log the event as well.
        self.log_event("Releasing control of "+site_id+":"+sensor_id)

    def log_event(self, event, severity="INFO", retries=3):
        """
        This method logs the given event message in the database.

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

        if not isinstance(event, str) or \
            event == "":

            raise ValueError("Invalid event message: "+str(event))

        if not isinstance(severity, str) or \
            event == "":

            raise ValueError("Invalid severity: "+str(severity))

        #Ignore if this event is exactly the same as the last one.
        if event == self.last_event:
            return

        self.last_event = event

        query = """INSERT INTO `EventLog`(`Site ID`, `Severity`, `Event`, `Device Time`)""" \
                + """VALUES('"""+self.site_id+"""', '"""+severity+"""', '"""+event \
                + """', '"""+str(datetime.datetime.now())+"""');"""

        self.do_query(query, retries)

    def update_status(self, pi_status, sw_status, current_action, retries=3):
        """
        This method logs the given statuses and action(s) in the database.

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

        if not isinstance(pi_status, str) or \
            pi_status == "":

            raise ValueError("Invalid Pi Status: "+str(pi_status))

        if not isinstance(sw_status, str) or \
            sw_status == "":

            raise ValueError("Invalid Software Status: "+str(sw_status))

        if not isinstance(current_action, str) or \
            current_action == "":

            raise ValueError("Invalid Current Action: "+str(current_action))

        #Ignore if this status is exactly the same as the last one.
        if pi_status == self.last_pi_status and sw_status == self.last_sw_status \
            and current_action == self.last_current_action:

            return

        self.last_pi_status = pi_status
        self.last_sw_status = sw_status
        self.last_current_action = current_action

        query = """UPDATE SystemStatus SET `Pi Status` = '"""+pi_status \
                + """', `Software Status` = '"""+sw_status \
                + """', `Current Action` =  '"""+current_action \
                + """' WHERE `SYSTEM ID` = '"""+self.site_id+"""';"""

        self.do_query(query, retries)

        self.log_event("Updated status")

    def get_latest_tick(self, retries=3):
        """
        This method gets the latest tick from the database. Used to restore
        the system tick on NAS bootup.

        .. warning::
                This is only meant to be run from the NAS box. The pis
                get the ticks over the socket - this is a much less
                efficient way to deliver system ticks, but is needed
                on NAS box startup.

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

        if config.SYSTEM_ID != "NAS":
            return None

        query = """SELECT * FROM `SystemTick` ORDER BY `ID` DESC """ \
                + """LIMIT 0, 1;"""

        result = self.do_query(query, retries)

        #Store the part of the results that we want (only the tick).
        try:
            result = result[0][1]

        except IndexError:
            result = None

        return result

    def store_tick(self, tick, retries=3):
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

        if config.SYSTEM_ID != "NAS":
            return

        if not isinstance(tick, int):
            raise ValueError("Invalid system tick: "+str(tick))

        query = """INSERT INTO `SystemTick`(`Tick`, `System Time`) """ \
                + """VALUES('"""+str(tick)+"""', NOW());"""

        self.do_query(query, retries)

    def store_reading(self, reading, retries=3):
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

        if not isinstance(reading, Reading):
            raise ValueError("Invalid reading object: "+str(reading))

        query = """INSERT INTO `"""+self.site_id+"""Readings`(`Probe ID`, `Tick`, """ \
                + """`Measure Time`, `Value`, `Status`) VALUES('"""+reading.get_sensor_id() \
                + """', """+str(reading.get_tick())+""", '"""+reading.get_time()+"""', '""" \
                + reading.get_value()+"""', '"""+reading.get_status()+"""');"""

        self.do_query(query, retries)

# -------------------- CONTROL LOGIC FUNCTIONS AND CLASSES --------------------
#NB: Moved to /Logic/controllogic.py

# -------------------- MISCELLANEOUS FUNCTIONS --------------------
def setup_sockets(system_id):
    """
    This function is used to set up the sockets for each site.

    Args:
        system_id (str):              The system that we're setting up for.

    Returns:
        tuple(A list of the sockets that were set up, the local socket for this site).

    Usage:
        >>> sockets, local_socket = setup_sockets("G4")

    """
    #Create all sockets.
    logger.info("Creating sockets...")
    sockets = {}

    if config.SITE_SETTINGS[system_id]["HostingSockets"]:
        #We are a server, and we are hosting sockets.
        #Use info ation from the other sites to figure out what sockets to create.
        for site in config.SITE_SETTINGS:
            site_settings = config.SITE_SETTINGS[site]

            #If no server is defined for this site, skip it.
            if "SocketName" not in site_settings:
                continue

            socket = sockettools.Sockets("Socket", system_id, site_settings["SocketName"])
            socket.set_portnumber(site_settings["ServerPort"])
            socket.set_server_address(site_settings["IPAddress"])
            sockets[site_settings["SocketID"]] = socket

            socket.start_handler()

    #If a server is defined for this pi, connect to it.
    if "SocketName" in config.SITE_SETTINGS[system_id]:
        #Connect to the server.
        socket = sockettools.Sockets("Plug", system_id,
                                      config.SITE_SETTINGS[system_id]["ServerName"])

        socket.set_portnumber(config.SITE_SETTINGS[system_id]["ServerPort"])
        socket.set_server_address(config.SITE_SETTINGS[system_id]["ServerAddress"])
        socket.start_handler()

        sockets[config.SITE_SETTINGS[system_id]["SocketID"]] = socket

        local_socket = socket

    logger.debug("Done!")

    return sockets, local_socket

def setup_devices(system_id, dictionary="Probes"):
    """
    This function is used to set up the device objects for each site.

    Args:
        system_id (str):              The system that we're setting up for.

    KWargs:
        dictionary (str):             The dictionary in config.py to set up for.
                                      If not specified, default is "Probes".

    Returns:
        A list of the device objects that were set up.

    Usage:
        >>> setup_devices("G4")

    """
    devices = []

    for device_id in config.SITE_SETTINGS[system_id][dictionary]:
        device_settings = config.SITE_SETTINGS[system_id][dictionary][device_id]

        device_name = device_settings["Name"]
        _type = device_settings["Type"]
        device = device_settings["Class"]

        device = device(device_id, device_name)

        if _type == "Hall Effect Probe":
            device.set_address(device_settings["ADCAddress"])
            device.set_limits(device_settings["HighLimits"], device_settings["LowLimits"])
            device.set_depths([device_settings["Depths100s"], device_settings["Depths25s"],
                               device_settings["Depths50s"], device_settings["Depths75s"]])

            device.start_thread()

        elif _type == "Motor":
            #The pins are outputs for Motors.
            device.set_pins(device_settings["Pins"], _input=False)

            #If this is sump pi and the circulation pump, turn it on.
            if system_id == "SUMP" and device_id == "SUMP:P1":
                print("Enabling circulation pump to avoid overflow while waiting for NAS box...")
                device.enable()

            else:
                #Immediately disable the motor, as they can turn on during
                #startup, if state is not initialised.
                device.disable()

        elif _type == "Gate Valve":
            device.set_pins(device_settings["Pins"])
            device.set_pos_tolerance(device_settings["posTolerance"])
            device.set_max_open(device_settings["maxOpen"])
            device.set_min_open(device_settings["minOpen"])
            device.set_ref_voltage(device_settings["refVoltage"])
            device.set_i2c_address(device_settings["ADCAddress"])

            device.start_thread()

        else:
            pins = device_settings["Pins"]
            device.set_pins(pins)

        devices.append(device)

    return devices

def get_and_handle_new_reading(monitor, _type):
    """
    This function is used to get, handle, and return new readings from the
    monitors. It checks each monitor to see if there is data, then prints
    and logs it if needed.

    Args:
        monitor (BaseMonitorClass):     The monitor we're checking.
        _type (str):                    The type of probe we're monitoring.

    Returns:
        A Reading object.

    Usage:

        >>> get_and_handle_new_reading(<BaseMonitorClass-Obj>, "test")
    """

    reading = None

    while monitor.has_data():
        last_reading = monitor.get_previous_reading()

        reading = monitor.get_reading()

        #Check if the reading is different to the last reading.
        if reading == last_reading:
            #Write a . to each file.
            logger.info(".")
            print(".", end='') #Disable newline when printing this message.

        else:
            #Write any new readings to the file and to stdout.
            logger.info(str(reading))

            print(reading)

        #Flush buffers.
        sys.stdout.flush()

    return reading
