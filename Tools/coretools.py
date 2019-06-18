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
import logging

import config

#Don't ask for a logger name, so this works with both main.py
#and the universal monitor.
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

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
        if not isinstance(reading_tick, int):
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

# -------------------- CONTROL LOGIC FUNCTIONS --------------------
#TODO update the documentation, this is old.
def sumppi_control_logic(sump_reading_obj, butts_reading_obj, butts_float_reading,
                         devices, monitors, sockets, reading_interval):
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
        sump_reading_obj (Reading):     The newest reading we have from
                                        the sump probe.

        butts_reading_obj (Reading):    As above, but for the butts.

        butts_float_reading (Reading):  As above, for the butts float switch.

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

        >>> reading_interval = sumppi_control_logic(<asumpreading>, <abuttsreading>,
        >>>                                     <listofprobes>, <listofmonitors>,
        >>>                                     <listofsockets>, <areadinginterval)

    """

    #Remove the 'mm' from the end of the reading value and convert to int.
    sump_reading = int(sump_reading_obj.get_value().replace("m", ""))
    butts_reading = int(butts_reading_obj.get_value().replace("m", ""))

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
    assert len(devices) > 0

    #Check that the sockets list is not empty.
    assert len(sockets) > 0

    #Check that the reading interval is positive, and greater than 0.
    assert reading_interval > 0

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

        if (butts_reading >= 300):
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

        if (butts_reading >= 300):
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
