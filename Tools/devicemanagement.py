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
import sys
import logging

#Import modules.
import config

#Use logger here too.
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

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

except (ImportError, NotImplementedError, ValueError) as e:
    if isinstance(e, ValueError):
        #Occurs when no I2C device is present.
        logger.critical("ADS (I2C) device not found!")
        print("ADS (I2C) device not found!")

    if not config.TESTING:
        logger.critical("Unable to import RPi.GPIO or ADS modules! Did you mean to use testing mode?")
        logger.critical("Exiting...")
        logging.shutdown()

        sys.exit("Unable to import RPi.GPIO or ADS modules! Did you mean to use testing mode? Exiting...")

    else:
        #Import dummy classes and methods.
        from Tools.testingtools import GPIO
        from Tools.testingtools import ADS
        from Tools.testingtools import ads
        from Tools.testingtools import AnalogIn

class ManageHallEffectProbe(threading.Thread):
    """
    This class is used to repeatedly poll the level of the hall effect probe, and
    make these levels available to the monitor thread. This is done because we can
    no longer use the hardware interrupts as with the old hall effect probe - this
    one uses and ADC.

    Documentation for the constructor for objects of type ManageHallEffectProbe:

    Usage:
        Use the constructor for this class the same way as for BaseDeviceClass.

    """

    def __init__(self, probe):
        """The constructor, set up some basic threading stuff"""
        #Initialise the thread.
        threading.Thread.__init__(self)

        #Make the probe object available to the rest of the class.
        self.probe = probe

        # Create four single-ended inputs on channels 0 to 3
        self.chan0 = AnalogIn(ads, ADS.P0)
        self.chan1 = AnalogIn(ads, ADS.P1)
        self.chan2 = AnalogIn(ads, ADS.P2)
        self.chan3 = AnalogIn(ads, ADS.P3)

        self.start()

    def run(self): #FIXME This is not a monitor thread! Fix documentation.
        """The main body of the monitor thread for this probe"""
        while not config.EXITING:
            new_reading = self.test_levels()

            if new_reading == 1000:
                #No Sensors Triggered - leave the reading as it was.
                logger.debug("Between levels - no sensors triggered")

            else:
                #Only update this if we got a meaningful reading from the ADS.
                #Aka at least 1 sensor triggered.
                self.probe._current_reading = new_reading

            time.sleep(0.5)

    def get_compensated_probe_voltages(self):
        """This function performs the measurement of the four voltages and applies the compensation
        to take out errors caused by the varying output impedance of the probe
        """
         # Initialise Lists and variables to hold the working values in each column
        v_meas = list()                                      # Actual voltages
        v_comp = list()                                      # Compensated values
        result = list()                                      # Measured value and column

        # Prepare v_comp to hold 4 values (pre-populate to avoid errors).
        for i in range(0, 4):
            v_comp.append(0)

        # Measure the voltage in each chain
        v_meas.append(self.chan0.voltage)
        v_meas.append(self.chan1.voltage)
        v_meas.append(self.chan2.voltage)
        v_meas.append(self.chan3.voltage)

        # Find the minimum value
        v_min = min(v_meas)

        # Find the column that the minimum value is in
        min_column = v_meas.index(min(v_meas))

        # Work out the average of the three highest measurements
        #(thus ignoring the 'dipped' channel).
        v_tot = v_meas[0] + v_meas[1] + v_meas[2] + v_meas[3]
        v_avg = (v_tot - v_min)/3

        # Calculate the compensated value for each channel.
        if v_min >= 3.0:
            # Take a shortcut when the magnet is between sensors
            v_comp[0] = v_comp[1] = v_comp[2] = v_comp[3] = v_avg - v_min

        else:
            if min_column in (0, 1, 2, 3):
                v_comp[min_column] = v_avg - v_min

            else:
                #NB: Will this ever happen? It seems impossible to me - Hamish.
                v_comp[min_column] = v_avg

        result = v_comp, min_column

        return result

    def test_levels(self):
        count = 0
        level = 1000                                              # Value to return

        while count < self.probe.length:
            v_comp, min_column = self.get_compensated_probe_voltages()

            # Now test the channel with the dip to see if any of the sensors are triggered
            if ((v_comp[min_column] <= self.probe.high_limits[count])
                    and (v_comp[min_column] >= self.probe.low_limits[count])):

                level = self.probe.depths[min_column][count]

            else:
                #FIXME: This fills up the log file pretty quickly - why?
                logger.debug("Possible faulty probe - no limits passed")

            count += 1

        return level

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
    def __init__(self, valve):
        """The constructor, set up some basic threading stuff."""
        #Store a reference to the GateValve object.
        self.valve = valve

        self._exit = False

        #Set the valve closed initially.
        self.percentage = 0

        #Used to store the measured position of the valve.
        self.actual_position = 0

        #Initial value. Calculated from the percentage requested.
        self.high_limit = 5

        #Initial value. Calculated from the percentage requested.
        self.low_limit = 0

        self.calculate_limits()

        threading.Thread.__init__(self)

        self.start()

    def run(self):
        """This is the part of the code that runs in the thread"""
        while not config.EXITING:
            self.actual_position = self.get_position()

            if ((self.actual_position <= self.high_limit
                 and self.actual_position >= self.low_limit)
                or (self.actual_position == -1)):

                #Hold current position
                logger.debug("ManageGateValve: Hold at "+str(self.actual_position))
                GPIO.output(self.valve.forward_pin, GPIO.LOW)
                GPIO.output(self.valve.reverse_pin, GPIO.LOW)
                time.sleep(1)

            elif self.actual_position < self.low_limit:
                #Open the valve
                logger.debug("ManageGateValve: Open valve a bit.")

                #Enable the motor.
                self.clutch_engage()
                GPIO.output(self.valve.forward_pin, GPIO.HIGH)
                GPIO.output(self.valve.reverse_pin, GPIO.LOW)

            elif self.actual_position > self.high_limit:
                #Close the valve.
                logger.debug("ManageGateValve: Close valve a bit.")

                #Enable the motor.
                self.clutch_engage()
                GPIO.output(self.valve.forward_pin, GPIO.LOW)
                GPIO.output(self.valve.reverse_pin, GPIO.HIGH)

        self.clutch_disengage()

    def clutch_engage(self):
        GPIO.output(self.valve.clutch_pin, GPIO.HIGH)

    def clutch_disengage(self):
        GPIO.output(self.valve.clutch_pin, GPIO.LOW)

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

        #Actual position as a percentage at the time of reading.
        #FIXME: This sometimes seems to be negative. Why? Bug in the ADS software?
        self.actual_position = int((voltage_0/self.valve.ref_voltage*100))
        return self.actual_position

    def set_position(self, new_percentage):
        """Sets self.percentage to new_percentage."""
        self.percentage = new_percentage
        self.calculate_limits()

    def calculate_limits(self):
        self.actualposition = self.get_position()
        if (self.actualposition) != self.percentage:
            if ((self.percentage + self.valve.pos_tolerance) > (self.valve.max_open - self.valve.pos_tolerance)):
                self.high_limit = self.valve.max_open
                #Subtract 6 to make sure the valve can close, but doesn't strain the
                #motor if alignment isn't perfect.
                self.low_limit = self.valve.max_open - 6

            elif (self.percentage - self.valve.pos_tolerance < self.valve.min_open):
                self.low_limit = self.valve.min_open
                #Add 1 to make sure the valve can close, but doesn't strain the
                #motor if alignment isn't perfect.
                self.high_limit = self.valve.min_open + 1

            else:
                #Set the High Limit to the required percentage
                self.high_limit = self.percentage + self.valve.pos_tolerance

                #Set the Low Limit to the required percentage
                self.low_limit = self.percentage - self.valve.pos_tolerance
