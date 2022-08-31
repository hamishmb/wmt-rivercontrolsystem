#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Database Tools for the River System Control and Monitoring Software
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
This is the dbtools module, which contains database-related functionality.

.. module:: dbtools.py
    :platform: Linux
    :synopsis: Contains database-related tools and functionality.

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

#Import modules.
sys.path.insert(0, os.path.abspath('..'))

import config

from Tools import coretools
from Tools.coretools import rcs_print as print #pylint: disable=redefined-builtin

#Don't ask for a logger name, so this works with both main.py
#and the universal monitor.
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
                    print("Could not connect to database! Retrying...", level="error")
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
                    print("Database connection lost! Reconnecting...", level="error")
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
                    print("Database connection lost! Reconnecting...", level="error")
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
                          + "Error was: "+str(error), level="error")

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

        Named args:
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
            >>> 'Reading at time 2020-09-30 12:01:12.227565, and tick 0, from probe: \
            >>> G4:M0, with value: 350, and status: OK'

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

        Named args:
            retries[=3] (int).        The number of times to retry before giving up
                                      and raising an error.

        Returns:
            List of (Reading objects).       The latest readings for that sensor at that site.

        Throws:
            RuntimeError, if the query failed too many times.

        Usage example:
            >>> get_latest_reading("G4", "M0")
            >>> 'Reading at time 2020-09-30 12:01:12.227565, and tick 0, from probe: \
            >>> G4:M0, with value: 350, and status: OK'

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
                readings.append(coretools.Reading(str(reading_data[3]), reading_data[2],
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

        Named args:
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

        Named args:
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

        Named args:
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

        Named args:
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

        Named args:
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

        Named args:
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
                on NAS box startup. This is a do-nothing method on all
                devices except the NAS box.

        Named args:
            retries[=3] (int).          The number of times to retry before giving up
                                        and raising an error.

        Throws:
            RuntimeError, if the query failed too many times.

        Returns:
            int. The latest system tick.

        Usage:
            >>> tick = get_latest_tick()
        """

        if config.SITE_ID != "NAS":
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

        Named args:
            retries[=3] (int).          The number of times to retry before giving up
                                        and raising an error.

        Throws:
            RuntimeError, if the query failed too many times.

        Usage:
            >>> store_tick(<int>)
            >>>
        """

        if config.SITE_ID != "NAS":
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

        Named args:
            retries[=3] (int).          The number of times to retry before giving up
                                        and raising an error.

        Throws:
            RuntimeError, if the query failed too many times.

        Usage:
            >>> store_reading(<Reading-Obj>)
            >>>
        """

        if not isinstance(reading, coretools.Reading):
            raise ValueError("Invalid reading object: "+str(reading))

        query = """INSERT INTO `"""+self.site_id+"""Readings`(`Probe ID`, `Tick`, """ \
                + """`Measure Time`, `Value`, `Status`) VALUES('"""+reading.get_sensor_id() \
                + """', """+str(reading.get_tick())+""", '"""+reading.get_time()+"""', '""" \
                + reading.get_value()+"""', '"""+reading.get_status()+"""');"""

        self.do_query(query, retries)

    #----- CONTROL METHODS -----
    def wait_exit(self):
        """
        This method is used to wait for the database thread to exit.

        This isn't a mandatory function as the database thread will shut down
        automatically when config.EXITING is set to True.

        Usage:
            >>> <DatabaseConnection>.wait_exit()
        """

        while self.is_running:
            time.sleep(0.5)
