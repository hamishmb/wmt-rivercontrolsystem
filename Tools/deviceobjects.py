#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Device classes for the River System Control and Monitoring Software Version 0.9.2
# Copyright (C) 2017-2019 Wimborne model Town
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
This is the part of the software framework that contains the control, sensor and
probe classes. These represent the control devices and probes/sensors that we're
interfacing with. These classes provide a common API to get readings (the get_reading()
method), and also draw the implementation details for how each probe is managed away
from the rest of the program.

.. module:: deviceobjects.py
    :platform: Linux
    :synopsis: The part of the framework that contains the control/probe/sensor classes.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk> and Terry Coles <WMT@hadrian-way.co.uk

"""

#Standard Imports.
import threading
import time
import logging

#Import modules.
from . import coretools as core_tools

try:
    #Allow us to generate documentation on non-RPi systems.
    import RPi.GPIO as GPIO                             # GPIO imports and setups
    GPIO.setmode(GPIO.BCM)

#    import board                                        # Imports for A/D Converter
#    import busio
#    import adafruit_ads1x15.ads1015 as ADS
#    from adafruit_ads1x15.analog_in import AnalogIn

#    i2c = busio.I2C(board.SCL, board.SDA)               # Create the I2C bus

#    ads = ADS.ADS1015(i2c)                              # Create the ADC object using the I2C bus

except ImportError:
    pass

VERSION = "0.9.2"

#Use logger here too.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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

        _id (string):                The probe's full ID.
                                    Used to identify the
                                    probe. eg "G4:FS0"

    Usage:
        >>> probe = BaseDeviceClass("myProbe")

        .. note::
            Not useful unless you derive from it.
    """

    # ---------- CONSTRUCTOR ----------
    def __init__(self, _id):
        """Constructor as documented above"""
        #Set some semi-private variables.
        self._id = _id                      #A unique full ID eg "G4:FS0".
        self._pin = -1                      #Needs to be set/deleted.
        self._pins = []                     #Needs to be set/deleted.
        self._reverse_pins = []             #Needs to be set/deleted.

    # ---------- INFO GETTER METHODS ----------
    def get_device_id(self):
        """
        This method returns this devices' device-id eg "FS0".

        Returns:
            string. The devices' ID.

        Usage:

            >>> a_name = <Device-Object>.get_device_id()
        """

        return self._id.split(":")[1]

    def get_system_id(self):
        """
        This method returns this devices' system-id eg "G4".

        Returns:
            string. The prob's system id.

        Usage:

            >>> a_name = <Device-Object>.get_system_id()
        """

        return self._id.split(":")[0]

    def get_id(self):
        """
        This method returns this devices' full ID eg "G4:FS0".

        Returns:
            string. The probe's full id.

        Usage:

            >>> a_name = <Device-Object>.get_id()
        """

        return self._id

    # ---------- INFO SETTER METHODS ----------
    def set_pins(self, pins, _input=True):
        #FIXME: Check if these pins are already in use.
        #FIXME: If so throw an error. Also check if these pins are valid input/output pins.
        #TODO?: Currently cannot specify both input and output pins.
        """
        This method is used to specify the pins this probe will use. This can be a
        single pin, or multiple pins (eg in the case of a magnetic probe). Can also
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
        GPIO.output(self._pin, False)

        #Log it.
        logger.info("Motor "+self._id+": Enabled.")

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
        GPIO.output(self._pin, True)

        #Log it.
        logger.info("Motor "+self._id+": Disabled.")

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
    This class is used to represent a magnetic probe of the old type that sets 10 pins to represent
    the level; one pin for each level.  It is now obsolecent and so this class
    will ultimately be removed.

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
        logging.debug(self._id+" 0mm level detected.")

    def _level1(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 100
        logging.debug(self._id+" 100mm level detected.")

    def _level2(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 200
        logging.debug(self._id+" 200mm level detected.")

    def _level3(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 300
        logging.debug(self._id+" 300mm level detected.")

    def _level4(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 400
        logging.debug(self._id+" 400mm level detected.")

    def _level5(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 500
        logging.debug(self._id+" 500mm level detected.")

    def _level6(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 600
        logging.debug(self._id+" 600mm level detected.")

    def _level7(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 700
        logging.debug(self._id+" 700mm level detected.")

    def _level8(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 800
        logging.debug(self._id+" 800mm level detected.")

    def _level9(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 900
        logging.debug(self._id+" 900mm level detected.")

    # ---------- CONTROL METHODS ----------
    def get_reading(self):
        """
        This method returns the rate at which the float is bobbing
        about.

        .. note::universal_monitor

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

