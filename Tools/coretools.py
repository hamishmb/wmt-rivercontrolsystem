#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Core Tools for the River System Control and Monitoring Software
# Copyright (C) 2017-2019 Wimborne Model Town
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
This is the coretools module, which contains tools used by both
the main control software, and the universal monitor. It's kind
superflous at the moment, but I will probably move some more
functions in here to reduce code duplication.

.. module:: coretools.py
    :platform: Linux
    :synopsis: Contains tools used by all parts of the software.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>
"""

import sys
import time
import threading
import subprocess
import logging
from collections import deque
#import MySQLdb as mysql
import psutil

import config

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
                                    depending on probe type at the moment **FIXME**.
                                    Ideally, these would all be values in mm like:
                                    400 mm.

        reading_status (String):    The status of the probe at the time the reading
                                    was taken. If there is no fault, this should be
                                    "OK". Otherwise, it should be "FAULT DETECTED: "
                                    followed by some sensor-dependant information
                                    about the fault.

    Usage:
        The constructor for this class takes four arguments as specified above.

        >>> my_reading = core_tools.Reading(<a_time>, <a_tick>, <an_id>, <a_value>, <a_status>)

    .. warning::
        There is currently **absolutely no** check to see that each instance variable
        actually has the correct format. This will come later.

    .. warning::
        System ticks have not yet been implemented. As such the value
        for the tick passed here to the constructor is ignored, and
        the attribute is set to -1.

    .. note::
        Equality methods have been implemented for this class so you can do things like:

        >>> reading_1 == reading_2

        AND:

        >>> reading_2 != reading_3

        With ease.
    """

    # ---------- CONSTRUCTORS ----------
    def __init__(self, reading_time, reading_tick, reading_id, reading_value, reading_status):
        """This is the constructor as defined above"""
        #Set some semi-private variables.
        #Check the time is a string.
        #TODO Check that the time string is valid as well.
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

        except:
            return False

    def __ne__(self, other):
        """
        This method is used to compare objects of type Reading.

        It simple does the same as the __eq__ method and then uses a
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
    """

    def __init__(self):
        """The constructor"""
        threading.Thread.__init__(self)

        self.start()

    def run(self):
        """The main body of the thread"""
        while not config.EXITING:
            cmd = subprocess.run(["sudo", "rdate", config.SITE_SETTINGS["SUMP"]["IPAddress"]],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            stdout = cmd.stdout.decode("UTF-8", errors="ignore")

            if cmd.returncode != 0:
                logger.error("Unable to sync system time. Error was: "+str(stdout))
                print("Unable to sync system time. Error was: "+str(stdout))
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
                cpu_percent = psutil.cpu_percent()
                used_memory_mb = (psutil.virtual_memory().used // 1024 // 1024)

            except Exception:
                pass

            else:
                logger.info("\n\nCPU Usage: "+str(cpu_percent)
                            + "\nMemory Used (MB): "+str(used_memory_mb)
                            +"\n\n")

                print("\n\nCPU Usage: "+str(cpu_percent)
                      + "\nMemory Used (MB): "+str(used_memory_mb)
                      + "\n\n")

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
    """

    #TODO Argument validation for remaining methods.
    #TODO Logging, especially debug logging.
    #TODO Error handling and connection error detection.
    # ^ Has been written to some extent, but not tested thoroughly.

    def __init__(self, site_id):
        """The constructor"""
        threading.Thread.__init__(self)

        #Check this is a valid site ID.
        if not isinstance(site_id, str) or \
            site_id not in config.SITE_SETTINGS:

            raise ValueError("Invalid site ID: "+str(site_id))

        self.site_id = site_id
        self.pi_name = config.SITE_SETTINGS[site_id]["Name"]

        #As the thread itself sets up the connection to the database, we need
        #a flag to show whether it's ready or not.
        self.is_connected = False

        #A flag to show if the DB thread is running or not.
        self.is_running = False

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

    def start_thread(self):
        """Called to start the database thread"""
        self.start()

    def run(self):
        """The main body of the thread"""
        self.db_thread = threading.current_thread()

        self.is_running = True

        #Setup to avoid errors.
        database = cursor = None

        #First we need to find our connection settings from the config file.
        user = config.SITE_SETTINGS[self.site_id]["DBUser"]
        passwd = config.SITE_SETTINGS[self.site_id]["DBPasswd"]
        host = config.SITE_SETTINGS[self.site_id]["DBHost"]
        port = config.SITE_SETTINGS[self.site_id]["DBPort"]

        while not config.EXITING:
            while not self.is_connected and not config.EXITING:
                #Attempt to connect to the database server.
                logger.info("DatabaseConnection: Attempting to connect to database...")

                database, cursor = self._connect(user, passwd, host, port)

                #Avoids duplicating the initialisation commands in the queue.
                if not self.is_connected:
                    continue

                #Initialise the database.
                self._initialise_db()

            #If we're exiting, break out of the loop.
            if config.EXITING:
                continue

            #We are now connected.
            self.is_connected = True
            config.DBCONNECTION = self

            #Do any requested operations on the queue.
            while self.in_queue:
                query = self.in_queue[0]

                try:
                    if "SELECT" not in query:
                        #Nothing to return, can do this the usual way.
                        cursor.execute(query)
                        database.commit()

                    else:
                        #We need to return data now, so we must be careful.
                        self.client_thread_done = False

                        cursor.execute(query)
                        self.result = cursor.fetchall()

                        while not self.client_thread_done:
                            time.sleep(0.01)

                except mysql._exceptions.Error as error:
                    logger.error("DatabaseConnection: Error executing query "+query+"! "
                                 + "Error was: "+str(error))

                    #Break out so we can check the connection again.
                    #TODO Need to check that this works, and handles only the errors
                    #we want it to handle.
                    #TODO How to handle if a query fails, rather than if the database is
                    #offline?
                    config.DBCONNECTION = None

                    break

                else:
                    self.in_queue.popleft()

            time.sleep(1)

        #Do clean up.
        self._cleanup(database, cursor)

        self.is_running = False

    #-------------------- PRIVATE SETUP METHODS -------------------
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
                                     connect_timeout=10, db="rivercontrolsystem")

            cursor = database.cursor()


        except mysql._exceptions.Error as error:
            logger.error("DatabaseConnection: Failed to connect! Error was: "+str(error)
                         + "Retrying in 10 seconds...")

            self._cleanup(database, cursor)

            time.sleep(10)

        else:
            #We are connected!
            self.is_connected = True

        return (database, cursor)

    def _initialise_db(self):
        """
        PRIVATE, implementation detail.

        Used to make sure that required records for this pi are present, and
        resets them if needed eg by clearing locks and setting initial status.
        """

        #It doesn't matter that these aren't done immediately - every query is done on
        #a first-come first-served basis.

        #----- Remove and reset the status entry for this pi, if it exists -----
        query = """DELETE FROM `SystemStatus` """ \
                + """ WHERE `Pi Name` = '"""+self.pi_name+"""';"""

        self.in_queue.append(query)

        query = """INSERT INTO `SystemStatus`(`Pi Name`, `Pi Status`, """ \
                + """`Software Status`, `Current Action`) VALUES('"""+self.pi_name \
                + """', 'Up', 'Initialising...', 'None');"""

        self.in_queue.append(query)

        #----- Clear any locks we're holding and create control entries for devices -----
        #TODO should be done on NAS box only, this isn't safe in case another pi is
        #controlling something and this one just rebooted!
        query = """DELETE FROM `"""+self.site_id+"""Control;"""

        self.in_queue.append(query)

        for device in config.SITE_SETTINGS[self.site_id]["Devices"]:
            query = """INSERT INTO `"""+self.site_id+"""Control`(`Device ID`, """ \
                    + """`Device Status`, `Request`, `Locked By`) VALUES('""" \
                    + device.split(":")[1]+"""', 'Unlocked', 'None', 'None');"""

            self.in_queue.append(query)

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
        This method returns True if the database is ready to use, otherwise False.
        """

        return self.is_connected

    def thread_running(self):
        """
        This method returns True if the database thread is running, otherwise False.
        """

        return self.is_running

    #-------------------- CONVENIENCE READER METHODS --------------------
    def get_latest_reading(self, site_id, sensor_id):
        """
        This method returns the latest reading for the given sensor at the given site.

        Args:
            site_id.            The site we want the reading from.
            sensor_id.          The sensor we want the reading for.

        Returns:
            A Reading object.       The latest reading for that sensor at that site.

            OR

            None.                   There is no reading available to return.

        Usage example:
            >>> get_latest_reading("G4", "M0")
            >>> 'Reading at time 2019-09-30 12:01:12.227565, and tick 0, from probe: G4:M0, with value: 350, and status: OK'

        """

        result = self.get_n_latest_readings(site_id, sensor_id, 1)

        if result != []:
            return result[0]

        else:
            return None

    def get_n_latest_readings(self, site_id, sensor_id, number):
        """
        This method returns last n readings for the given sensor at the given site.
        If the list is empty, or contains fewer readings than was asked for, this
        means there aren't enough readings to return all of them.

        Args:
            site_id.            The site we want the reading from.
            sensor_id.          The sensor we want the reading for.
            number.             The number of readings.

        Returns:
            List of (Reading objects).       The latest readings for that sensor at that site.

        Usage example:
            >>> get_latest_reading("G4", "M0")
            >>> 'Reading at time 2019-09-30 12:01:12.227565, and tick 0, from probe: G4:M0, with value: 350, and status: OK'

        """

        query = """SELECT * FROM `"""+site_id+"""Readings` WHERE `Probe ID` = '"""+sensor_id \
                + """' ORDER BY ID DESC LIMIT 0, """+str(number)+""";"""

        if threading.current_thread() is not self.db_thread:
            #Acquire the lock for fetching data.
            self.client_lock.acquire()

        self.in_queue.append(query)

        #Wait until the query is processed.
        #TODO Could cause a deadlock if a prev query keeps failing!
        while self.result is None:
            time.sleep(0.01)

        #Store the results.
        result = self.result
        self.result = None

        #Signal that the database thread can safely continue.
        self.client_thread_done = True

        if threading.current_thread() is not self.db_thread:
            self.client_lock.release()

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

    def get_state(self, site_id, sensor_id):
        """
        This method queries the state of the given sensor/device. Information is returned
        such as what (if anything) has been requested, if it is Locked or Unlocked,
        and which pi locked it, if any.

        Args:
            site_id.            The site that holds the device we're interested in.
            sensor_id.          The sensor we want to know about.

        Returns:
            tuple.      1st element:        Device status (str) ("Locked" or "Unlocked").
                        2nd element:        Request (str) (values depend on device).
                        3rd element:        Locked by (str) (site id as defined in config.py).

            OR

            None.           No data available.

        Usage:
            >>> get_state("V4", "V4")
            >>> ("Locked", "50%", "SUMP")

        """
        query = """SELECT * FROM `"""+site_id+"""Control` WHERE `Device ID` = '""" \
                + sensor_id+"""' LIMIT 0, 1;"""

        if threading.current_thread() is not self.db_thread:
            #Acquire the client thread lock for fetching data.
            self.client_lock.acquire()

        self.in_queue.append(query)

        #Wait until the query is processed.
        #TODO Could cause a deadlock if a prev query keeps failing!
        while self.result is None:
            time.sleep(0.01)

        #Store the results.
        try:
            result = self.result[0][2:]

        except IndexError:
            result = None

        self.result = None

        #Signal that the database thread can safely continue.
        self.client_thread_done = True

        if threading.current_thread() is not self.db_thread:
            self.client_lock.release()

        return result

    #-------------------- CONVENIENCE WRITER METHODS --------------------
    def attempt_to_control(self, site_id, sensor_id, request):
        """
        This method attempts to lock the given sensor/device so we can take control.
        First we check if the device is locked. If it isn't locked, or this pi locked it,
        then we take control and note the requested action, and True is returned.

        Otherwise, we don't take control, and False is returned.

        Args:
            site_id.            The site that holds the device we're interested in.
            sensor_id.          The sensor we want to know about.
            request (str).      What state we want the device to be in.

        Returns:
            boolean.        True - We are now in control of the device.
                            False - The device is locked and in use by another pi.

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
             not "V" in site_id):

            raise ValueError("Invalid sensor ID: "+str(sensor_id))

        if not isinstance(request, str) or \
            request == "":

            raise ValueError("Invalid request: "+str(request))

        state = self.get_state(site_id, sensor_id)

        #If it's locked and we didn't lock it, return False.
        if state is None or \
            (state[0] == "Locked" and \
             state[2] != self.site_id):

            return False

        #Otherwise we may now take control.
        query = """UPDATE `"""+site_id+"""Control` SET `Device Status` = 'Locked', """ \
                + """`Request` = '"""+request+"""', `Locked By` = '"""+self.site_id \
                + """' WHERE `Device ID` = '"""+sensor_id+"""';"""

        self.in_queue.append(query)

        #Log the event as well.
        self.log_event("Taking control of "+site_id+":"+sensor_id
                       + ", Request: "+request)

        return True

    def release_control(self, site_id, sensor_id):
        """
        This method attempts to release the given sensor/device so other pis can
        take control. First we check if we locked the device. If it isn't locked,
        or this pi didn't lock it, we return without doing anything.

        Otherwise, we unlock the device.

        Args:
            site_id.            The site that holds the device we're interested in.
            sensor_id.          The sensor we want to know about.

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
             not "V" in site_id) or \
             ("V" in site_id and site_id != sensor_id):

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

        self.in_queue.append(query)

        #Log the event as well.
        self.log_event("Releasing control of "+site_id+":"+sensor_id)

    def log_event(self, event):
        """
        This method logs the given event message in the database.

        Args:
            event (str).            The event to log.

        Usage:
            >>> log_event("test")
            >>>
        """

        if not isinstance(event, str) or \
            event == "":

            raise ValueError("Invalid event message: "+str(event))

        query = """INSERT INTO `EventLog`(`Site ID`, `Event`, `Time`) VALUES('"""+self.site_id \
                +"""', '"""+event+"""', NOW());"""

        self.in_queue.append(query)

    def update_status(self, pi_status, sw_status, current_action):
        """
        This method logs the given statuses and action(s) in the database.

        Args:
            pi_status (str).            The current status of this pi.
            sw_status (str).            The current status of the software on this pi.
            current_action (str).       The software's current action(s).

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

        query = """UPDATE SystemStatus SET `Pi Status` = '"""+pi_status \
                + """', `Software Status` = '"""+sw_status \
                + """', `Current Action` =  '"""+current_action \
                + """' WHERE `Pi Name` = '"""+self.pi_name+"""';"""

        self.in_queue.append(query)

        self.log_event("Updated status")

    def store_reading(self, reading):
        """
        This method stores the given reading in the database.

        Args:
            reading (Reading). The reading to store.

        Usage:
            >>> store_reading(<Reading-Obj>)
            >>>
        """

        if not isinstance(reading, Reading):
            raise ValueError("Invalid reading object: "+str(reading))

        query = """INSERT INTO `"""+self.site_id+"""Readings`(`Probe ID`, `Tick`, """ \
                + """`Time`, `Value`, `Status`) VALUES('"""+reading.get_sensor_id() \
                + """', """+str(reading.get_tick())+""", '"""+reading.get_time()+"""', '""" \
                + reading.get_value()+"""', '"""+reading.get_status()+"""');"""

        self.in_queue.append(query)

# -------------------- CONTROL LOGIC FUNCTIONS --------------------
def sumppi_control_logic(readings, devices, monitors, sockets, reading_interval):
    """
    This function is used to decides what action to take based
    on the readings it is passed.

    The butts pump is turned on when the sump level >= 600 mm, and
    turned off when it reaches 400 mm. The circulation pump is
    turned on when the sump level >= 300, and otherwise the
    circulation pump will be turned off.

    The reading intervals at both the sumppi and the buttspi end
    are controlled and set here as well.

    .. note::
        Just added support for SSR 2 (circulation pump).

    Otherwise, nothing currently happens because there is nothing
    else we can take control of at the moment.

    Args:
        readings (list):                A list of the latest readings for each probe/device.

        devices  (list):                A list of all master pi device objects.

        monitors (list):                A list of all master pi monitor objects.

        sockets (list of Socket):       A list of Socket objects that represent
                                        the data connections between pis. Passed
                                        here so we can control the reading
                                        interval at that end.

        reading_interval (int):     The current reading interval, in
                                    seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = sumppi_control_logic(<listofreadings>,
        >>>                                         <listofprobes>, <listofmonitors>,
        >>>                                         <listofsockets>, <areadinginterval)

    """

    #Remove the 'mm' from the end of the reading value and convert to int.
    sump_reading = int(readings["SUMP:M0"].get_value().replace("m", ""))
    butts_reading = int(readings["G4:M0"].get_value().replace("m", ""))
    butts_float_reading = readings["G4:FS0"]

    #Get a reference to both pumps.
    main_pump = None
    butts_pump = None

    for device in devices:
        if device.get_id() == "SUMP:P0":
            butts_pump = device

        elif device.get_id() == "SUMP:P1":
            main_pump = device

    #Check that we got references to both pumps.
    assert main_pump is not None
    assert butts_pump is not None

    #Check that the devices list is not empty.
    assert devices

    #Check that the sockets list is not empty.
    assert sockets

    #Check that the reading interval is positive, and greater than 0.
    assert reading_interval > 0

    #Check that the butts float switch reading is sane.
    assert butts_float_reading.get_value() in ("True", "False")

    if sump_reading >= 600:
        #Level in the sump is getting high.
        logger.warning("Water level in the sump ("+str(sump_reading)+") >= 600 mm!")
        print("Water level in the sump ("+str(sump_reading)+") >= 600 mm!")

        #Make sure the main circulation pump is on.
        logger.info("Turning the main circulation pump on, if it was off...")
        print("Turning the main circulation pump on, if it was off...")

        #Close the wendy butts gate valve.
        logger.info("Closing the wendy butts gate valve...")
        print("Closing the wendy butts gate valve...")
        sockets["SOCK14"].write("Valve Position 0")

        main_pump.enable()

        #Pump some water to the butts if they aren't full.
        #If they are full, do nothing and let the sump overflow.
        if butts_float_reading.get_value() == "False":
            #Pump to the butts.
            logger.warning("Pumping water to the butts...")
            print("Pumping water to the butts...")
            butts_pump.enable()

            logger.warning("Changing reading interval to 30 seconds so we can "
                           +"keep a close eye on what's happening...")

            print("Changing reading interval to 30 seconds so we can keep a "
                  +"close eye on what's happening...")

            reading_interval = 30

        else:
            #Butts are full. Do nothing, but warn user.
            butts_pump.disable()

            logger.warning("The water butts are full. Allowing the sump to overflow.")
            print("The water butts are full.")
            print("Allowing the sump to overflow.")

            logger.warning("Setting reading interval to 1 minute...")
            print("Setting reading interval to 1 minute...")
            reading_interval = 60

    elif sump_reading >= 500 and sump_reading <= 600:
        #Level is okay.
        #We might be pumping right now, or the level is increasing, but do nothing.
        #^ Do NOT change the state of the butts pump.
        logger.info("Water level in the sump is between 500 and 600 mm.")
        print("Water level in the sump is between 500 and 600 mm.")

        #Make sure the main circulation pump is on.
        logger.info("Turning the main circulation pump on, if it was off...")
        print("Turning the main circulation pump on, if it was off...")

        #Close gate valve.
        logger.info("Closing wendy butts gate valve...")
        print("Closing wendy butts gate valve...")
        sockets["SOCK14"].write("Valve Position 0")

        main_pump.enable()

    elif sump_reading >= 400 and sump_reading <= 500:
        #Level in the sump is good.
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        logger.info("Water level in the sump is between 400 and 500 mm. "
                    + "Turned the butts pump off, if it was on.")

        print("Water level in the sump is between 400 and 500 mm. "
              + "Turned the butts pump off, if it was on.")

        #Make sure the main circulation pump is on.
        logger.info("Turning the main circulation pump on, if it was off...")
        print("Turning the main circulation pump on, if it was off...")

        #Close gate valve.
        logger.info("Closing wendy butts gate valve...")
        print("Closing wendy butts gate valve...")
        sockets["SOCK14"].write("Valve Position 0")

        main_pump.enable()

        logger.info("Setting reading interval to 1 minute...")
        print("Setting reading interval to 1 minute...")
        reading_interval = 60

    elif sump_reading >= 300 and sump_reading <= 400:
        #Level in the sump is getting low.
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        logger.warning("Water level in the sump is between 300 and 400 mm!")
        logger.warning("Opening wendy butts gate valve to 25%...")

        print("Water level in the sump is between 300 and 400 mm!")

        if butts_reading >= 300:
            logger.info("Opening wendy butts gate valve to 25%...")
            print("Opening wendy butts gate valve to 25%...")
            sockets["SOCK14"].write("Valve Position 25")

        else:
            logger.warning("Insufficient water in wendy butts...")
            print("Insufficient water in wendy butts...")
            sockets["SOCK14"].write("Valve Position 0")

        #Make sure the main circulation pump is on.
        logger.info("Turning the main cirulation pump on, if it was off...")
        print("Turning the main circulation pump on, if it was off...")

        main_pump.enable()

        logger.warning("Setting reading interval to 1 minute so we can monitor more closely...")
        print("Setting reading interval to 1 minute so we can monitor more closely...")

        reading_interval = 60

    elif sump_reading >= 200 and sump_reading <= 300:
        #Level in the sump is very low!
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        if butts_reading >= 300:
            logger.info("Opening wendy butts gate valve to 50%...")
            print("Opening wendy butts gate valve to 50%...")
            sockets["SOCK14"].write("Valve Position 50")

        else:
            logger.error("Insufficient water in wendy butts...")
            print("Insufficient water in wendy butts...")
            sockets["SOCK14"].write("Valve Position 0")

            logger.error("*** NOTICE ***: Water level in the sump is between 200 and 300 mm!")
            logger.error("*** NOTICE ***: HUMAN INTERVENTION REQUIRED: "
                         + "Please add water to the system.")

            print("\n\n*** NOTICE ***: Water level in the sump is between 200 and 300 mm!")
            print("*** NOTICE ***: HUMAN INTERVENTION REQUIRED: Please add water to the system.")

        #Make sure the main circulation pump is off.
        logger.warning("Disabling the main circulation pump, if it was on...")
        print("Disabling the main circulation pump, if it was on...")

        main_pump.disable()

        logger.warning("Setting reading interval to 30 seconds for close monitoring...")
        print("Setting reading interval to 30 seconds for close monitoring...")

        reading_interval = 30

    else:
        #Level in the sump is critically low!
        #If the butts pump is on, turn it oactuaff.
        butts_pump.disable()

        if butts_reading >= 300:
            logger.info("Opening wendy butts gate valve to 100%...")
            print("Opening wendy butts gate valve to 100%...")
            sockets["SOCK14"].write("Valve Position 100")

        else:
            logger.warning("Insufficient water in wendy butts...")
            print("Insufficient water in wendy butts...")
            sockets["SOCK14"].write("Valve Position 0")

            logger.critical("*** CRITICAL ***: Water level in the sump less than 200 mm!")
            logger.critical("*** CRITICAL ***: HUMAN INTERVENTION REQUIRED: Please add water to system.")
            logger.critical("*** INFO ***: The pump won't run dry; it has been temporarily disabled.")

            print("\n\n*** CRITICAL ***: Water level in the sump less than 200 mm!")
            print("*** CRITICAL ***: HUMAN INTERVENTION REQUIRED: Please add water to the system.")
            print("*** INFO ***: The pump won't run dry; it has been temporarily disabled.")

        #Make sure the main circulation pump is off.
        logger.warning("Disabling the main circulation pump, if it was on...")
        print("Disabling the main circulation pump, if it was on...")

        main_pump.disable()

        logger.critical("Setting reading interval to 15 seconds for super close monitoring...")
        print("Setting reading interval to 15 seconds for super close monitoring...")

        reading_interval = 15

    #Set the reading interval in the monitors, and send it down the sockets to the peers.
    for monitor in monitors:
        monitor.set_reading_interval(reading_interval)

    for each_socket in sockets.values():
        each_socket.write("Reading Interval: "+str(reading_interval))

    return reading_interval

# -------------------- MISCELLANEOUS FUNCTIONS --------------------
def setup_devices(system_id, dictionary="Probes"):
    """
    This function is used to set up the device objects for each site.

    Args:
        system_id (str):              The system (pi) that we're setting up for.

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
            high_limits = device_settings["HighLimits"]
            low_limits = device_settings["LowLimits"]

            #Create the multdimensional list for the Depth values
            depths = []
            depths.append(device_settings["Depths100s"])
            depths.append(device_settings["Depths25s"])
            depths.append(device_settings["Depths50s"])
            depths.append(device_settings["Depths75s"])

            device.set_limits(high_limits, low_limits)
            device.set_depths(depths)
            device.start_thread()

        elif _type == "Motor":
            #The pins are outputs for these.
            pins = device_settings["Pins"]
            device.set_pins(pins, _input=False)

            #Immediately disable the motor, as it seems they can turn on during
            #startup, if state is not initialised.
            device.disable()

        else:
            pins = device_settings["Pins"]
            device.set_pins(pins)

        devices.append(device)

    return devices

def setup_valve(system_id):
    """
    This function is used to set up gate valves.

    Args:
        system_id (str):              The system (pi) that we're setting up for.

    Returns:
        A reference to the GateValve object created.

    Usage:
        >>> setup_valve("V4")

    """
    valve_settings = config.SITE_SETTINGS[system_id]

    valve_name = valve_settings["Name"]
    _type = valve_settings["Type"]
    valve = valve_settings["Class"]
    pins = valve_settings["Pins"]
    pos_tolerance = valve_settings["posTolerance"]
    max_open = valve_settings["maxOpen"]
    min_open = valve_settings["minOpen"]
    ref_voltage = valve_settings["refVoltage"]

    valve = valve(system_id, valve_name, pins, pos_tolerance, max_open, min_open, ref_voltage)

    valve.start_thread()

    return valve

def get_and_handle_new_reading(monitor, _type, server_address=None, socket=None):
    """
    This function is used to get, handle, and return new readings from the
    monitors. It checks each monitor to see if there is data, then prints
    and logs it if needed, before writing the new reading down the socket
    to the master pi, if a connection has been set up.

    Args:
        monitor (BaseMonitorClass):     The monitor we're checking.
        _type (str):                    The type of probe we're monitoring.

    KWargs:
        server_address (str):           The server address. Set to None if
                                        not specified.

        socket (Sockets):               The socket connected to the master pi.
                                        Set to None if not specified.

    Returns:
        A Reading object.

    Usage:

        >>> get_and_handle_new_reading(<BaseMonitorClass-Obj>)

        OR

        >>> get_and_handle_new_reading(<BaseMonitorClass-Obj>, "192.168.0.2")

        OR

        >>> get_and_handle_new_reading(<BaseMonitorClass-Obj>, "192.168.0.2", <Socket-Obj>)
    """

    reading = None

    while monitor.has_data():
        last_reading = monitor.get_previous_reading()

        reading = monitor.get_reading()

        #Check if the reading is different to the last reading.
        if reading == last_reading: #TODO What to do here if a fault is detected?
            #Write a . to each file.
            logger.info(".")
            print(".", end='') #Disable newline when printing this message.

        else:
            #Write any new readings to the file and to stdout.
            logger.info(str(reading))

            print(reading)

        #Flush buffers.
        sys.stdout.flush()

        if server_address is not None:
            socket.write(reading)

    return reading
