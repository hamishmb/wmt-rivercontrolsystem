#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Sensor classes for the River System Control and Monitoring Software Version 0.9.2
# Copyright (C) 2017-2018 Wimborne model Town
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

#TODO: Throw errors if setup hasn't been completed properly.

"""
This is the part of the software framework that contains the
sensor/probe classes. These represent the probes/sensors that
we're interfacing with. These classes provide a common API to
get readings (the get_reading() method), and also draw the
implementation details for how each probe is managed away from
the rest of the program.

.. module:: sensorobjects.py
    :platform: Linux
    :synopsis: The part of the framework that contains the probe/sensor classes.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>

"""

#Standard Imports.
import time
import logging

try:
    #Allow us to generate documentation on non-RPi systems.
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)

except ImportError:
    pass

VERSION = "0.9.2"

#Use logger here too.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class BaseDeviceClass:
    """
    This is a base probe/sensor type that defines features common to all
    probes. It isn't meaningful to construct objects of this type, instead
    you should derive from it and build upon it. All other device classes
    defined in this module inherit from this class.

    .. warning::
        Most of the probes that inherit from this class require that you call
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

        Name (string):              The probe's name.
                                    Can be used in
                                    logging messages
                                    for extra clarity.

    Usage:
        >>> probe = BaseDeivceClass("myProbe")

        .. note::
            Not useful unless you derive from it.
    """

    # ---------- CONSTRUCTOR ----------
    def __init__(self, Name):
        """Constructor as documented above"""
        #Set some semi-private variables.
        self._name = Name                   #Just a label.
        self._pin = -1                      #Needs to be set/deleted.
        self._pins = []                     #Needs to be set/deleted.
        self._reverse_pins = []             #Needs to be set/deleted.

    # ---------- INFO SETTER METHODS ----------
    def set_pins(self, pins, _input=True):
        #FIXME: Check if these pins are already in use.
        #FIXME: If so throw an error. Also check if these pins are valid input/output pins.
        #TODO?: Currently cannot specify both input and output pins.
        """
        This method is used to specify the pins this probe will use. This can be a
        single pin, or multiple pins (eg in the case of a resistance probe). Can also
        be used to specify one or more output pins. Cannot currently specify both
        input and output pins. Uses RPi BCM pins.

        .. note::
            If you are specifying multiple input pins, eg for a Hall Effect Probe, then
            specify the pins for each level in order, from low to high.

        Args:
            pins (int or tuple(int)):        The BCM pin(s) you want to specify to be used
                                             with this probe.

        KWargs:
            _input (bool):                   True if the pins are inputs, False if they are
                                             outputs. Default is True if not specified.

        Usage:
            >>> <Device-Object>.set_pins(15)                            //For single input on
                                                                        BCM pin 15.

            OR

            >>> <Device-Object>.set_pins(15, _input=False)              //For single output
                                                                        on BCM pin 15.

            OR

            >>> <Device-Object>.set_pins(<tuple<int>>)                  //For multiple inputs
                                                                        on all listed BCM pins.

            OR

            >>> <Device-Object>.set_pins(<tuple<int>>, _input=False)    //For multiple outputs
                                                                        on all listed BCM pins.
        """

        #Put the int in a list so this works.
        if isinstance(pins, int):
            pins = [pins]

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

    # ---------- INFO GETTER METHODS ----------
    def get_name(self):
        """
        This method returns this object's name.

        Returns:
            string. The object's name.

        Usage:

            >>> a_name = <Device-Object>.get_name()
        """

        return self._name

    def get_pins(self):
        """
        This method returns this object's BCM pin numbers.

        Returns:
            tuple. The BCM pins.

        Usage:

            >>> my_pins = <Device-Object>.get_pins()
        """

        return self._pins

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
    def __init__(self, Name):
        """This is the constructor, as documented above."""

        #Call the base class constructor.
        BaseDeviceClass.__init__(self, Name)

        #Set some semi-private variables.
        self._state = False                  #Motor is initialised to be off.
        self._supports_pwm = False           #Assume we don't have PWM by default.
        self._pwm_pin = -1                   #Needs to be set.

    # ---------- INFO SETTER METHODS ----------
    def set_pwm_available(self, pwm_available, pwm_pin=-1):
        #TODO Hardware check to determine if PWM is available.
        #TODO If PWM available, check if PWM pin is valid and not in use.
        """
        This method enables/disables PWM support, and allows you to specify the
        PWM pin.

        Args:
            pwm_available (bool):       Specify if PWM is available or not.
                                        True = yes, False = no.

        KWargs:
            pwm_pin (int):              Specify the PWM pin. Default = -1.
                                        If you're enabling PWM, you need to
                                        set this.

        Usage:

            >>> <Motor-Object>.set_pwm_available(True, 26)

            OR

            >>> <Motor-Object>.set_pwm_available(False)
        """

        self._supports_pwm = pwm_available
        self._pwm_pin = pwm_pin

    # ---------- INFO GETTER METHODS ----------
    def pwm_supported(self):
        """
        This method returns True if PWM is supported for this motor. Else False.

        Returns:
            bool. True = PWM supported, False = no support.

        Usage:

            >>> is_pwm_supported = <Motor-Object>.pwm_supported()
        """

        return self._supports_pwm

    # ---------- CONTROL METHODS ----------
    def enable(self):
        """
        This method attempts to turn the motor on. Currently, will only return False
        if motor output pin is not set.

        Returns:
            bool. True if successful, False if not.

        Usage:

            >>> <Motor-Object>.enable()
            >>> True
        """

        #Return false if control pin isn't set.
        if self._pin == -1:
            return False

        #Turn the pin on.
        GPIO.output(self._pin, True)

        #Log it.
        logger.info("Motor "+self._name+": Enabled.")

        return True

    def disable(self):
        """
        This method attempts to turn the motor off. Currently, will only return False
        if motor output pin is not set.

        Returns:
            bool. True if successful, False if not.

        Usage:

            >>> <Motor-Object>.disable()
            >>> True
        """

        #Return false if control pin isn't set.
        if self._pin == -1:
            return False

        #Turn the pin off.
        GPIO.output(self._pin, False)

        #Log it.
        logger.info("Motor "+self._name+": Disabled.")

        return True

