#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Sensor classes for the River System Control and Monitoring Software Version 0.9.1
# Copyright (C) 2017 Wimborne model Town
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

#Standard Imports.
import time

import RPi.GPIO as GPIO

#TODO Check that the change to BCM hasn't screwed anything up.
GPIO.setmode(GPIO.BCM)

class BaseDeviceClass: #NOTE: Should this be in coretools?
    # ---------- CONSTRUCTOR ----------
    def __init__(self, Name):
        """
        This is the constructor.
        It is not intended to be used except as part of the initialistion for a derived class.
        """

        #Set some semi-private variables.
        self._name = Name                   #Just a label.
        self._pin = -1                      #Needs to be set/deleted.
        self._pins = []                     #Needs to be set/deleted.
        self._reverse_pins = []                    #Needs to be set/deleted.

    # ---------- INFO SETTER FUNCTIONS ----------
    def set_pins(self, pins, _input=True):
        #FIXME: Check if these pins are already in use.
        #FIXME: If so throw an error. Also check if these pins are valid input/output pins.
        """
        Sets the pins this device will use (from low to high if a resistance probe).
        Usage:

            <Device-Object>.set_pins(tuple pins, bool _input)
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

    # ---------- INFO GETTER FUNCTIONS ----------
    def get_name(self):
        """
        Returns the name of the device this object is representing.
        Usage:

            str <Device-Object>.get_name()
        """

        return self._name

    def get_pins(self):
        """
        Returns the pins for this device (from low to high if a resistance probe).
        Usage:

            tuple <Device-Object>.get_pins()
        """

        return self._pins

class Motor(BaseDeviceClass):
    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """
        This is the constructor.
        Usage:

            <Variable-Name> = Motor(str Name)
        """

        #Call the base class constructor.
        BaseDeviceClass.__init__(self, Name)

        #Set some semi-private variables.
        self._state = False                 #Motor is initialised to be off.
        self._supports_pwm = False       #Assume we don't have PWM by default.
        self._pwm_pin = -1                   #Needs to be set.

    # ---------- INFO SETTER FUNCTIONS ----------
    def set_pwm_available(self, pwm_available, pwm_pin):
        #TODO Hardware check to determine if PWM is avaiable.
        """
        Enables/Disables PWM support.
        Usage:

            <Motor-Object>.set_pwm_available(bool pwm_available, int pwm_pin)
        """

        self._supports_pwm = pwm_available
        self._pwm_pin = pwm_pin

    # ---------- INFO GETTER FUNCTIONS ----------
    def pwm_supported(self):
        """
        Returns True if PWM is supported for this motor. Else False.
        Usage:

            bool <Motor-Object>.pwm_supported()
        """

        return self._supports_pwm

    # ---------- CONTROL FUNCTIONS ----------
    def enable(self):
        """
        Turn the motor on. Returns True if successful, false if not.
        Usage:

            bool <Motor-Object>.enable()
        """

        #Return false if control pin isn't set.
        if self._pin == -1:
            return False

        #Turn the pin on.
        GPIO.output(self._pin, True)

        return True

    def disable(self):
        """
        Turn the motor off. Returns True if successful, false if not.
        Usage:

            bool <Motor-Object>.disable()
        """

        #Return false if control pin isn't set.
        if self._pin == -1:
            return False

        #Turn the pin off.
        GPIO.output(self._pin, False)

        return True

# -------------------- SENSOR PROBES --------------------

class FloatSwitch(BaseDeviceClass):
    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """
        This is the constructor.
        Usage:

            <Variable-Name> = FloatSwitch(string Name)
        """
        #Call the base class constructor.
        BaseDeviceClass.__init__(self, Name)

        #Set some semi-private variables.
        self._active_state = False           #Active low by default.

    # ---------- INFO SETTER FUNCTIONS ----------
    def set_active_state(self, state):
        """
        Sets the active state for the pins. True for active high, False for active low.
        Usage:

            <ResistanceProbe-Object>.set_active_state(bool state)
        """

        self._active_state = state

    # ---------- INFO GETTER FUNCTIONS ----------
    def get_reading(self):
        """
        Returns the state of the switch. True = on, False = off.
        Usage:
            bool <FloatSwitch-Object>.get_reading()
        """

        return bool(GPIO.input(self._pin) == self._active_state), "OK" #TODO Actual fault checking.

class CapacitiveProbe(BaseDeviceClass):
    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """
        This is the constructor.
        Usage:

            <Variable-Name> = CapacitiveProbe(string ProbeName)
        """
        #Call the base class constructor.
        BaseDeviceClass.__init__(self, Name)

        #Set some semi-private variables.
        self._num_detections = 0                #Internal use only.

    # ---------- PRIVATE FUNCTIONS ----------
    def increment_num_detections(self, channel):
        """Called when a falling edge is detected. Adds 1 to the number of falling edges detected"""
        self._num_detections += 1

    # ---------- CONTROL FUNCTIONS ----------
    def get_reading(self):
        """
        Returns the level of water. Takes readings for 5 seconds and then averages the result.
        Usage:

            int <CapacitiveProbe-Object>.get_reading()
        """
        self._num_detections = 0

        #Automatically call our function when a falling edge is detected.
        GPIO.add_event_detect(self._pin, GPIO.FALLING, callback=self.increment_num_detections)

        time.sleep(5)

        #Stop calling our function.
        GPIO.remove_event_detect(self._pin)

        #Use integer divison '//' because it's fast.
        freq = self._num_detections // 5 #Take the mean average over 5 seconds.

        return freq, "OK" #TODO Actual fault checking.

class ResistanceProbe(BaseDeviceClass):
    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """
        This is the constructor.
        Usage:

            <Variable-Name> = ResistanceProbe(string ProbeName)
        """
        #Call the base class constructor.
        BaseDeviceClass.__init__(self, Name)

        #Set some semi-private variables.
        self._active_state = False           #Active low by default.

    # ---------- INFO SETTER FUNCTIONS ----------
    def set_active_state(self, state):
        """
        Sets the active state for the pins. True for active high, False for active low.
        Usage:

            <ResistanceProbe-Object>.set_active_state(bool state)
        """

        self._active_state = state

    # ---------- INFO GETTER FUNCTIONS ----------
    def get_active_state(self):
        """
        Returns the active state for the pins.
        Usage:

            bool <ResistanceProbe-Object>.get_active_state()
        """

        return self._active_state

    # ---------- CONTROL FUNCTIONS ----------
    def get_reading(self):
        """
        Gets the level of the water in the probe.
        Usage:

            (int, string) <ResistanceProbe-Object>.get_reading()
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
            status_text = self.detect_faults(index, status_text)

            #Return the level, assume pin 0 is at 0mm. Also return fault_text
            return index*100, status_text

        #No pins were high.
        return -1, "1111111111"

    def detect_faults(self, highest_active_pin, status_text):
        """
        Checks for faults in the sensor.
        Isn't capable of finding all faults without another sensor to compare against.
        Usage:

            bool <ResistanceProbe-Object>.detect_faults(int highest_active_pin)
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
    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """
        This is the constructor.
        Usage:

            <Variable-Name> = HallEffectDevice(string DeviceName)
        """

        #Call the base class costructor.
        BaseDeviceClass.__init__(self, Name)

        #Set some semi-private variables.
        self._num_detections = 0                  #Internal use only.

    # ---------- PRIVATE FUNCTIONS ----------
    def increment_num_detections(self, channel):
        """Called when a falling edge is detected. Adds 1 to the number of falling edges detected"""
        self._num_detections += 1

    # ---------- CONTROL FUNCTIONS ----------
    def get_reading(self):
        """
        Returns the rate at with the hall effect device is rotating.
        Takes readings for 5 seconds and then averages the result.
        Usage:

            int <HallEffectDevice-Object>.get_reading()
        """
        self._num_detections = 0

        #Automatically call our function when a falling edge is detected.
        GPIO.add_event_detect(self._pin, GPIO.FALLING, callback=self.increment_num_detections)

        time.sleep(5)

        #Stop calling our function.
        GPIO.remove_event_detect(self._pin)

        #Use integer divison '//' because it's fast.
        revs_per_5_seconds = self._num_detections // 5 #Take the mean average over 5 seconds.

        #Then multiply by 12 to get rpm.
        rpm = revs_per_5_seconds * 12

        return rpm, "OK" #TODO Actual fault checking.

class HallEffectProbe(BaseDeviceClass):
    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """
        This is the constructor.
        Usage:

            <Variable-Name> = HallEffectDevice(string DeviceName)
        """

        #Call the base class costructor.
        BaseDeviceClass.__init__(self, Name)

        #Set some semi-private variables.
        self._current_reading = 0                  #Internal use only.
        self._post_init_called = False             #Internal use only.

    def post_init(self):
        """Automatically call our functions when a falling edge is detected on each pin."""
        GPIO.add_event_detect(self._pins[0], GPIO.FALLING, callback=self.level0)
        GPIO.add_event_detect(self._pins[1], GPIO.FALLING, callback=self.level1)
        GPIO.add_event_detect(self._pins[2], GPIO.FALLING, callback=self.level2)
        GPIO.add_event_detect(self._pins[3], GPIO.FALLING, callback=self.level3)
        GPIO.add_event_detect(self._pins[4], GPIO.FALLING, callback=self.level4)
        GPIO.add_event_detect(self._pins[5], GPIO.FALLING, callback=self.level5)
        GPIO.add_event_detect(self._pins[6], GPIO.FALLING, callback=self.level6)
        GPIO.add_event_detect(self._pins[7], GPIO.FALLING, callback=self.level7)
        GPIO.add_event_detect(self._pins[8], GPIO.FALLING, callback=self.level8)
        GPIO.add_event_detect(self._pins[9], GPIO.FALLING, callback=self.level9)

        self._post_init_called = True

    # ---------- PRIVATE FUNCTIONS ----------
    def level0(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 0

    def level1(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 100

    def level2(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 200

    def level3(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 300

    def level4(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 400

    def level5(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 500

    def level6(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 600

    def level7(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 700

    def level8(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 800

    def level9(self, channel):
        """Called when a falling edge is detected. Sets current reading to relevant level"""
        self._current_reading = 900

    # ---------- CONTROL FUNCTIONS ----------
    def get_reading(self):
        """
        Returns the level at which the magnet is bobbing about at.
        """
        if not self._post_init_called:
            self.post_init()

        return self._current_reading, "OK" #TODO Actual fault checking.