class HallEffectProbe2(BaseDeviceClass, threading.Thread):
    """
    This class is used to represent the new type of magnetic probe.  This probe
    encodes the water level as four voltages at 100 mm intervals.  Each of the four voltage
    O/Ps provides levels at one of 100 mm, 25 mm, 50 mm and 75 mm levels and the Interface
    Board converts these voltages to four values, which this class then converts to depth.
    It has higher precision than the old type but only needs 6 wires to carry the signals.

    Documentation for the constructor for objects of type HallEffectProbe2:

    Usage:
        >>> probe = deviceobjects.HallEffectProbe2(<a_time>, <a_tick>, <an_id>, <a_value>, <a_status>)

    """

    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """This is the constructor, as documented above"""

        #Call the base class constructor.
        BaseDeviceClass.__init__(self, Name)

        #Initialise the thread.
        threading.Thread.__init__(self)

        #Set some semi-private variables.
        self._current_reading = 0                  #Internal use only.
        self._post_init_called = False             #Internal use only.

        # Create four single-ended inputs on channels 0 to 3
        self.chan0 = 2.42 #AnalogIn(ads, ADS.P0)
        self.chan1 = 2.42 #AnalogIn(ads, ADS.P1)
        self.chan2 = 2.42 #AnalogIn(ads, ADS.P2)
        self.chan3 = 2.42 #AnalogIn(ads, ADS.P3)

    def start_thread(self):
        """Start the thread to keep polling the probe."""
        self.start()

    def set_limits(self, high_limits, low_limits):
        """
        This method is used to import the limits this probe will use. The calling code must
        already have established these from config.py

        Args:
            high_limits (list(float):          The high limits to be used with this probe.
            low_limits (list(float)):          The high limits to be used with this probe.

        Usage:
            >>> <Device-Object>.set_limits(<list(float)>, <list(float)>)

        """

        #NB: Removed the []s around these - we don't want a list with a tuple
        #inside!
        self.high_limits = high_limits
        self.low_limits = low_limits

    def set_depths(self, depths):
        """
        This method is used to import the depth precision values this probe support. The
        calling code must already have established these from config.py

        Args:
            depths (list(int):              The multidimensionl list of four rows of depths
                                            to be used with this probe.

        Usage:
            >>> <Device-Object>.set_limits(<list(int)>)

        """

        #NB: Removed the []s around this too - we don't want a list with a tuple
        #inside!
        self.depths = depths

        #We need to count the number of sensors in the stack, not the number of stacks!
        self.length = len(depths[0])

    def get_compensated_probe_voltages(self):
        """This function performs the measurement of the four voltages and applies the compensation
        to take out errors caused by the varying output impedance of the probe
        """
         # Initialise Lists and variables to hold the working values in each column
        Vmeas = list()                                      # Actual voltages
        Vcomp = list()                                      # Compensated values
        result = list()                                                # Measured value and column

        # Prepare Vcomp to hold 4 values (pre-populate to avoid errors).
        for i in range(0, 4):
            Vcomp.append(0)
        
        # Measure the voltage in each chain
        Vmeas.append(self.chan0.voltage)
        Vmeas.append(self.chan1.voltage)
        Vmeas.append(self.chan2.voltage)
        Vmeas.append(self.chan3.voltage)

        # Find the minimum value
        Vmin = min(Vmeas)

        # Find the column that the minimum value is in
        min_column = Vmeas.index(min(Vmeas))
        print("Column containing the minimum value = " + str(min_column))

        # Work out the average of the three highest measurements (thus ignoring the 'dipped' channel.
        Vtot = Vmeas[0] + Vmeas[1] + Vmeas[2] + Vmeas[3]
        Vav = (Vtot - Vmin)/3

        # Calculate the compensated value for each channel.
        if Vmin >= 3.0:
            # Take a shortcut when the magnet is between sensors
            Vcomp[0] = Vcomp[1] = Vcomp[2] = Vcomp[3] = Vav - Vmin

        else:
            if min_column == 0:
                Vcomp[min_column] = Vav - Vmin
            elif min_column == 1:
                Vcomp[min_column] = Vav - Vmin
            elif min_column == 2:
                Vcomp[min_column] = Vav - Vmin
            elif min_column == 3:
                Vcomp[min_column] = Vav - Vmin
            else:
                Vcomp[min_column] = Vav

        print("Dip Value = " + str(Vcomp[min_column]))

        result = Vcomp, min_column

        return result

    def test_levels(self):
        count = 0
        level = 1000                                              # Value to return

        while count < self.length:
            print("")
            print("Count Number = " + str(count))

            Vcomp, min_column = self.get_compensated_probe_voltages()

            # Now test the channel with the dip to see if any of the sensors are triggered
            if ((Vcomp[min_column] <= self.high_limits[count]) and (Vcomp[min_column] >= self.low_limits[count])):
                level = self.depths[min_column][count]
                print("Depth = " + str(level))

            else:
                print("Between Sensors at this Depth")

            count += 1

        return level

    def run(self):
        """The main body of the monitor thread for this probe"""
        #FIXME We need a way of exiting from this cleanly on
        #program shutdown.

        while True:
            new_reading = self.test_levels()

            if new_reading == 1000:
                print("No Sensors Triggered")

            else:
                print("Depth = " + str(new_reading))

                #Only update this if we got a meaningful reading from the probe.
                #Aka at least 1 sensor triggered.
                self._current_reading = new_reading

            time.sleep(0.5)

    # ---------- CONTROL METHODS ----------
    def get_reading(self):
        """
        This method returns the rate at which the float is bobbing
        about.

        .. note::universal_monitor

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

            >>> <HallEffectProbe2-Object>.get_reading()
            >>> (500, "OK")

        """

        return self._current_reading, "OK" #TODO Actual fault checking.

