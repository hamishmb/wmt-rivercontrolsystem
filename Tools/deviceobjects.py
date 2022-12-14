#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Device classes for the River System Control and Monitoring Software
# Copyright (C) 2017-2022 Wimborne model Town
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
This is the part of the software framework that contains the device, sensor and
probe classes. These represent the devices and probes/sensors that we're
interfacing with. These classes provide a common API to get readings (the get_reading()
method), and also draw the implementation details for how each probe is managed away
from the rest of the program.

.. module:: deviceobjects.py
    :platform: Linux
    :synopsis: The part of the framework that contains the device/probe/sensor classes.

.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>
.. moduleauthor:: Terry Coles <wmt@hadrian-way.co.uk

"""

#Standard Imports.
import time
import sys
import logging

#Import modules.
import config

from Tools import devicemanagement as device_mgmt
from Tools.coretools import rcs_print as print #pylint: disable=redefined-builtin,unused-import

#Use logger here too.
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

for handler in logging.getLogger('River System Control Software').handlers:
    logger.addHandler(handler)

try:
    #Allow us to generate documentation on non-RPi systems.
    from RPi import GPIO                             # GPIO imports and setups
    GPIO.setmode(GPIO.BCM)

except (ImportError, NotImplementedError):
    if not config.TESTING:
        logger.critical("Unable to import RPi.GPIO! Did you mean to use testing mode?")
        logger.critical("Exiting...")
        logging.shutdown()

        sys.exit("Unable to import RPi.GPIO! Did you mean to use testing mode? Exiting...")

    else:
        #Import dummy class.
        from Tools.testingtools import GPIO #pylint: disable=ungrouped-imports

def reconfigure_logger():
    """
    Reconfigures the logging level for this module.
    """

    logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

    for _handler in logging.getLogger('River System Control Software').handlers:
        logger.addHandler(_handler)

class BaseDeviceClass:
    """
    This is a base control/probe/sensor type that defines features common to all
    devices. It isn't meaningful to construct objects of this type, instead
    you should derive from it and build upon it. All other device classes
    defined in this module inherit from this class.

    .. warning::
        Most of the devices that inherit from this class require that you call
        the methods defined here for setup before you can use them. Not doing
        so **WILL** cause problems.

    Documentation for the constructor for objects of type BaseDeviceClass:

    This is essentially an abstract class, but as with BaseMonitorClass,
    the constructor is useful when deriving from this class.

    Args:
        self (BaseDeviceClass):     A self-reference.
                                    Only passed when
                                    helping construct
                                    a subclass.

        _id (str):                  The probe's full ID.
                                    Used to identify the
                                    probe. eg "G4:FS0"

    Usage:
        >>> probe = BaseDeviceClass("myProbe")

        .. note::
            Not useful unless you derive from it.
    """

    # ---------- CONSTRUCTOR ----------
    def __init__(self, _id, _name="<unspecified>"):
        """Constructor as documented above"""
        #Set some semi-private variables.
        #Check the ID is valid.
        if not isinstance(_id, str) \
            or ":" not in _id \
            or len(_id.split(":")) != 2 \
            or _id.split(":")[0] == "" \
            or _id.split(":")[1] == "":

            raise ValueError("Invalid ID: "+str(_id))

        self._id = _id                      #A unique full ID eg "G4:FS0".

        #Check the name is valid.
        if not isinstance(_name, str) \
            or _name == "":

            raise ValueError("Invalid Name: "+str(_name))

        self._name = _name                  #The human-readable name for the probe.
        self._pin = -1                      #Needs to be set/deleted.
        self._pins = []                     #Needs to be set/deleted.
        self._reverse_pins = []             #Needs to be set/deleted.
        self.mgmt_thread = None            #Holds a reference to the management thread, if any.

    # ---------- INFO GETTER METHODS ----------
    def get_device_id(self):
        """
        This method returns this device's device-id eg "FS0".

        Returns:
            str. The device's ID.

        Usage:

            >>> get_device_id()
            >>> "FS1"
        """

        return self._id.split(":")[1]

    def get_site_id(self):
        """
        This method returns this device's site id eg "G4".

        Returns:
            str. The device's site id.

        Usage:

            >>> get_site_id()
            >>> "G3"
        """

        return self._id.split(":")[0]

    def get_id(self):
        """
        This method returns this device's full ID eg "G4:FS0".

        Returns:
            str. The probe's full id.

        Usage:

            >>> an_id = get_id()
        """

        return self._id

    def get_name(self):
        """
        This method returns this device's human-readable name.

        Returns:
            str. The device's name.

        Usage:

            >>> a_name = get_name()
        """
        return self._name

    def has_mgmt_thread(self):
        """
        This method provides a simple way to check if this device has a management thread.

        Returns:
            bool. Whether or not the device has a management thread.

        Usage:

            >>> <BaseDeviceClass>.has_mgmt_thread()
            >>> False
        """
        return self.mgmt_thread is not None

    # ---------- INFO SETTER METHODS ----------
    def set_pins(self, pins, _input=True):
        """
        This method is used to specify the pins this probe will use. This can be a
        single pin, or multiple pins (eg in the case of a magnetic probe). Can also
        be used to specify one or more output pins. Cannot currently specify both
        input and output pins. Uses RPi BCM pin numbers.

        .. note::
            If you are specifying multiple input pins, eg for a Hall Effect Probe, then
            specify the pins for each level in order, from low to high.

        Args:
            pins (int or tuple(int)):        The BCM pin(s) you want to specify to be used
                                             with this probe.

        Named args:
            _input (bool):                   True if the pins are inputs, False if they are
                                             outputs. Default is True if not specified.

        Usage:
            >>> set_pins(15)                            //For single input on
                                                        BCM pin 15.

            OR

            >>> set_pins(15, _input=False)              //For single output
                                                        on BCM pin 15.

            OR

            >>> set_pins(<tuple<int>>)                  //For multiple inputs
                                                        on all listed BCM pins.

            OR

            >>> set_pins(<tuple<int>>, _input=False)    //For multiple outputs
                                                        on all listed BCM pins.
        """

        #Put the int in a list so this works, if there is only one pin.
        if isinstance(pins, int):
            pins = [pins]

        #NOTE: Valid BCM pins range from 2 to 27.
        #Check that the pins specified are valid.
        if not isinstance(pins, list) and \
            not isinstance(pins, tuple):

            raise ValueError("Invalid value for pins: "+str(pins))

        for pin in pins:
            if not isinstance(pin, int) or \
                pin < 2 or \
                pin > 27:

                raise ValueError("Invalid pin(s): "+str(pins))

        self._pins = pins
        self._reverse_pins = pins[::-1]

        #Setup the pins.
        if _input:
            mode = GPIO.IN

        else:
            mode = GPIO.OUT

        #From lowest to highest, inputs.
        for pin in self._pins:
            GPIO.setup(pin, mode)

        #Set self._pin if required.
        if len(self._pins) == 1:
            self._pin = self._pins[0]

# ---------------------------------- MOTOR OBJECTS -----------------------------------------

class Motor(BaseDeviceClass):
    """
    This class is used to represent a motor or pump, for example the butts pump. It is incomplete;
    there isn't currently a way to set motor speed with PWM, but it does at least have a
    way of specifying whether PWM is available, and a pin to use for PWM.

    Documentation for the constructor for objects of type Motor:

    Usage:
        Use the constructor for this class the same way as for BaseDeviceClass.

    .. note::
        Currently this class has no PWM support.

    .. note::
        Upon instantiaton, a Motor object state is (off, no PWM support, no PWM pin).
    """

    # ---------- CONSTRUCTORS ----------
    def __init__(self, _id, _name):
        """This is the constructor, as documented above."""

        #Call the base class constructor.
        BaseDeviceClass.__init__(self, _id, _name)

        #Set some semi-private variables.
        self._state = False                  #Motor is initialised to be off.
        self._supports_pwm = False           #Assume we don't have PWM by default.
        self._pwm_pin = -1                   #Needs to be set.

    # ---------- INFO SETTER METHODS ----------
    def set_pwm_available(self, pwm_available, pwm_pin=-1):
        """
        This method enables/disables PWM support, and allows you to specify the
        PWM pin.

        Args:
            pwm_available (bool):       Specify if PWM is available or not.
                                        True = yes, False = no.

        Named args:
            pwm_pin (int):              Specify the PWM pin. Default = -1.
                                        If you're enabling PWM, you need to
                                        set this.

        Usage:

            >>> set_pwm_available(True, 26)

            OR

            >>> set_pwm_available(False)
        """

        #Check that pwm_available is valid.
        if not isinstance(pwm_available, bool):
            raise ValueError("Invalid value for pwm_available: "+str(pwm_available))

        self._supports_pwm = pwm_available

        #Check that pwm_pin is valid (-1 is also allowed if disabled).
        if (not isinstance(pwm_pin, int) or \
            pwm_pin < 2 or \
            pwm_pin > 27) and \
            pwm_pin != -1:

            raise ValueError("Invalid pin: "+str(pwm_pin))

        #Check that the arguments make sense together.
        if (pwm_available is True and pwm_pin == -1) or \
            (pwm_available is False and pwm_pin != -1):

            raise ValueError("Arguments: "+str(pwm_available)+" and "+str(pwm_pin)
                             + " do not make sense together.")

        self._pwm_pin = pwm_pin

    # ---------- INFO GETTER METHODS ----------
    def get_reading(self):
        """
        This method returns the state of the switch. True = on, False = off.

        .. note::
            No fault checking is done thus far, so the string part of the return value is always
            "OK".

        Returns:
            tuple(bool, str).

            bool: The status of the motor.

                - True  -- On.
                - False -- Off.

            str: Fault checking status.

                - OK -- Everything is fine.

        Usage:
            >>> get_reading()
            >>> (False, OK)
        """

        return self._state, "OK"

    def pwm_supported(self):
        """
        This method returns True if PWM is supported for this motor. Else False.

        Returns:
            bool. True = PWM supported, False = no support.

        Usage:

            >>> pwm_supported()
            >>> False
        """

        return self._supports_pwm

    # ---------- CONTROL METHODS ----------
    def enable(self):
        """
        This method attempts to turn the motor on. Currently, will only return False
        if motor output pin is not set.

        Returns:
            bool. True if successful, False if not.

        Throws:
            RuntimeError if control pin not set.

        Usage:

            >>> enable()
            >>> True
        """

        #Raise RuntimeError if control pin isn't set.
        if self._pin == -1:
            raise RuntimeError("Control pin was not set!")

        #Turn the pin on.
        GPIO.output(self._pin, False)
        self._state = True

        #Log it.
        logger.info("Motor ("+self._name+"): Enabled.")

        return True

    def disable(self):
        """
        This method attempts to turn the motor off. Currently, will only return False
        if motor output pin is not set.

        Returns:
            bool. True if successful, False if not.

        Throws:
            RuntimeError if control pin not set.

        Usage:

            >>> disable()
            >>> True
        """

        #Raise RuntimeError if control pin isn't set.
        if self._pin == -1:
            raise RuntimeError("Control pin was not set!")

        #Turn the pin off.
        GPIO.output(self._pin, True)
        self._state = False

        #Log it.
        logger.info("Motor ("+self._name+"): Disabled.")

        return True

# ---------------------------------- SENSOR OBJECTS -----------------------------------------

class FloatSwitch(BaseDeviceClass):
    """
    This class is used to represent a float switch.

    Documentation for the constructor for objects of type FloatSwitch:

    Usage:
        Use the constructor for this class the same way as for BaseDeviceClass.

    .. note::
        Upon instantiaton, a FloatSwitch object is assumed to be active high.
        This is because they are always pressed down unless the butts are full.
        Hence, if the **hardware** is active low, the **software representation**
        of it must be active high.

    .. note::
        The new float switches that do both high and low are essentially 2-in-1.
        As such, initialise 2 of these classes with the correct pins to interface
        with the new float switches.

    """

    # ---------- CONSTRUCTORS ----------
    def __init__(self, _id, _name):
        """This is the constructor as defined above."""
        #Call the base class constructor.
        BaseDeviceClass.__init__(self, _id, _name)

        #Set some semi-private variables.
        #Actually active low, but active high by default,
        #because always pressed unless butts are full.
        self._active_state = True

    # ---------- INFO SETTER METHODS ----------
    def set_active_state(self, state):
        """
        This method sets the active state for the switch.

        Args:
            State:          The active state for the switch. True for active high, False for
                            active low.

        Usage:

            >>> set_active_state(True)     //Active high.

            OR

            >>> set_active_state(False)    //Active low.
        """

        #Check the state is valid.
        if not isinstance(state, bool):
            raise ValueError("Invalid state: "+str(state))

        self._active_state = state

    # ---------- INFO GETTER METHODS ----------
    def get_active_state(self):
        """
        This method returns the active state of the switch. True = active high, False = active low.

        Usage:
            >>> get_active_state()
            >>> True
        """

        return self._active_state

    def get_reading(self):
        """
        This method returns the state of the switch. True = triggered, False = not triggered.

        .. note::
            The return values from this method are not affected by active state, as long as it
            was set correctly.

        .. note::
            No fault checking is done thus far, so the string part of the return value is always
            "OK".

        Returns:
            tuple(bool, str).

            bool: The status of the switch.

                - True  -- Switch triggered - butts full.
                - False -- Switch not triggered - butts not full.

            str: Fault checking status.

                - OK -- Everything is fine.

        Usage:
            >>> get_reading()
            >>> (False, OK)
        """

        return bool(GPIO.input(self._pin) == self._active_state), "OK"

class HallEffectDevice(BaseDeviceClass):
    """
    This class is used to represent a hall effect device (as in what you may
    find in a water wheel).

    .. note::
        Currently, this class has no facility to convert RPM into a flow rate.
        The data is available but this hasn't been implemented.

    Documentation for the constructor for objects of type HallEffectDevice:

    Usage:
        Use the constructor for this class the same way as for BaseDeviceClass.

    """

    # ---------- CONSTRUCTORS ----------
    def __init__(self, _id, _name):
        """This is the constructor, as documented above."""

        #Call the base class costructor.
        BaseDeviceClass.__init__(self, _id, _name)

        #Set some semi-private variables.
        self._num_detections = 0                  #Internal use only.

    # ---------- PRIVATE METHODS ----------
    def _increment_num_detections(self, channel): #pylint: disable=unused-argument
        """
        PRIVATE, implementation detail.

        Called when a falling edge is detected. Adds 1 to the number of
        falling edges detected.
        """

        self._num_detections += 1

    # ---------- CONTROL METHODS ----------
    def get_reading(self):
        """
        This method returns the rate at which the hall effect device (water
        wheel) is rotating, in RPM. Takes readings for 5 seconds for accuracy,
        and then averages the result.

        .. note::
            Currently no fault checking is performed, so the string part of the return value
            is always "OK".

        Returns:

            tuple(int, str)

            int:
                The RPM of the water wheel.

            str:
                Fault checking status.

                "OK" -- Everything is fine.

        Usage:

            >>> get_reading()
            >>> (50, "OK")

        """
        self._num_detections = 0

        #Automatically call our function when a falling edge is detected.
        GPIO.add_event_detect(self._pin, GPIO.FALLING, callback=self._increment_num_detections)

        time.sleep(5)

        #Stop calling our function.
        GPIO.remove_event_detect(self._pin)

        #Multiply by 12 to get rpm.
        rpm = self._num_detections * 12

        return rpm, "OK"

class HallEffectProbe(BaseDeviceClass):
    """
    This class is used to represent the new type of magnetic probe.  This probe
    encodes the water level as four voltages at 100 mm intervals.  Each of the four voltage
    O/Ps provides levels at one of 100 mm, 25 mm, 50 mm and 75 mm levels and the Interface
    Board converts these voltages to four values, which this class then converts to depth.
    It has higher precision than the old type but only needs 6 wires to carry the signals.

    Documentation for the constructor for objects of type HallEffectProbe:

    Usage:
        >>> probe = deviceobjects.HallEffectProbe(<a_time>, <a_tick>, <an_id>,
        >>>                                       <a_value>, <a_status>)

    """

    # ---------- CONSTRUCTORS ----------
    def __init__(self, _id, _name):
        """This is the constructor, as documented above"""

        #Call the base class constructor.
        BaseDeviceClass.__init__(self, _id, _name)

        #Set some semi-private variables.
        self._current_reading = 0                  #Internal use only.

        self.high_limits = None                    #The high limits to be used with this probe.
        self.low_limits = None                     #The low limits to be used with this probe.
        self.depths = None                         #The multidimensional list of 4 rows or depths.
        self.length = None                         #The number of sensors in each stack.
        self.i2c_address = None                    #The i2c address of the probe.
        self.mgmt_thread = True                   #We do have a management thread.

    def start_thread(self):
        """Start the thread to keep polling the probe."""
        self.mgmt_thread = device_mgmt.ManageHallEffectProbe(self, self.i2c_address)

    def set_address(self, i2c_address):
        """
        This method is used to import the address this probe will use. The calling code must
        already have established these from config.py

        Args:
            i2c_address (int):          The hardware address this probe will use.

        Usage:
            >>> set_address(<int>)
        """

        self.i2c_address = i2c_address

    def set_limits(self, high_limits, low_limits):
        """
        This method is used to import the limits this probe will use. The calling code must
        already have established these from config.py

        Args:
            high_limits (list(float):          The high limits to be used with this probe.
            low_limits (list(float)):          The low limits to be used with this probe.

        Usage:
            >>> set_limits(<list(float)>, <list(float)>)

        """


        #Check the limits are valid.
        #Basic check.
        if not (isinstance(high_limits, (list, tuple))) or \
            not (isinstance(low_limits, (list, tuple))) or \
            len(high_limits) != 10 or \
            len(low_limits) != 10:

            raise ValueError("Invalid limits: "+str(high_limits)+", "+str(low_limits))

        #Advanced checks.
        #Check that all the limits are floats or ints.
        for limits in (high_limits, low_limits):
            for limit in limits:
                if not (isinstance(limit, (float, int))) or \
                    isinstance(limit, bool):

                    raise ValueError("Invalid limits: "+str(high_limits)+", "+str(low_limits))

        #Check that the corresponding limits in low_limits are actually lower.
        for limit in high_limits:
            if not limit > low_limits[high_limits.index(limit)]:
                raise ValueError("Invalid limits: "+str(high_limits)+", "+str(low_limits))

        self.high_limits = high_limits
        self.low_limits = low_limits

    def set_depths(self, depths):
        """
        This method is used to import the depth precision values this probe support. The
        calling code must already have established these from config.py. The depths should be
        in the order: [100s, 25s, 50s, 75s].

        Args:
            depths (list(list(int)):        The multidimensionl list of four rows of depths
                                            to be used with this probe.

        Usage:
            >>> set_limits(<list<list(int)>>)

        """

        #Check the depths are valid.
        #Basic checks.
        for depthlist in depths:
            if not (isinstance(depthlist, (list, tuple))) or \
                depthlist in ((), []) or \
                len(depthlist) != 10 or \
                len(depths) != 4:

                raise ValueError("Invalid depths: "+str(depths))

        #Advanced checks.
        #Check that these are all integers.
        for depthlist in depths:
            for depth in depthlist:
                if not isinstance(depth, int):
                    raise ValueError("Invalid depths: "+str(depths))

        #Check that the hundreds are actually hundreds and so on.
        #Also check that the values are in the right order, eg if we are at 400
        #in the 100s, the corresponding 25 should be 425, the 50 should be 450
        #and so on.
        for depth in depths[0]:
            i = depths[0].index(depth)

            if (not depth % 100 == 0) or \
                depths[1][i] != depth + 25 or \
                depths[2][i] != depth + 50 or \
                depths[3][i] != depth + 75:

                raise ValueError("Invalid depths: "+str(depths))

        self.depths = depths

        #We need to count the number of sensors in the stack, not the number of stacks!
        self.length = len(depths[0])

    def get_limits(self):
        """
        This method returns the limits, in the order: high, low.

        Returns:
            tuple(list(float), list(float))

            OR

            tuple(None, None), if not set.

        Usage:
            >>> get_limits()
        """

        return self.high_limits, self.low_limits

    def get_depths(self):
        """
        This method returns the depth precision values.

        Returns:
            list(list(int)). The depths.

        Usage:
            >>> get_depths()
        """

        return self.depths

    # ---------- CONTROL METHODS ----------
    def get_reading(self):
        """
        This method returns the rate at which the float is bobbing
        about.

        .. note::

            Currently no fault checking is performed, so the string part of the return value
            is always "OK".

        Returns:

            tuple(int, str)

            int:
                The level of the float.

            str:
                Fault checking status.

                "OK" -- Everything is fine.

        Usage:

            >>> get_reading()
            >>> (500, "OK")

        """

        return self._current_reading, "OK"

# ---------------------------------- HYBRID OBJECTS -----------------------------------------
# (Objects that contain both controlled devices and sensors)
class GateValve(BaseDeviceClass):
    def __init__(self, _id, _name):
        """This is the constructor"""
        BaseDeviceClass.__init__(self, _id, _name)

        self.forward_pin = None #The pin to set the motor direction to backwards (opening gate).
        self.reverse_pin = None #The pin to set the motor direction to backwards (closing gate).
        self.clutch_pin = None #The pin to engage the clutch.

        self.pos_tolerance = None #Positional tolerance in %.
        self.max_open = None #Max open value in %.
        self.min_open = None #Min open value in %.

        self.ref_voltage = None #Reference voltage.
        self.i2c_address = None #The hardware address for the A2D (ADC)
        self.mgmt_thread = True                   #We do have a management thread.

    def set_pins(self, pins, _input=False):
        """Wrapper for BaseDeviceClass that also sets forward_pin, reverse_pin, and clutch_pin."""
        if (not isinstance(pins, list) and \
            not isinstance(pins, tuple)) or \
            len(pins) != 3:

            raise ValueError("Invalid value for pins: "+str(pins))

        #Call the BaseDeviceClass method.
        super().set_pins(pins, _input)

        self.forward_pin = pins[0]
        self.reverse_pin = pins[1]
        self.clutch_pin = pins[2]

    def set_pos_tolerance(self, pos_tolerance):
        """
        This method sets the positional tolerance of this valve as a percentage.

        Args:
            pos_tolerance (int). Must be between 1 and 10.

        Usage:
            >>> set_pos_tolerance(5)
        """
        if not isinstance(pos_tolerance, int) or \
            isinstance(pos_tolerance, bool) or \
            pos_tolerance < 1 or \
            pos_tolerance > 10:

            raise ValueError("Invalid value for pos_tolerance: "+str(pos_tolerance))

        self.pos_tolerance = pos_tolerance

    def set_max_open(self, max_open):
        """
        This method sets the maximum percentage the gate valve will open.

        Args:
            max_open (int). The maximum open value of this gate valve.
                            Must be between 90 and 99.

        Usage:

            >>> set_max_open(95)
        """
        if not isinstance(max_open, int) or \
            max_open < 90 or \
            max_open > 99:

            raise ValueError("Invalid value for max_open: "+str(max_open))

        self.max_open = max_open

    def set_min_open(self, min_open):
        """
        This method sets the minimum percentage the gate valve will open.

        Args:
            min_open (int). The minimum open value of this gate valve.
                            Must be between 1 and 10.

        Usage:

            >>> set_min_open(5)
        """
        if not isinstance(min_open, int) or \
            min_open < 1 or \
            min_open > 10:

            raise ValueError("Invalid value for min_open: "+str(min_open))

        self.min_open = min_open

    def set_ref_voltage(self, ref_voltage):
        """
        This method sets the reference voltage of the gate valve.

        Args:
            ref_voltage(float). The reference voltage of this gate valve.

        Usage:

            >>> set_ref_voltage(3.3)
        """
        if not isinstance(ref_voltage, (int, float)) or \
            ref_voltage < 2 or \
            ref_voltage > 5.5:

            raise ValueError("Invalid value for ref_voltage: "+str(ref_voltage))

        self.ref_voltage = ref_voltage

    def set_i2c_address(self, i2c_address):
        """
        This method sets the address of the valve on the i2c bus.

        Args:
            i2c_address(int). The address of this gate valve.

        Usage:

            >>> set_i2c_address(0x48)
        """
        if not isinstance(i2c_address, int):
            raise ValueError("Invalid value for i2c_address: "+str(i2c_address))

        self.i2c_address = i2c_address

    def start_thread(self):
        """Start the thread to manage the thread."""
        self.mgmt_thread = device_mgmt.ManageGateValve(self, self.i2c_address)

    def get_pos_tolerance(self):
        """
        This method returns the positional tolerance of this valve as a percentage.

        Returns:

            int. The percentage tolerance of the valve.

        Usage:

            >>> get_pos_tolerance()
            >>> 5
        """
        return self.pos_tolerance

    def get_max_open(self):
        """
        This method returns the maximum percentage the gate valve will open.

        Returns:

            int. The maximum open value of this gate valve.

        Usage:

            >>> get_max_open()
            >>> 95
        """
        return self.max_open

    def get_min_open(self):
        """
        This method returns the minimum percentage the gate valve will open.

        Returns:

            int. The minimum open value of this gate valve.

        Usage:

            >>> get_ref_voltage()
            >>> 5
        """
        return self.min_open

    def get_ref_voltage(self):
        """
        This method returns the reference voltage of the gate valve.

        Returns:

            float. The reference voltage of this gate valve.

        Usage:

            >>> get_ref_voltage()
            >>> 3.3
        """
        return self.ref_voltage

    def get_requested_position(self):
        """
        This method returns the most recent requested position for the gate valve.

        Returns:

            int. The position (0 - 100).

        Usage:

            >>> get_requested_position()
            >>> 50
        """
        return self.mgmt_thread.get_requested_position()

    # ---------- CONTROL METHODS ----------
    def set_position(self, percentage):
        """
        This method sets the position of the gate valve to the given percentage.

        If a value less than 0 is specified, the position is set to 0 (or any defined minimum
        value - currently 1).

        If a value greater than 100 is specified, the position is set to 100 (or any defined
        maximum value - currently 99).

        Usage:

            >>> set_position(100)

        """
        if isinstance(percentage, bool) \
            or not isinstance(percentage, int):

            raise ValueError("Invalid value for percentage: "+str(percentage))

        #Make sure percentage is between 100 and 0, and adjust it if not.
        percentage = min(percentage, 100)
        percentage = max(percentage, 0)

        self.mgmt_thread.set_position(percentage)

    def get_reading(self):
        """
        This method returns the current position of the gate valve as a percentage.
        0% - fully closed.
        100% - fully open.

        .. note::

            Currently no fault checking is performed, so the string part of the return value
            is always "OK".

        Returns:

            tuple(int, str)

            int:
                The percentage (0 - 100) position of the valve..

            str:
                Fault checking status.

                "OK" -- Everything is fine.

        Usage:

            >>> get_reading()
            >>> (60, "OK")

        """

        return (self.mgmt_thread.get_current_position(), "OK")
