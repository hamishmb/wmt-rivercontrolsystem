#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Device management classes for the River System Control and Monitoring Software
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

#pylint: disable=logging-not-lazy
#
#Reason (logging-not-lazy): Harder to understand the logging statements that way.

#TODO: Throw errors if setup hasn't been completed properly.

"""
This is the part of the software framework that contains classes to help manage the device objects.
These take the form of management threads to separate coordination of each of these
more complicated devices, from the classes that represent the devices themselves.

.. module:: deviceobjects.py
    :platform: Linux
    :synopsis: The part of the framework that contains the control/probe/sensor classes.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk> and Terry Coles <WMT@hadrian-way.co.uk

"""

import traceback
import threading
import time
import logging

try:
    #Allow us to generate documentation on non-RPi systems.
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)

    #Setup for ADS1115 (A2D converter).
    import board
    import busio

    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn

    # Create the I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)

    # Create the ADC object using the I2C bus
    ads = ADS.ADS1115(i2c)

except ImportError:
    #Occurs when generating documentation on a non-pi system with Sphinx.
    print("CoreTools: ImportError: Are you generating documentation?")

except NotImplementedError:
    #Occurs when importing busio on Raspberry Pi 1 B+ for some reason.
    print("CoreTools: NotImplementedError: Testing environment?")

except ValueError:
    #Occurs when no I2C device is present.
    print("CoreTools: ValueError: No I2C device found! Testing environment?")

#Don't ask for a logger name, so this works with both main.py
#and the universal monitor.
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

class ManageGateValve(threading.Thread):
    """
    This class is used to energise and position the Actuator Motor that drives a Gate Valve
    to control the flow of water in the system.

    Documentation for the constructor for objects of type ManageGateValve:

    Usage:
        Use the constructor for this class the same way as for BaseDeviceClass.

    """

    #FIXME The documentation for this constructor is wrong -
    #there are extra arguments that we need to explain in the docstring.
    def __init__(self, pins, pos_tolerance, max_open, min_open, ref_voltage):
        """The constructor, set up some basic threading stuff."""
        #The pin to set the motor direction to forwards (opening gate).
        self.forward_pin = pins[0]

        #The pin to set the motor direction to backwards (closing gate).
        self.reverse_pin = pins[1]

        #The pin to engage the clutch.
        self.clutch_pin = pins[2]

        #Positional Tolerance in percent
        self.pos_tolerance = pos_tolerance

        #Upper limit of valve position in percent
        self.max_open = max_open

        #Lower limit of valve position in percent
        self.min_open = min_open

        #Voltage at the top of the position pot
        self.ref_voltage = ref_voltage
        self._exit = False

        #Set the valve closed initially.
        self.percentage = 0

        #Used to store the measured position of the valve.
        self.actual_position = 0

        #Initial value. Calculated from the percentage requested.
        self.high_limit = 2

        #Initial value. Calculated from the percentage requested.
        self.low_limit = 1

        self.calculate_limits()

        threading.Thread.__init__(self)

        self.start()

    def run(self):
        """This is the part of the code that runs in the thread"""
        while not self._exit:
            self.actual_position = self.get_position()

            if ((self.actual_position <= self.high_limit
                 and self.actual_position >= self.low_limit)
                or (self.actual_position == -1)):

                #Hold current position
                logger.debug("ManageGateValve: Hold at "+str(self.actual_position))
                GPIO.output(self.forward_pin, GPIO.LOW)
                GPIO.output(self.reverse_pin, GPIO.LOW)
                time.sleep(1)

            elif self.actual_position < self.low_limit:
                #Open the valve
                logger.debug("ManageGateValve: Open valve a bit.")

                #Enable the motor.
                self.clutch_engage()
                GPIO.output(self.forward_pin, GPIO.HIGH)
                GPIO.output(self.reverse_pin, GPIO.LOW)

            elif self.actual_position > self.high_limit:
                #Close the valve.
                logger.debug("ManageGateValve: Close valve a bit.")

                #Enable the motor.
                self.clutch_engage()
                GPIO.output(self.forward_pin, GPIO.LOW)
                GPIO.output(self.reverse_pin, GPIO.HIGH)

    def clutch_engage(self):
        GPIO.output(self.clutch_pin, GPIO.HIGH)

    def clutch_disengage(self):
        GPIO.output(self.clutch_pin, GPIO.LOW)

    def get_position(self):
        #Create the Analog reading object to read Ch 0 of the A/D
        chan = AnalogIn(ads, ADS.P0)

        try:
            #Get voltage reading for channel 0 (the position pot slider)
            voltage_0 = chan.voltage

        except OSError:
            #An I/O error occured when trying to read from the A/D.
            logger.error("OSError \n\n"+str(traceback.format_exc())
                         + "\n\nwhile running. Continuing...")

            print("OSError \n\n"+str(traceback.format_exc())+"\n\nwhile running. Continuing...")

            #The current reading is invalid so flag an error.
            return -1

        #Actual position as a percentage at the time of reading
        self.actual_position = int((voltage_0/self.ref_voltage*100))
        return self.actual_position

    def set_position(self, new_percentage):
        """Sets self.percentage to new_percentage."""
        self.percentage = new_percentage
        self.calculate_limits()

    def calculate_limits(self):
        self.actualposition = self.get_position()
        if (self.actualposition) != self.percentage:
            if ((self.percentage + self.pos_tolerance) > (self.max_open - self.pos_tolerance)):
                self.high_limit = self.max_open
                self.low_limit = self.max_open - 6


            elif (self.percentage - self.pos_tolerance < self.min_open):
                self.low_limit = self.min_open
                self.high_limit = self.min_open + 1

            else:
                #Set the High Limit to the required percentage
                self.high_limit = self.percentage + self.pos_tolerance

                #Set the Low Limit to the required percentage
                self.low_limit = self.percentage - self.pos_tolerance

    def stop(self):
        """Stops the thread."""
        self._exit = True
        self.clutch_disengage()
