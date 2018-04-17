#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Core Tools for the River System Control and Monitoring Software Version 0.9.2
# Copyright (C) 2017-2018 Wimborne Model Town
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

import datetime
import sys
import os
import logging

VERSION = "0.9.2"

#Don't ask for a logger name, so this works with both main.py
#and the universal monitor.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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

        reading_id (String):        The ID for the reading. Format: Two
                                    characters to identify the group, followed
                                    by a colon, followed by two more characters
                                    to identify the probe. Example: "G4:M0".

        reading_time (String):      The time of the reading. Format as returned
                                    from running str(datetime.datetime.now()).

        reading_value (String):     The value of the reading. Format differs
                                    depending on probe type at the moment **FIXME**.
                                    Ideally, these would all be values in mm like:
                                    400mm.

        reading_status (String):    The status of the probe at the time the reading
                                    was taken. If there is no fault, this should be
                                    "OK". Otherwise, it should be "FAULT DETECTED: "
                                    followed by some sensor-dependant information
                                    about the fault.

    Usage:
        The constructor for this class takes four arguments as specified above.

        >>> my_reading = core_tools.Reading(<an_id>, <a_time>, <a_value>, <a_status>)
        >>> my_reading = core_tools.Reading("G4:M0", str(datetime.datetime.now()), "500mm", "OK")

    .. warning::
        There is currently **absolutely no** check to see that each instance variable
        actually has the correct format. This will come later.
    """

    # ---------- CONSTRUCTORS ----------
    def __init__(self, reading_id, reading_time, reading_value, reading_status):
        """This is the constructor as defined above"""
        #Set some semi-private variables. TODO format checking.
        self._id = reading_id
        self._time = reading_time
        self._value = reading_value
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

def greet_and_get_filename(module_name, file_name):
    """
    This function greets the user and, if needed (not specified on the
    commandline), asks him/her for a file name to store readings in. It
    then proceeds to check that the file is valid and writable.

    Args:
        module_name (str):  The program that has been started. Either
                            the main software or the universal monitor.

        file_name (str):    The file name the program got from the
                            commandline arguments. Prompt user to enter
                            a name if this is "Unknown".

    Returns:
        tuple(str <file name>, file <file handle>)

    Raises:
        None, but will exit the program if a critical error is
        encountered with sys.exit().

    Usage:

        >>> file_name, file_handle = greet_and_get_filename("AProgramName", "AFileName")

    """

    print("System Time: ", str(datetime.datetime.now()))
    print(module_name+" is running standalone.")
    print("Welcome. This program will quit automatically if you specified a number of readings.")
    print("otherwise quit by pressing CTRL-C when you wish.\n")

    #Get filename, if one wasn't specified.
    if file_name == "Unknown":
        print("Please enter a filename to save the readings to.")
        print("This isn't a log file. The log file will be created automatically")
        print("and will store debugging information, whereas this file just stores")
        print("Readings.\n")
        print("The file will be appended to.")
        print("Make sure it's somewhere where there's plenty of disk space.")

        sys.stdout.write("Enter filename and press ENTER: ")

        file_name = input()

        print("\n\nSelected File: "+file_name)

        if os.path.isfile(file_name):
            print("*WARNING* This file already exists!")

        print("Press CTRL-C if you are not happy with this choice.\n")

        print("Press ENTER to continue...")

        input() #Wait until user presses enter.

    if os.path.isfile(file_name):
        print("*WARNING* The file chosen already exists!")

    try:
        print("Opening file...")
        recordings_file_handle = open(file_name, "a")

    except BaseException as err:
        #Bad practice :P
        print("Error opening file. Do you have permission to write there?")
        print("Exiting...")
        sys.exit()

    else:
        recordings_file_handle.write("Start Time: "+str(datetime.datetime.now())+"\n\n")
        recordings_file_handle.write("Starting to take readings...\n")
        print("Successfully opened file. Continuing..")

    return file_name, recordings_file_handle

def get_and_handle_new_reading(monitor, _type, file_handle, server_address=None, socket=None):
    """
    This function is used to get, handle, and return new readings from the
    monitors. It checks each monitor to see if there is data, then prints
    and logs it if needed, before writing the new reading down the socket
    to the master pi, if a connection has been set up.

    Args:
        monitor (BaseMonitorClass):     The monitor we're checking.
        _type (str):                    The type of probe we're monitoring.
        file_handle (file):             A handle for the readings file.

    KWargs:
        server_address (str):           The server address. Set to None if
                                        not specified.

        socket (Sockets):               The socket connected to the master pi.
                                        Set to None if not specified.

    Returns:
        tuple(str reading_id, str reading_time, str reading, str reading_status).

    Usage:

        >>> get_and_handle_new_reading(<BaseMonitorClass-Obj>, <aFile>)
        >>> (<id>, <time>, "500", "OK")

        OR

        >>> get_and_handle_new_reading(<BaseMonitorClass-Obj>, <aFile>, "192.168.0.2")
        >>> (<id>, <time>, "500", "OK")

        OR

        >>> get_and_handle_new_reading(<BaseMonitorClass-Obj>, <aFile>, "192.168.0.2", <Socket-Obj>)
        >>> (<id>, <time>, "500", "OK")
    """

    reading_id = reading_time = reading = reading_status = ""

    if monitor.has_data():
        last_reading = monitor.get_previous_reading()

        reading_id, reading_time, reading, reading_status = monitor.get_reading()

        #Check if the reading is different to the last reading.
        if reading == last_reading: #TODO What to do here if a fault is detected?
            #Write a . to each file.
            logger.info(".")
            print(".", end='') #Disable newline when printing this message.
            file_handle.write(".")

        else:
            #Write any new readings to the file and to stdout.
            logger.info("ID: "+reading_id+" Time: "+reading_time+" "
                        +_type+": "+reading+" Status: "+reading_status)

            print("\nID: "+reading_id+" Time: "+reading_time+" "
                  +_type+": "+reading+" Status: "+reading_status)

            file_handle.write("\nID: "+reading_id+" Time: "+reading_time+" "
                              +_type+": "+reading+" Status: "+reading_status)

        #Flush buffers.
        sys.stdout.flush()
        file_handle.flush()

        if server_address is not None:
            socket.write([reading_id, reading_time, reading, reading_status])

    return reading_id, reading_time, reading, reading_status

def do_control_logic(sump_reading, butts_reading, butts_pump, main_pump, monitor, socket, reading_interval):
    """
    This function is used to decides what action to take based
    on the readings it is passed.

    The butts pump is turned on when the sump level >= 600mm, and
    turned off when it reaches 400mm. The circulation pump is
    turned on when the sump level >= 400, and otherwise the
    circulation pump will be turned off.

    The reading intervals at both the sumppi and the buttspi end
    are controlled and set here as well.

    .. note::
        Just added support for SSR 2 (circulation pump).

    Otherwise, nothing currently happens because there is nothing
    else we can take control of at the moment.

    Args:
        sump_reading (str):     The newest reading we have from
                                the sump probe.

        butts_reading (str):    As above, but for the butts.

        butts_pump (Motor):     A reference to a Motor object
                                that represents the butts pump.

        main_pump (Motor):      A refernece to a Motor object
                                that represents the main circulation
                                pump.

        monitor (Monitor):      A reference to a Monitor object
                                that is used to monitor the sump
                                level. Passed here so we can
                                control the reading interval at
                                this end.

        socket (Socket):        A reference to the Socket object
                                that represents the data connection
                                between sumppi and buttspi. Passed
                                here so we can control the reading
                                interval at that end.

        reading_interval (int): The current reading interval, in
                                seconds.

    Returns:
        int: The reading interval, in seconds.

    Usage:

        >>> reading_interval = do_control_logic(<asumpreading>, <abuttsreading>,
        >>>                                     <apumpobject>, <apumpobject>,
        >>>                                     <amonitorthreadobject,
        >>>                                     <asocketsobject>, <areadinginterval)

    """

    #Remove the 'mm' from the end of the reading and convert to int.
    sump_reading = int(sump_reading.replace("m", ""))

    if sump_reading >= 600:
        #Level in the sump is getting high.
        logger.warning("Water level in the sump ("+str(sump_reading)+") >= 600mm!")
        print("Water level in the sump ("+str(sump_reading)+") >= 600mm!")

        #Make sure the main circulation pump is on.
        logger.info("Turning the main circulation pump on, if it was off...")
        print("Turning the main circulation pump on, if it was off...")

        main_pump.enable()

        #Pump some water to the butts if they aren't full.
        #If they are full, do nothing and let the sump overflow.
        if butts_reading == "False":
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

    elif sump_reading == 500:
        #Level is okay.
        #We might be pumping right now, or the level is increasing, but do nothing.
        #^ Do NOT change the state of the butts pump.
        logger.info("Water level in the sump is 500mm.")
        print("Water level in the sump is 500mm.")

        #Make sure the main circulation pump is on.
        logger.info("Turning the main circulation pump on, if it was off...")
        print("Turning the main circulation pump on, if it was off...")

        main_pump.enable()

    elif sump_reading == 400:
        #Level in the sump is good.
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        logger.info("Water level in the sump is 400mm. Turned the butts pump off, if it was on.")
        print("Water level in the sump is 400mm. Turned the butts pump off, if it was on.")

        #Make sure the main circulation pump is on.
        logger.info("Turning the main circulation pump on, if it was off...")
        print("Turning the main circulation pump on, if it was off...")

        main_pump.enable()

        logger.info("Setting reading interval to 5 minutes...")
        print("Setting reading interval to 5 minutes...")
        reading_interval = 300

    elif sump_reading == 300:
        #Level in the sump is getting low.
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        logger.warning("Water level in the sump is 300mm!")
        logger.warning("Waiting for water to come back from the butts before "
                       +"requesting human intervention...")

        print("Water level in the sump is 300mm!")
        print("Waiting for water to come back from the butts before requesting "
              +"human intervention...")

        #Make sure the main circulation pump is off.
        logger.warning("Disabling the main circulation pump, if it was on...")
        print("Disabling the main circulation pump, if it was on...")

        main_pump.disable()

        logger.warning("Setting reading interval to 1 minute so we can monitor more closely...")
        print("Setting reading interval to 1 minute so we can monitor more closely...")

        reading_interval = 60

        #We have no choice here but to wait for water to come back from the butts and warn the user.
        #^ Tap is left half-open.

    elif sump_reading == 200:
        #Level in the sump is very low!
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        logger.error("*** NOTICE ***: Water level in the sump is 200mm!")
        logger.error("*** NOTICE ***: HUMAN INTERVENTION REQUIRED: Please add water to the system.")

        print("\n\n*** NOTICE ***: Water level in the sump is 200mm!")
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
        #If the butts pump is on, turn it off.
        butts_pump.disable()

        logger.critical("*** CRITICAL ***: Water level in the sump < 200mm!")
        logger.critical("*** CRITICAL ***: HUMAN INTERVENTION REQUIRED: Please add water to the system.")
        logger.critical("*** INFO ***: The pump won't run dry; it has been temporarily disabled.")

        print("\n\n*** CRITICAL ***: Water level in the sump < 200mm!")
        print("*** CRITICAL ***: HUMAN INTERVENTION REQUIRED: Please add water to the system.")
        print("*** INFO ***: The pump won't run dry; it has been temporarily disabled.")

        #Make sure the main circulation pump is off.
        logger.warning("Disabling the main circulation pump, if it was on...")
        print("Disabling the main circulation pump, if it was on...")

        main_pump.disable()

        logger.critical("Setting reading interval to 15 seconds for super close monitoring...")
        print("Setting reading interval to 15 seconds for super close monitoring...")

        reading_interval = 15

    #Set the reading interval in the thread, and send it down the socket to the peer.
    monitor.set_reading_interval(reading_interval)
    socket.write("Reading Interval: "+str(reading_interval))

    return reading_interval