# -------------------- SENSOR PROBES --------------------

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
    """

    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """This is the constructor as defined above."""
        #Call the base class constructor.
        BaseDeviceClass.__init__(self, Name)

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

            >>> <FloatSwitch-Object>.set_active_state(True)     //Active high.

            OR

            >>> <FloatSwitch-Object>.set_active_state(False)    //Active low.
        """

        self._active_state = state

    # ---------- INFO GETTER METHODS ----------
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
            tuple(bool, string).

            bool: The status of the switch.

                - True  -- Switch triggered - butts full.
                - False -- Switch not triggered - butts not full.

            string: Fault checking status.

                - OK -- Everything is fine.

        Usage:
            >>> <FloatSwitch-Object>.get_reading()
            >>> (False, OK)
        """

        return bool(GPIO.input(self._pin) == self._active_state), "OK" #TODO Actual fault checking.

class CapacitiveProbe(BaseDeviceClass):
    """
    This class is used to represent a capacitive probe.

    Documentation for the constructor for objects of type CapacitiveProbe:

    Usage:
        Use the constructor for this class the same way as for BaseDeviceClass.
    """

    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """This is the constructor, as documented above."""
        #Call the base class constructor.
        BaseDeviceClass.__init__(self, Name)

        #Set some semi-private variables.
        self._num_detections = 0                #Internal use only.

    # ---------- PRIVATE METHODS ----------
    def _increment_num_detections(self, channel):
        """
        PRIVATE, implementation detail.

        Called when a falling edge is detected. Adds 1 to the number of falling edges detected
        """

        self._num_detections += 1

    # ---------- CONTROL METHODS ----------
    def get_reading(self):
        """
        This method returns the level of water. Takes readings for 5 seconds for accuracy,
        then averages the result.

        .. warning::
            Currently returns the frequency rather than a level in mm, because our
            prototypes haven't yet advanced to the point where we can map frequency to
            mm.

        .. note::
            Currently no fault checking is performed, so the string part of the return value
            is always "OK".

        Returns:
            tuple(int, string).

            int:
                The frequency, in Hz.

            string:
                The fault checking status.

                OK -- Everything is fine.

        Usage:

            int <CapacitiveProbe-Object>.get_reading()
        """

        self._num_detections = 0

        #Automatically call our function when a falling edge is detected.
        GPIO.add_event_detect(self._pin, GPIO.FALLING, callback=self._increment_num_detections)

        time.sleep(5)

        #Stop calling our function.
        GPIO.remove_event_detect(self._pin)

        #Use integer divison '//' because it's fast.
        freq = self._num_detections // 5 #Take the mean average over 5 seconds.

        return freq, "OK" #TODO Actual fault checking.

class ResistanceProbe(BaseDeviceClass):
    """
    This class is used to represent a resistance probe.

    Documentation for the constructor for objects of type ResistanceProbe:

    Usage:
        Use the constructor for this class the same way as for BaseDeviceClass.

    .. note::
        Upon instantiation, a ResiatanceProbe object is assumed to be active low.
    """

    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """This is the constructor, as dcumented above."""
        #Call the base class constructor.
        BaseDeviceClass.__init__(self, Name)

        #Set some semi-private variables.
        self._active_state = False           #Active low by default.

    # ---------- INFO SETTER METHODS ----------
    def set_active_state(self, state):
        """
        This method sets the active state for the pins.

        Args:
            State:          The active state for the pins. True for active high, False for
                            active low.

        Usage:

            >>> <ResistanceProbe-Object>.set_active_state(True)     //Active high.

            OR

            >>> <ResistanceProbe-Object>.set_active_state(False)    //Active low.
        """

        self._active_state = state

    # ---------- INFO GETTER METHODS ----------
    def get_active_state(self):
        """
        This method returns the active state for the pins.

        Returns:
            bool. The active state.

                True  -- Active high.
                False -- Active low.

        Usage:

            >>> <ResistanceProbe-Object>.get_active_state()
            >>> False

        """

        return self._active_state

    # ---------- CONTROL METHODS ----------
    def get_reading(self):
        """
        This method gets the level of the water in the probe. It also does basic
        fault checking and reports back if any faults were found.

        Returns:
            tuple(int, string).

            int:
                The level of water in the probe, in mm.

            string:
                The fault checking status.

                Pin states for debugging eg "1111111111 ",
                and message if any fault was detected.

                Examples:

                    1110000000                  -- Fine, 200mm.
                    1111110000                  -- Fine, 500mm.
                    1110011110 FAULT DETECTED   -- Bad; could be anything, but probably 900mm.

        .. warning::
            We **CANNOT** detect all faults in this manner. For example, if the pin states were:

                1110000000

            The level could actually be 500mm, instead of 200mm, but the 300, 400 and 500mm
            sensors could be broken. Essentially, extra checks based on history and the
            readings from other sensors need to be performed.

        Usage:

            >>> <ResistanceProbe-Object>.get_reading()
            >>> (300, 1111000000)

        """

        for pin in self._reverse_pins:
            #Ignore pins until we find one that is in the active state.
            if GPIO.input(pin) != self._active_state:
                continue

            #This pin must be active.
            index = self._pins.index(pin)

            #Log the states of all the pins.
            status_text = ""

            for pin in self._pins:
                status_text += str(GPIO.input(pin))

            #Check for faults.
            status_text = self._detect_faults(index, status_text)

            #Return the level, assume pin 0 is at 0mm. Also return fault_text
            return index*100, status_text

        #No pins were high.
        return -1, "1111111111"

    def _detect_faults(self, highest_active_pin, status_text):
        """
        PRIVATE, implementation detail.

        Checks for faults in the probe. Isn't capable of finding all faults,
        because it doesn't use data from past readings or from other probes;
        that would be done elsewhere.

        Usage:

            >>> <ResistanceProbe-Object>.detect_faults(int highest_active_pin, status_text)
            >>> <status_text> + " FAULT DETECTED"
        """

        #Must convert string to int first, because any string except "" evals to boolean True.
        fault_text = ""

        #All pins before this one should be active.
        for pin in status_text[:highest_active_pin]:
            if bool(int(pin)) != self._active_state:
                fault_text = "FAULT DETECTED"

        #All pins after this one should be inactive.
        for pin in status_text[highest_active_pin+1:]:
            if bool(int(pin)) == self._active_state:
                fault_text = "FAULT DETECTED"

        return status_text+" "+fault_text

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
    def __init__(self, Name):
        """This is the constructor, as documented above."""

        #Call the base class costructor.
        BaseDeviceClass.__init__(self, Name)

        #Set some semi-private variables.
        self._num_detections = 0                  #Internal use only.

    # ---------- PRIVATE METHODS ----------
    def _increment_num_detections(self, channel):
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

            tuple(int, string)

            int:
                The RPM of the water wheel.

            string:
                Fault checking status.

                "OK" -- Everything is fine.

        Usage:

            >>> <HallEffectDevice-Object>.get_reading()
            >>> (50, "OK")

        """
        self._num_detections = 0

        #Automatically call our function when a falling edge is detected.
        GPIO.add_event_detect(self._pin, GPIO.FALLING, callback=self._increment_num_detections)

        time.sleep(5)

        #Stop calling our function.
        GPIO.remove_event_detect(self._pin)

        #Use integer divison '//' because it's fast.
        revs_per_5_seconds = self._num_detections // 5 #Take the mean average over 5 seconds.

        #Then multiply by 12 to get rpm.
        rpm = revs_per_5_seconds * 12

        return rpm, "OK" #TODO Actual fault checking.

