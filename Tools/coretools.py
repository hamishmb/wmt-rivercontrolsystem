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
import shutil
import time
import threading
import subprocess
import logging
import os.path

#Extra imports.
import psutil

#Import modules.
sys.path.insert(0, os.path.abspath('..'))

import config

#These are injected from main.py to avoid a circular import problem.
sockettools = None #pylint: disable=invalid-name
dbtools = None #pylint: disable=invalid-name
logiccoretools = None #pylint: disable=invalid-name

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

        reading_time (str):         The time of the reading. Format as returned
                                    from running str(datetime.datetime.now()).

        reading_tick (int):         The system tick number at the time the reading
                                    was taken. A positive integer.

        reading_id (str):           The ID for the reading. Format: Two
                                    characters to identify the group, followed
                                    by a colon, followed by two more characters
                                    to identify the probe. Example: "G4:M0".

        reading_value (str):        The value of the reading. Format differs
                                    depending on probe type at the moment.
                                    Ideally, these would all be values in mm like:
                                    "400mm".

        reading_status (str):       The status of the probe at the time the reading
                                    was taken. If there is no fault, this should be
                                    "OK". Otherwise, it should be "FAULT DETECTED: "
                                    followed by some sensor-dependant information
                                    about the fault.

    Usage:
        The constructor for this class takes four arguments as specified above.

        >>> my_reading = coretools.Reading(<a_time>, <a_tick>, <an_id>, <a_value>, <a_status>)

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
            >>> Reading at time 2018, and tick 101, from probe: G4:M0, with value: 500, \
            >>> and status: FAULT DETECTED
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

            See Usage below for an example.

        Usage:
            >>> reading_1.as_csv()
            >>> "2018-06-11 11:04:01.635548,101,G4:M0,500,OK"
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
        site_id (str):                  The site ID of this pi.
    """

    def __init__(self, site_id):
        """The constructor"""
        threading.Thread.__init__(self)
        self.site_id = site_id
        self.is_running = True

        self.start()

    def run(self):
        """The main body of the thread"""
        while not config.EXITING:
            cmd = subprocess.run(["sudo", "rdate", config.SITE_SETTINGS["NAS"]["IPAddress"]],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

            stdout = cmd.stdout.decode("UTF-8", errors="ignore")

            if cmd.returncode != 0:
                logger.error("SyncTime: Unable to sync system time with NAS box. "
                             + "Error was: "+str(stdout))

                print("SyncTime: Unable to sync system time with NAS box.",
                      "Error was: "+str(stdout), level="error")

                #If this isn't Sump Pi, try to sync with Sump Pi instead.
                if self.site_id != "SUMP":
                    print("SyncTime: Falling back to Sump Pi...", level="error")
                    logger.error("SyncTime: Falling back to Sump Pi...")

                    cmd = subprocess.run(["sudo", "rdate",
                                          config.SITE_SETTINGS["SUMP"]["IPAddress"]],
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         check=False)

                    stdout = cmd.stdout.decode("UTF-8", errors="ignore")

                    if cmd.returncode != 0:
                        logger.error("SyncTime: Unable to sync system time with Sump Pi. "
                                     + "Error was: "+str(stdout))

                        print("SyncTime: Unable to sync system time with Sump Pi. "
                              + "Error was: "+str(stdout), level="error")

                        logger.error("SyncTime: Retrying time sync in 10 seconds...")
                        sleep = 10

                    else:
                        logger.error("SyncTime: Retrying time sync in 10 seconds...")
                        sleep = 10

                else:
                    logger.error("SyncTime: Retrying time sync in 10 seconds...")
                    sleep = 10

            else:
                logger.info("SyncTime: System time synchronised, now set to "+str(stdout))
                print("SyncTime: System time synchronised, now set to "+str(stdout))
                sleep = 86400

            #Respond to system teardown quickly.
            count = 0

            while count < sleep and not config.EXITING:
                count += 1
                time.sleep(1)

        #Signal that we have exited.
        self.is_running = False

    #----- CONTROL METHODS -----
    def wait_exit(self):
        """
        This method is used to wait for the timesync thread to exit.

        This isn't a mandatory function as the timesync thread will tear down
        automatically when config.EXITING is set to True.

        Usage:
            >>> <SyncTimeObject>.wait_exit()
        """

        while self.is_running:
            time.sleep(0.5)

class MonitorLoad(threading.Thread):
    """
    This class starts a thread that repeatedly monitors system load every 30
    seconds and logs this information in the log file.
    """

    def __init__(self):
        """The constructor"""
        threading.Thread.__init__(self)
        self.is_running = True

        self.start()

    def run(self):
        """The main body of the thread"""
        #The first time around, this returns a meaningless value, so discard it.
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

            #Respond to system teardown quickly.
            sleep = 30
            count = 0

            while count < sleep and not config.EXITING:
                count += 1
                time.sleep(1)

        #Signal that we have exited.
        self.is_running = False

    #----- CONTROL METHODS -----
    def wait_exit(self):
        """
        This method is used to wait for the monitorload thread to exit.

        This isn't a mandatory function as the monitorload thread will tear down
        automatically when config.EXITING is set to True.

        Usage:
            >>> <MonitorLoadObject>.wait_exit()
        """

        while self.is_running:
            time.sleep(0.5)

# -------------------- DATABASE FUNCTIONS AND CLASSES --------------------
#NB: Moved to /Tools/dbtools.py

# -------------------- CONTROL LOGIC FUNCTIONS AND CLASSES --------------------
#NB: Moved to /Logic/

# -------------------- STARTUP FUNCTIONS --------------------
def setup_sockets(site_id):
    """
    This function is used to set up the sockets for each site.

    Args:
        site_id (str):              The system that we're setting up for.

    Returns:
        If this is not the NAS box:
            Socket.     The nas socket for this site.

        If this is the NAS box:
            None.

    Usage:
        >>> nas_socket = setup_sockets("G4")

    """
    #Create all sockets.
    logger.info("Creating sockets...")

    nas_socket = None

    if config.SITE_SETTINGS[site_id]["HostingSockets"]:
        #We are a server, and we are hosting sockets.
        #Use info ation from the other sites to figure out what sockets to create.
        for site_settings in config.SITE_SETTINGS.values():
            #If no server is defined for this site, skip it.
            if "SocketName" not in site_settings:
                continue

            socket = sockettools.Sockets("Socket", site_id, site_settings["SocketName"])
            socket.set_portnumber(site_settings["ServerPort"])
            socket.set_server_address(site_settings["IPAddress"])

            socket.start_handler()

    #If a server is defined for this pi, connect to it.
    if "SocketName" in config.SITE_SETTINGS[site_id]:
        #Connect to the server.
        socket = sockettools.Sockets("Plug", site_id,
                                      config.SITE_SETTINGS[site_id]["ServerName"])

        socket.set_portnumber(config.SITE_SETTINGS[site_id]["ServerPort"])
        socket.set_server_address(config.SITE_SETTINGS[site_id]["ServerAddress"])
        socket.start_handler()

        nas_socket = socket

    logger.debug("Done!")

    return nas_socket

def setup_devices(site_id, dictionary="Probes"):
    """
    This function is used to set up the device objects for each site.

    Args:
        site_id (str):                The system that we're setting up for.

    Named args:
        dictionary (str):             The dictionary in config.py to set up for.
                                      If not specified, default is "Probes".

    Returns:
        A list of the device objects that were set up.

    Usage:
        >>> setup_devices("G4")

    """
    devices = []

    for device_id in config.SITE_SETTINGS[site_id][dictionary]:
        device_settings = config.SITE_SETTINGS[site_id][dictionary][device_id]

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
            if site_id == "SUMP" and device_id == "SUMP:P1":
                print("Enabling circulation pump to avoid overflow while waiting "
                      + "for NAS box...")

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

def wait_for_tick(nas_socket):
    """
    This function is used to wait for the system tick on boot. This is used on all systems
    except the NAS box (which supplies the tick).

    Args:
        nas_socket (Socket):          The socket that connects to the NAS box.

    Usage:
        >>> wait_for_tick(<Socket>)

    """
    #Request the latest system tick value and wait 180 seconds for it to come in.
    logger.info("Waiting up to 180 seconds for the system tick (Press CTRL-C to skip)...")
    print("Waiting up to 180 seconds for the system tick (Press CTRL-C to skip)...")

    count = 0

    try:
        while config.TICK == 0 and count < 18:
            nas_socket.write("Tick?")

            if nas_socket.has_data():
                data = nas_socket.read()

                if "Tick:" in data:
                    #Store tick sent from the NAS box.
                    config.TICK = int(data.split(" ")[1])

                    print("New tick: "+data.split(" ")[1])
                    logger.info("New tick: "+data.split(" ")[1])

                nas_socket.pop()

            time.sleep(10)

        count += 1

    except KeyboardInterrupt:
        print("\nSystem tick wait skipped as requested by user.")
        logger.info("System tick wait skipped as requested by user.")

    if config.TICK != 0:
        logger.info("Received tick")
        print("Received tick")

    else:
        logger.error("Could not get tick within 180 seconds!")
        print("Could not get tick within 180 seconds!", level="error")

# -------------------- MAIN LOOP FUNCTIONS --------------------
def get_local_readings(monitors, readings):
    """
    This function gets all the readings from the local monitors and adds them
    to the local readings list.

    Args:
        monitors (list of BaseMonitorClass):     The monitors.
        readings (list of Reading):              The local readings list.

    Usage:

        >>> get_local_readings(list<BaseMonitorClass>, list<Reading>)
    """

    for monitor in monitors:
        #Skip over any monitors that have stopped.
        if not monitor.is_running():
            logger.error("Monitor for "+monitor.get_site_id()+":"+monitor.get_probe_id()
                         + " is not running!")

            print("Monitor for "+monitor.get_site_id()+":"+monitor.get_probe_id()
                  + " is not running!", level="error")

            logiccoretools.log_event("Monitor for "+monitor.get_site_id()+":"
                                     + monitor.get_probe_id()+" is not running!",
                                     severity="ERROR")

            continue

        #Check for new readings.
        reading = get_and_handle_new_reading(monitor, "test")

        #Ignore empty readings.
        if reading is None:
            continue

        #Keep all the readings we get, for the control logic functions.
        #Only some of the control logic functions use these.
        readings[reading.get_id()] = reading

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
            print(".", level="none", end='') #Disable newline when printing this message.

        else:
            #Write any new readings to the file and to stdout.
            logger.info(str(reading))

            print(reading)

        #Flush buffers.
        sys.stdout.flush()

    return reading

def wait_for_next_reading_interval(reading_interval, site_id, nas_socket):
    """
    This function keeps watching for new messages coming from other sites while
    we count down the reading interval.

    Args:
        reading_interval:           The reading interval.
        site_id:                    The site id.
        nas_socket:                 The nas socket. Special None value if on NAS box.

    Usage:

        >>> wait_for_next_reading_interval(30, "SUMP", <Socket>)
    """
    #Keep watching for new messages from the socket while we count down the
    #reading interval.
    asked_for_tick = False
    count = 0

    while count < reading_interval:
        #This way, if our reading interval changes,
        #the code will respond to the change immediately.
        #Check if we have a new reading interval.
        if not asked_for_tick and (reading_interval - count) < 10 and site_id != "NAS":
            #Get the latest system tick if we're in the last 10 seconds of the interval.
            asked_for_tick = True
            nas_socket.write("Tick?")

        for _socket in config.SOCKETSLIST:
            if _socket.has_data():
                data = _socket.read()

                if not isinstance(data, str):
                    continue

                #-------------------- SYSTEM TICK HANDLING --------------------
                if data == "Tick?" and site_id == "NAS":
                    #NAS box only: reply with the current system tick when asked.
                    _socket.write("Tick: "+str(config.TICK))

                    print("Received request for current system tick")
                    logger.info("Received request for current system tick")

                elif "Tick:" in data and site_id != "NAS":
                    #Everything except NAS box: store tick sent from the NAS box.
                    config.TICK = int(data.split(" ")[1])

                    print("New tick: "+data.split(" ")[1])
                    logger.info("New tick: "+data.split(" ")[1])

                _socket.pop()

        time.sleep(1)
        count += 1


# -------------------- SITEWIDE UPDATER PREPARATION FUNCTIONS --------------------
#FIXME: These are currently broken. Do not use them.
#TODO: Could also do with some deduplication of code that checks the db, if I continue
#      with that approach.
def prepare_sitewide_actions(site_id): #FIXME
    """
    This function coordinates the following features:

    - Preparing to shut down just this system via database command or the presence of a file.
    - Preparing to shut down all systems via database command or the presence of a file.
    - Preparing to reboot just this system via database command or the presence of a file.
    - Preparing to reboot all systems via database command or the presence of a file.
    - Preparing to update all systems via database command or the presence of a file.

    .. warning::
            This is currently broken and sometimes doesn't behave deterministically.
            Do not use.

    Args:
        site_id:                  The site id.

    Usage:

        >>> handle_sitewide_actions("G4")
    """
    #Check the database and for the presence of local files.
    try:
        state = logiccoretools.get_state(config.SITE_ID, config.SITE_ID)

    except RuntimeError:
        state = None
        request = None

        print("Error: Couldn't check for requested site actions!", level="error")
        logger.error("Error: Couldn't check for requested site actions!")

    else:
        if state is not None:
            request = state[1].upper()

    #Figure out, from both the database and the files, if any sitewide actions have been
    #requested.
    #FIXME: Assert that only one of the three overarching actions here has been requested.

    config.SHUTDOWN = request in ("SHUTDOWN", "SHUTDOWNALL") \
                      or os.path.exists("/tmp/.shutdown") \
                      or os.path.exists("/tmp/.shutdownall")

    config.SHUTDOWNALL = request == "SHUTDOWNALL" or os.path.exists("/tmp/.shutdownall")

    config.REBOOT = request in ("REBOOT", "REBOOTALL") or os.path.exists("/tmp/.reboot") \
                    or os.path.exists("/tmp/.rebootall")

    config.REBOOTALL = request == "REBOOTALL" or os.path.exists("/tmp/.rebootall")

    config.UPDATE = request == "UPDATE" or os.path.exists("/tmp/.update")

    at_least_one_action = config.SHUTDOWN or config.REBOOT or config.UPDATE

    #Prepare for any sitewide actions.
    if config.SHUTDOWN:
        prepare_shutdown(site_id)

        try:
            os.remove("/tmp/.shutdown")

        except (OSError, IOError):
            pass

        try:
            os.remove("/tmp/.shutdownall")

        except (OSError, IOError):
            pass

    elif config.REBOOT:
        prepare_reboot(site_id)

        try:
            os.remove("/tmp/.reboot")

        except (OSError, IOError):
            pass

        try:
            os.remove("/tmp/.rebootall")

        except (OSError, IOError):
            pass

    elif config.UPDATE:
        if site_id == "NAS":
            nas_prepare_update()

        else:
            pi_prepare_update()

        try:
            os.remove("/tmp/.update")

        except (OSError, IOError):
            pass

    #Signal the software to tear down if we are performing at least one site-wide action.
    #NOTE: Actually shutting down/rebooting/applying the update is done later after most of
    #      the framework has been torn down.
    if at_least_one_action:
        config.EXITING = True

def prepare_shutdown(site_id): #FIXME
    """
    This function prepares the system to shut down, and makes it known in the database
    that this is going to happen.

    If this is the NAS box, and all sites are to shut down, all sites are requested to
    shut down individually through the database.

    .. warning::
            This is currently broken and sometimes doesn't behave deterministically.
            Do not use.

    Args:
        site_id:                  The site id.

    Usage:

        >>> prepare_shutdown("G4")
    """
    try:
        logiccoretools.log_event("Preparing to shut down...")
        logiccoretools.update_status("Preparing to shut down", "N/A", "Shutdown")

    except RuntimeError:
        #FIXME: Take appropriate action here.
        print("Error: Couldn't update site status or event log!", level="error")
        logger.error("Error: Couldn't update site status or event log!")

    if site_id == "NAS" and config.SHUTDOWNALL:
        for _site_id in config.SITE_SETTINGS:
            try:
                logiccoretools.attempt_to_control(_site_id, _site_id, "Shutdown")

            except RuntimeError:
                #FIXME: Take appropriate action here.
                print("Error: Couldn't request poweroff for "+_site_id+"!", level="error")
                logger.error("Error: Couldn't request poweroff for "+_site_id+"!")

def prepare_reboot(site_id): #FIXME
    """
    This function prepares the system to reboot, and makes it known in the database
    that this is going to happen.

    If this is the NAS box, and all sites are to reboot, all sites are requested to
    reboot individually through the database.

    .. warning::
            This is currently broken and sometimes doesn't behave deterministically.
            Do not use.

    Args:
        site_id:                  The site id.

    Usage:

        >>> prepare_reboot("G4")
    """
    try:
        logiccoretools.log_event("Preparing to reboot...")
        logiccoretools.update_status("Preparing to reboot", "N/A", "Rebooting")

    except RuntimeError:
        #FIXME: Take appropriate action here.
        print("Error: Couldn't update site status or event log!", level="error")
        logger.error("Error: Couldn't update site status or event log!")

    if site_id == "NAS" and config.REBOOTALL:
        for _site_id in config.SITE_SETTINGS:
            try:
                logiccoretools.attempt_to_control(_site_id, _site_id, "Reboot")

            except RuntimeError:
                #FIXME: Take appropriate action here.
                print("Error: Couldn't request reboot for "+_site_id+"!", level="error")
                logger.error("Error: Couldn't request reboot for "+_site_id+"!")

def nas_prepare_update(): #FIXME
    """
    This function makes the update available to all pis and signals that they should
    update using the database. The update is made available at
    http://192.168.0.25/rivercontrolsystem.tar.gz. After this, the update is ready
    to be applied.

    .. warning::
            This function is intended to be run only on the NAS box. This is a
            do-nothing function on all devices except the NAS box.

    .. warning::
            This is currently broken and sometimes doesn't behave deterministically.
            Do not use.

    Usage:

        >>> nas_prepare_update("G4")
    """

    if config.SITE_ID != "NAS":
        return

    logger.info("Making new software available to all pis using webserver...")
    cmd = subprocess.run(["ln", "-s", "/mnt/HD/HD_a2/rivercontrolsystem.tar.gz",
                          "/var/www"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         check=False)

    stdout = cmd.stdout.decode("UTF-8", errors="ignore")

    if cmd.returncode != 0:
        #FIXME: Take appropriate action here.
        print("Error! Unable to host software update on webserver. "
              + "Error was:\n"+stdout+"\n", level="critical")

        logger.critical("Error! Unable to host software update on webserver. "
                        + "Error was:\n"+stdout+"\n")

    #Signal that we are updating.
    try:
        logiccoretools.log_event("Preparing to update...")
        logiccoretools.update_status("Up, CPU: "+config.CPU+"%, MEM: "
                                     +config.MEM+"%", "OK", "Updating")

    except RuntimeError:
        #FIXME: Take appropriate action here.
        print("Error: Couldn't update site status or event log!", level="error")
        logger.error("Error: Couldn't update site status or event log!")

    for site_id in config.SITE_SETTINGS:
        try:
            logiccoretools.attempt_to_control(site_id, site_id, "Update")

        except RuntimeError:
            #FIXME: Take appropriate action here.
            print("Error: Couldn't request update for "+site_id+"!", level="error")
            logger.error("Error: Couldn't request update for "+site_id+"!")

def pi_prepare_update(): #FIXME
    """
    This function downloads the update from the NAS box at
    http://192.168.0.25/rivercontrolsystem.tar.gz. After this, the update is ready
    to be applied.

    .. warning::
            This function is intended to be run only on the pis. This is a do-nothing
            function when run on the NAS box.

    .. warning::
            This is currently broken and sometimes doesn't behave deterministically.
            Do not use.

    Usage:

        >>> pi_prepare_update("G4")
    """
    if config.SITE_ID == "NAS":
        return

    #Download the update from the NAS box.
    logger.info("Downloading software update from NAS box...")
    cmd = subprocess.run(["wget", "-O", "/tmp/rivercontrolsystem.tar.gz",
                          "http://192.168.0.25/rivercontrolsystem.tar.gz"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

    stdout = cmd.stdout.decode("UTF-8", errors="ignore")

    if cmd.returncode != 0:
        #FIXME: Take appropriate action here.
        print("Error! Unable to download software update. "
              + "Error was:\n"+stdout+"\n", level="critical")

        logger.critical("Error! Unable to download software update. "
                        + "Error was:\n"+stdout+"\n")

    #Signal that we got it.
    try:
        logiccoretools.log_event("Preparing to update...")
        logiccoretools.update_status("Up, CPU: "+config.CPU+"%, MEM: "
                                     +config.MEM+"%", "OK", "Updating")

    except RuntimeError:
        #FIXME: Take appropriate action here.
        print("Error: Couldn't update site status or event log!", level="error")
        logger.error("Error: Couldn't update site status or event log!")

# -------------------- SITEWIDE UPDATER REALISATION FUNCTIONS --------------------
def do_sitewide_actions(site_id): #FIXME
    """
    This function coordinates the following features:

    - Shutting down just this system via database command or the presence of a file.
    - Shutting down all systems via database command or the presence of a file.
    - Rebooting just this system via database command or the presence of a file.
    - Rebooting all systems via database command or the presence of a file.
    - Updating all systems via database command or the presence of a file.

    .. warning::
            This is currently broken and sometimes doesn't behave deterministically.
            Do not use.

    Args:
        site_id:                  The site id.

    Usage:

        >>> do_sitewide_actions("G4")
    """

    if config.SHUTDOWN:
        do_shutdown(site_id)

    elif config.REBOOT:
        do_reboot(site_id)

    elif config.UPDATE:
        do_update(site_id)

def do_shutdown(site_id): #FIXME
    """
    This function shuts the system down.

    If this is the NAS box, and all sites are shutting down, we wait until we can confirm
    that they all received the shutdown request.

    .. warning::
            This is currently broken and sometimes doesn't behave deterministically.
            Do not use.

    Args:
        site_id:                  The site id.

    Usage:

        >>> do_shutdown("G4")
    """

    print("System shutdown sequence initiated.")
    logger.info("System shutdown sequence initiated.")

    if site_id != "NAS":
        print("Sequence complete. Process successful. Shutting down now.")
        logger.info("Sequence complete. Process successful. Shutting down now.")
        logging.shutdown()
        subprocess.run(["poweroff"], check=False)

    #The NAS box needs a special script for safe and reliable shutdown.
    elif not config.SHUTDOWNALL:
        print("Sequence complete. Process successful. Shutting down now.")
        logger.info("Sequence complete. Process successful. Shutting down now.")
        logging.shutdown()
        subprocess.run(["ash", "/home/admin/shutdown.sh"], check=False)

    #Wait until all the pis have shut down before we shut down the NAS box.
    elif config.SHUTDOWNALL:
        #Restart database thread to check.
        #FIXME We don't wait to make sure the DB connection is alive!
        config.EXITING = False
        dbtools.DatabaseConnection(site_id)
        config.DBCONNECTION.start_thread()

        print("Waiting for pis shut down...")
        logger.info("Waiting for pis to shut down...")

        done = []

        while True:
            for _site_id in config.SITE_SETTINGS:
                if _site_id == "NAS" or _site_id in done:
                    continue

                try:
                    status = logiccoretools.get_status(_site_id)

                except RuntimeError:
                    print("Error: Couldn't get "+_site_id+" site status!", level="error")
                    logger.error("Error: Couldn't get "+_site_id+" site status!")
                    continue

                if status is not None:
                    action = status[2].upper()

                    if action == "SHUTTING DOWN":
                        print("Shut down: "+_site_id)
                        logger.info("Shut down: "+_site_id)
                        done.append(_site_id)

            #When all have shut down (ignoring NAS), break out.
            if done and len(done) == len(config.SITE_SETTINGS.keys()) - 1:
                break

            time.sleep(5)

        #All pis have shut down, now shut down the NAS box with the special script.
        print("Sequence complete. Process successful. Shutting down now.")
        logger.info("Sequence complete. Process successful. Shutting down now.")
        logging.shutdown()
        subprocess.run(["ash", "/home/admin/shutdown.sh"], check=False)

def do_reboot(site_id): #FIXME
    """
    This function reboots the system.

    If this is the NAS box, and all sites are rebooting, we wait until we can confirm
    that they all received the reboot request.

    .. warning::
            This is currently broken and sometimes doesn't behave deterministically.
            Do not use.

    Args:
        site_id:                  The site id.

    Usage:

        >>> do_reboot("G4")
    """

    print("System reboot sequence initiated.")
    logger.info("System reboot sequence initiated.")

    if site_id != "NAS":
        print("Sequence complete. Process successful. Rebooting now.")
        logger.info("Sequence complete. Process successful. Rebooting now.")
        logging.shutdown()
        subprocess.run(["reboot"], check=False)

    #The NAS box needs a special script for safe and reliable rebooting.
    elif not config.REBOOTALL:
        print("Sequence complete. Process successful. Rebooting now.")
        logger.info("Sequence complete. Process successful. Rebooting now.")
        logging.shutdown()
        subprocess.run(["ash", "/home/admin/reboot.sh"], check=False)

    #Wait until all the pis have rebooted before we reboot the NAS box.
    elif config.REBOOTALL:
        #Restart database thread to check.
        #FIXME We don't wait to make sure the DB connection is alive!
        config.EXITING = False
        dbtools.DatabaseConnection(site_id)
        config.DBCONNECTION.start_thread()

        print("Waiting for pis to reboot...")
        logger.info("Waiting for pis to reboot...")

        done = []

        while True:
            for _site_id in config.SITE_SETTINGS:
                if _site_id == "NAS" or _site_id in done:
                    continue

                try:
                    status = logiccoretools.get_status(_site_id)

                except RuntimeError:
                    print("Error: Couldn't get "+_site_id+" site status!", level="error")
                    logger.error("Error: Couldn't get "+_site_id+" site status!")
                    continue

                if status is not None:
                    action = status[2].upper()

                    if action == "REBOOTING":
                        print("Rebooted: "+_site_id)
                        logger.info("Rebooted: "+_site_id)
                        done.append(_site_id)

            #When all have rebooted (ignoring NAS), break out.
            if done and len(done) == len(config.SITE_SETTINGS.keys()) - 1:
                break

            time.sleep(5)

        #All pis have rebooted, now reboot the NAS box with the special script.
        print("Sequence complete. Process successful. Rebooting now.")
        logger.info("Sequence complete. Process successful. Rebooting now.")
        logging.shutdown()
        subprocess.run(["ash", "/home/admin/reboot.sh"], check=False)

def do_update(site_id): #FIXME
    """
    This function updates the system. This is done by moving the existing river system
    software to rivercontrolsystem.old, extracting the previously-downloaded
    update tarball, and then cleaning up by removing the tarball. Finally, the system
    is rebooted, completing the process with a normal system start-up sequence.

    If this is the NAS box, we always update all sites at the same time, so we wait
    until we can confirm that they all received the update request. After that, the
    above sequence is performed on the NAS box, and then the NAS box reboots.

    .. warning::
            This is currently broken and sometimes doesn't behave deterministically.
            Do not use.

    Args:
        site_id:                  The site id.

    Usage:

        >>> do_update("G4")
    """

    print("System update sequence initiated.")
    logger.info("System update sequence initiated.")

    if site_id != "NAS":
        update_files("/home/pi")

        #Reboot.
        print("Sequence complete. Process successful. Rebooting now.")
        logger.info("Sequence complete. Process successful. Rebooting now.")
        logging.shutdown()
        subprocess.run(["reboot"], check=False)

    else:
        #Wait until all the pis have downloaded the update.
        #Restart database thread to check.
        #FIXME We don't wait to make sure the DB connection is alive!
        config.EXITING = False
        dbtools.DatabaseConnection(site_id)
        config.DBCONNECTION.start_thread()

        print("Waiting for pis to download the update...")
        logger.info("Waiting for pis to download the update...")

        done = []

        while True:
            for _site_id in config.SITE_SETTINGS:
                if _site_id == "NAS" or _site_id in done:
                    continue

                try:
                    status = logiccoretools.get_status(_site_id)

                except RuntimeError:
                    print("Error: Couldn't get "+_site_id+" site status!", level="error")
                    logger.error("Error: Couldn't get "+_site_id+" site status!")
                    continue

                if status is not None:
                    action = status[2].upper()

                    if action == "UPDATING":
                        print("Updated: "+_site_id)
                        logger.info("Updated: "+_site_id)
                        done.append(_site_id)

            #When all have grabbed the file (ignoring NAS), break out.
            if done and len(done) == len(config.SITE_SETTINGS.keys()) - 1:
                break

            time.sleep(5)

        print("All pis have updated. Updating now.")
        logger.info("All pis have updated. Updating now.")

        update_files("/mnt/HD/HD_a2")

        #All pis have updated, now reboot the NAS box with the special script.
        print("Sequence complete. Process successful. Rebooting now.")
        logger.info("Sequence complete. Process successful. Rebooting now.")
        logging.shutdown()
        subprocess.run(["ash", "/home/admin/reboot.sh"], check=False)

def update_files(instdir): #FIXME
    """
    This function moves the files around during a system update.

    .. warning::
            This is currently broken and sometimes doesn't behave deterministically.
            Do not use.

    Args:
        instdir:                  The directory where the river control system is installed.

    Usage:

        >>> update_files("/home/pi")
    """

    #Move current software to rivercontrolsystem.old.
    if os.path.exists(instdir+"/rivercontrolsystem.old"):
        logger.info("Removing old software backup...")
        shutil.rmtree(instdir+"/rivercontrolsystem.old")

    logger.info("Backing up existing software to rivercontrolsystem.old...")
    cmd = subprocess.run(["mv", instdir+"/rivercontrolsystem",
                          instdir+"/rivercontrolsystem.old"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

    stdout = cmd.stdout.decode("UTF-8", errors="ignore")

    if cmd.returncode != 0:
        #FIXME: Take appropriate action here.
        print("Error! Unable to backup existing software. "
              + "Error was:\n"+stdout+"\n", level="critical")

        logger.critical("Error! Unable to backup existing software. "
                        + "Error was:\n"+stdout+"\n")

    #Extract new software.
    logger.info("Applying update...")
    cmd = subprocess.run(["tar", "-xf", "/tmp/rivercontrolsystem.tar.gz", "-C",
                          instdir],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

    stdout = cmd.stdout.decode("UTF-8", errors="ignore")

    if cmd.returncode != 0:
        #FIXME: Take appropriate action here.
        print("Error! Unable to extract new software. "
              + "Error was:\n"+stdout+"\n", level="critical")

        logger.critical("Error! Unable to extract new software. "
                        + "Error was:\n"+stdout+"\n")

    #Clean up.
    logger.info("Removing downloaded tarball...")
    if os.path.exists(instdir+"/rivercontrolsystem.tar.gz"):
        os.remove(instdir+"/rivercontrolsystem.tar.gz")

# -------------------- MISCELLANEOUS FUNCTIONS --------------------
#ANSI colours to use in the terminal.
BLACK = "\033[1;30m"
RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
MAGENTA = "\033[1;35m"
CYAN = "\033[1;36m"
WHITE = "\033[1;37m"
BRIGHT_BLACK = "\033[1;90m"
BRIGHT_RED = "\033[1;91m"
BRIGHT_GREEN = "\033[1;92m"
BRIGHT_YELLOW = "\033[1;93m"
BRIGHT_BLUE = "\033[1;94m"
BRIGHT_MAGENTA = "\033[1;95m"
BRIGHT_CYAN = "\033[1;96m"
BRIGHT_WHITE = "\033[1;97m"
DEFAULT = "\033[00m"

def rcs_print(*args, level="info", end="\n"):
    """
    This function provides a way to print messages to the console with severity
    information. This is also used so we can silence commandline output upon
    request when running the CLI, and when running the unit tests.

    The text is coloured depending on the severity level.

    Named Args:
        level[="info"] (str).         The severity of the message. Valid values are "debug",
                                      "info", "warning", "error", and "critical". We default
                                      to info if the value isn't recognised. "none" is also
                                      accepted to avoid having any severity prefix.

        end[="\n"] (str).             Specifies the character printed at the end of the
                                      message.

    Arbitrary arguments are also accepted and are just printed just like when using the
    default Python print() function.
    """

    level = level.lower()

    if level == "debug":
        prefix = "D: "

    elif level == "info":
        prefix = BRIGHT_GREEN+"I: "

    elif level == "warning":
        prefix = BRIGHT_BLUE+"W: "

    elif level == "error":
        prefix = BRIGHT_YELLOW+"!ERROR: "

    elif level == "critical":
        prefix = BRIGHT_RED+"!!!CRITICAL: "

    elif level == "none":
        prefix = BRIGHT_GREEN

    #Default to INFO if we don't know.
    else:
        builtin_print(BRIGHT_BLUE+"WARNING: Unknown message severity: "+level)
        logger.warning("Unknown message severity: "+level)
        prefix = GREEN+"I: "

    #Sanitize args
    safe_args = []
    count = 0

    for arg in args:
        #Handle messages that start with a newline properly.
        if count == 0 and isinstance(arg, str) and arg.startswith("\n"):
            prefix = "\n"+prefix
            arg = ' '.join(arg.split("\n")[1:])

        safe_args.append(str(arg))

    args = safe_args

    builtin_print(prefix+' '.join(args)+DEFAULT, end=end)

#Override print() with rcs_print.
builtin_print = print
print = rcs_print #pylint: disable=redefined-builtin