# ---------------------------------- HYBRID OBJECTS -----------------------------------------
# (Objects that contain both controlled devices and sendors
class GateValve(BaseDeviceClass):
    def __init__(self, _id, pins, pos_tolerance, max_open, min_open, ref_voltage):
        """This is the constructor"""
        #NB: ID will be repeated eg "V4:V4" so that BaseDeviceClass and the
        #rest of the software functions properly.
        BaseDeviceClass.__init__(self, _id+":"+_id)

        #Set all pins as outputs.
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)

        #Start the thread so we can control the gate valve.
        self.control_thread = core_tools.ActuatorPosition(pins, pos_tolerance, max_open, min_open,
                                                          ref_voltage)

    def set_position(self, percentage):
        """
        This method sets the position of the gate valve to the given percentage.

        If a value less than 0 is specified, the position is set to 0 (or any defined minimum
        value - currently 1).

        If a value greater than 100 is specified, the position is set to 100 (or any defined
        maximum value - currently 99).

        Usage:

            >>> <GateValve-Object>.set_position(100)

        """

        self.control_thread.set_position(percentage)

    def get_reading(self):
        """
        This method returns the current position of the gate valve as a percentage.
        0% - fully closed.
        100% - fully open.

        .. note::universal_monitor

            Currently no fault checking is performed, so the string part of the return value
            is always "OK".

        Returns:

            tuple(int, string)

            int:
                The percentage (0 - 100) position of the valve..

            string:
                Fault checking status.

                "OK" -- Everything is fine.

        Usage:

            >>> <GateValve-Object>.get_reading()
            >>> (60, "OK")

        """

        return (self.control_thread.get_position(), "OK")