class HallEffectProbe(BaseDeviceClass):
    """
    This class is used to represent a magnetic probe.

    Documentation for the constructor for objects of type HallEffectProbe:

    Usage:
        Use the constructor for this class the same way as for BaseDeviceClass.

    """

    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """This is the constructor, as documented above"""

        #Call the base class constructor.
        BaseDeviceClass.__init__(self, Name)

        #Set some semi-private variables.
        self._current_reading = 0                  #Internal use only.
        self._post_init_called = False             #Internal use only.

    # ---------- PRIVATE METHODS ----------
    def _post_init(self):
        """
        Automatically call our methods when a falling edge is detected on each pin.

        Not done in __init__ because pins aren't defined at that point.
        """

        GPIO.add_event_detect(self._pins[0], GPIO.FALLING, callback=self._level0)
        GPIO.add_event_detect(self._pins[1], GPIO.FALLING, callback=self._level1)
        GPIO.add_event_detect(self._pins[2], GPIO.FALLING, callback=self._level2)
        GPIO.add_event_detect(self._pins[3], GPIO.FALLING, callback=self._level3)
        GPIO.add_event_detect(self._pins[4], GPIO.FALLING, callback=self._level4)
        GPIO.add_event_detect(self._pins[5], GPIO.FALLING, callback=self._level5)
        GPIO.add_event_detect(self._pins[6], GPIO.FALLING, callback=self._level6)
        GPIO.add_event_detect(self._pins[7], GPIO.FALLING, callback=self._level7)
        GPIO.add_event_detect(self._pins[8], GPIO.FALLING, callback=self._level8)
        GPIO.add_event_detect(self._pins[9], GPIO.FALLING, callback=self._level9)

        self._post_init_called = True

    def _level0(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 0

    def _level1(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 100

    def _level2(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 200

    def _level3(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 300

    def _level4(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 400

    def _level5(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 500

    def _level6(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 600

    def _level7(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 700

    def _level8(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 800

    def _level9(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 900

    # ---------- CONTROL METHODS ----------
    def get_reading(self):
        """
        This method returns the rate at which the float is bobbing
        about.

        .. note::

            Currently no fault checking is performed, so the string part of the return value
            is always "OK".

        Returns:

            tuple(int, string)

            int:
                The level of the float.

            string:
                Fault checking status.

                "OK" -- Everything is fine.

        Usage:

            >>> <HallEffectProbe-Object>.get_reading()
            >>> (500, "OK")

        """
        if not self._post_init_called:
            self._post_init()

        return self._current_reading, "OK" #TODO Actual fault checking.
