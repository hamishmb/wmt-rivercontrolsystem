#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Device management classes for the River System Control and Monitoring Software
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
This is the part of the software framework that contains classes to help manage the device objects.
These take the form of management threads to separate coordination of each of these
more complicated devices, from the classes that represent the devices themselves.

.. module:: devicemanagement.py
    :platform: Linux
    :synopsis: The part of the framework that contains the management code for device classes.

.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>
.. moduleauthor:: Terry Coles <wmt@hadrian-way.co.uk

"""

import traceback
import threading
import time
import sys
import logging

#Import modules.
import config

from Tools.coretools import rcs_print as print #pylint: disable=redefined-builtin

#Use logger here too.
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

for handler in logging.getLogger('River System Control Software').handlers:
    logger.addHandler(handler)

try:
    #Allow us to generate documentation on non-RPi systems.
    from RPi import GPIO
    GPIO.setmode(GPIO.BCM)

    #Setup for ADS1115 (A2D converter).
    import board
    import busio

    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn

    # Create the I2C bus
    I2C = busio.I2C(board.SCL, board.SDA)

except (ImportError, NotImplementedError, ValueError) as error:
    if isinstance(error, ValueError):
        #Occurs when no I2C device is present.
        logger.critical("ADS (I2C) device not found!")
        print("ADS (I2C) device not found!", level="critical")

    if not config.TESTING:
        logger.critical("Unable to import RPi.GPIO or ADS modules! "
                        + "Did you mean to use testing mode?")

        logger.critical("Exiting...")
        logging.shutdown()

        sys.exit("Unable to import RPi.GPIO or ADS modules! "
                 + "Did you mean to use testing mode? Exiting...")

    else:
        #Import dummy classes and methods.
        from Tools.testingtools import GPIO #pylint: disable=ungrouped-imports
        from Tools.testingtools import ADS #pylint: disable=ungrouped-imports
        from Tools.testingtools import AnalogIn #pylint: disable=ungrouped-imports

        I2C = None

def reconfigure_logger():
    """
    Reconfigures the logging level for this module.
    """

    logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

    for _handler in logging.getLogger('River System Control Software').handlers:
        logger.addHandler(_handler)

class ManageHallEffectProbe(threading.Thread):
    """
    This class is used to repeatedly poll the level of the hall effect probe, and
    make these levels available to the monitor thread. This is done because we can
    no longer use the hardware interrupts as with the old hall effect probe - this
    one uses an ADC.

    Documentation for the constructor for objects of type ManageHallEffectProbe:

    Args:
        probe (BaseDeviceClass-Object).     The hall effect probe to manage.

    Usage:
        Use the constructor for this class the same way as for BaseDeviceClass.

    """

    def __init__(self, probe, i2c_address):
        """The constructor, set up some basic threading stuff"""
        #Initialise the thread.
        threading.Thread.__init__(self)

        # Create the ADC object using the I2C bus
        self.ads = ADS.ADS1115(I2C, address=i2c_address)

        #Make the probe object available to the rest of the class.
        self.probe = probe

        #Create a lock (or mutex) for the A2D.
        self.ads_lock = threading.RLock()

        # Create four single-ended inputs on channels 0 to 3
        self.chan0 = AnalogIn(self.ads, ADS.P0)
        self.chan1 = AnalogIn(self.ads, ADS.P1)
        self.chan2 = AnalogIn(self.ads, ADS.P2)
        self.chan3 = AnalogIn(self.ads, ADS.P3)

        #For debugging.
        self.count = 0

        self.is_running = True
        self.start()

    def run(self):
        """
        The main body of the management thread for this probe.
        """

        while not config.EXITING:
            new_reading = self.get_level()

            if new_reading == -1:
                #No Sensors Triggered - leave the reading as it was.
                logger.debug("Between levels (no sensors triggered) or unable to get voltage")

            else:
                #Only update this if we got a meaningful reading from the ADS.
                #Aka at least 1 sensor triggered.
                self.probe._current_reading = new_reading

            time.sleep(0.5)

            if config.DEBUG:
                self.count += 1

        #Signal that we have exited.
        self.is_running = False

    def get_compensated_probe_voltages(self):
        """
        This function performs the measurement of the four voltages and
        applies the compensation to take out errors caused by the varying
        output impedance of the probe.

        Returns:
            A tuple:
                1st element:        The compensated voltage.
                2nd element:        The column the minimum voltage was found in.

        """

        #Initialise Lists and variables to hold the working values in each column.
        #Actual voltages
        v_meas = []

        #Compensated values - prefill with 4 zeros.
        v_comp = [0, 0, 0, 0]

        #Measure the voltage in each chain
        try:
            self.ads_lock.acquire()
            v_meas.append(self.chan0.voltage)
            v_meas.append(self.chan1.voltage)
            v_meas.append(self.chan2.voltage)
            v_meas.append(self.chan3.voltage)

        except OSError:
            #An I/O error occured when trying to read from the A/D.
            logger.error("OSError \n\n"+str(traceback.format_exc())
                         + "\n\nwhile running. Continuing...")

            print("OSError \n\n"+str(traceback.format_exc())
                  +"\n\nwhile running. Continuing...", level="error")

            #The current reading is invalid so flag an error.
            return False, False

        finally:
            self.ads_lock.release()

        #Do 10 minutes of probe voltage dumping if we're in debug mode.
        if config.DEBUG:
            if self.count < 1200:
                logger.info("Voltages ("+self.probe.get_id()+"): "+str(v_meas[0])+", "
                            + str(v_meas[1])+", "+str(v_meas[2])
                            +", "+str(v_meas[3]))

                print("Voltages ("+self.probe.get_id()+"): "+str(v_meas[0])+", "
                      + str(v_meas[1])+", "+str(v_meas[2])
                      +", "+str(v_meas[3]))

        #Find the minimum value
        v_min = min(v_meas)

        #Find the column that the minimum value is in
        min_column = v_meas.index(min(v_meas))

        #Work out the average of the three highest measurements
        #(thus ignoring the 'dipped' channel).
        v_tot = v_meas[0] + v_meas[1] + v_meas[2] + v_meas[3]
        v_avg = (v_tot - v_min)/3

        #Calculate the compensated value for each channel.
        if v_min >= 3.0:
            #Take a shortcut when the magnet is between sensors
            v_comp[0] = v_comp[1] = v_comp[2] = v_comp[3] = v_avg - v_min

        else:
            if min_column in (0, 1, 2, 3):
                v_comp[min_column] = v_avg - v_min

            else:
                #NB: Catchall for any corner cases where a minimum cannot be determined.
                v_comp[min_column] = v_avg

        return (v_comp, min_column)

    def get_level(self):
        """
        This method determines the probe float's position, and returns it.

        Returns:
            int. The position.
                -1:                         An error has occurred!
                anything else:              The level in mm.

        Usage:
            >>> get_level()
            >>> 475

        """

        count = 0

        #The value to return. This defaults to -1 if we couldn't detect
        #the level.
        level = -1

        v_comp, min_column = self.get_compensated_probe_voltages()

        #Return -1 if an error occurred getting the voltages.
        if v_comp is False:
            return -1

        while count < self.probe.length:
            #Now test the channel with the dip to see if any of the
            #sensors are triggered

            if (v_comp[min_column] <= self.probe.high_limits[count]) \
                and (v_comp[min_column] >= self.probe.low_limits[count]):

                level = self.probe.depths[min_column][count]

            else:
                logger.debug("Possible faulty probe - no limits passed")

            count += 1

        #Print level that corresponds to the voltage if we're in debug mode.
        #Do this only for the first 1200 readings to avoid spamming the log too much.
        if config.DEBUG:
            if self.count < 1200:
                logger.info("Level ("+self.probe.get_id()+"): "+str(level))

                print("Level ("+self.probe.get_id()+"): "+str(level))

        return level

    #----- CONTROL METHODS -----
    def wait_exit(self):
        """
        This method is used to wait for the management thread to exit.

        This isn't a mandatory function as the management thread will shut down
        automatically when config.EXITING is set to True.

        Usage:
            >>> <ManageHallEffectProbeObject>.wait_exit()
        """

        while self.is_running:
            time.sleep(0.5)

class ManageGateValve(threading.Thread):
    """
    This class is used to energise and position the Actuator Motor that drives a Gate Valve
    to control the flow of water in the system.

    Documentation for the constructor for objects of type ManageGateValve:

    Args:
        valve (GateValve-Object).         The valve to manage.
        i2c_address (int).                The i2c_address of the ADC. Most easily expressed
                                          in hexadecimal.

    Usage:
        >>> mgmt_thread = ManageGateValve(<valve-object>, 0x48)
    """

    def __init__(self, valve, i2c_address):
        """The constructor, set up some basic threading stuff."""
        threading.Thread.__init__(self)
        #Store a reference to the GateValve object.
        self.valve = valve

        # Create the ADC object using the I2C bus
        self.ads = ADS.ADS1115(I2C, address=i2c_address)

        #Set the valve closed initially.
        self.percentage = 0

        #Used to store the measured position of the valve.
        self.actual_position = 0

        #Initial value. Calculated from the percentage requested.
        self.high_limit = 5

        #Initial value. Calculated from the percentage requested.
        self.low_limit = 0

        #Create a lock (or mutex) for the A2D.
        self.ads_lock = threading.RLock()

        self.is_running = True

        self.start()

    def run(self):
        """This is the part of the code that runs in the thread"""

        while not config.EXITING:
            self.actual_position = self._get_position()
            self.calculate_limits()

            logger.debug("ManageGateValve: Actual position: "+str(self.actual_position)
                         + " type: "+str(type(self.actual_position)))

            logger.debug("ManageGateValve: High limit: "+str(self.high_limit)
                         + " type: "+str(type(self.high_limit)))

            logger.debug("ManageGateValve: Low limit: "+str(self.low_limit)
                         + " type: "+str(type(self.low_limit)))

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

            else:
                #FIXME Is this a good way to handle this situation?
                logger.critical("ManageGateValve: Critical error: valve is not "
                                + "in any of the three states!")

                logger.critical("ManageGateValve: Actual position: "+str(self.actual_position)
                                +" type: "+str(type(self.actual_position)))

                logger.critical("ManageGateValve: High limit: "+str(self.high_limit)
                                +" type: "+str(type(self.high_limit)))

                logger.critical("ManageGateValve: Low limit: "+str(self.low_limit)
                                +" type: "+str(type(self.low_limit)))

                logger.critical("ManageGateValve: Shutting down river system software!")

                config.EXITING = True

                break

        self.clutch_disengage()

        #Signal that we have exited.
        self.is_running = False

    def calculate_limits(self):
        """
        This method calculates the maximum and minimum values to accept for
        for the position that was requested.

        This is required in order to provide some tolerance - the gate valve
        may not have the accuracy to move to exactly, say, 50%. By having a
        maximum and minimum limit, we can define what values are within
        tolerance.

        Usage:

            >>> calculate_limits()
        """

        if self.actual_position != self.percentage:
            if (self.percentage + self.valve.pos_tolerance) > \
               (self.valve.max_open - self.valve.pos_tolerance):

                self.high_limit = self.valve.max_open
                #Subtract 6 to make sure the valve can close, but doesn't strain the
                #motor if alignment isn't perfect.
                self.low_limit = self.valve.max_open - 6

            elif self.percentage - self.valve.pos_tolerance < self.valve.min_open:
                self.low_limit = self.valve.min_open
                #Add 1 to make sure the valve can close, but doesn't strain the
                #motor if alignment isn't perfect.
                self.high_limit = self.valve.min_open + 2

            else:
                #Set the High Limit to the required percentage
                self.high_limit = self.percentage + self.valve.pos_tolerance

                #Set the Low Limit to the required percentage
                self.low_limit = self.percentage - self.valve.pos_tolerance

    #-------------------- GETTER METHODS --------------------
    def _get_position(self):
        """
        This method queries the A2D to get the gate valve's position.

        .. warning::
            Do NOT run this method outside of the management thread.
            Doing so can cause a deadlock. There are safety measures
            built in to prevent this, but it can still happen.
        """

        #Create the Analog reading object to read Ch 0 of the A/D
        chan = AnalogIn(self.ads, ADS.P0)

        try:
            #Get voltage reading for channel 0 (the position pot slider)
            logger.debug("ManageGateValve: About to read voltage")
            self.ads_lock.acquire()
            voltage_0 = chan.voltage
            logger.debug("ManageGateValve: Read voltage")

        except OSError:
            #An I/O error occured when trying to read from the A/D.
            logger.error("OSError \n\n"+str(traceback.format_exc())
                         + "\n\nwhile running. Continuing...")

            print("OSError \n\n"+str(traceback.format_exc())
                  +"\n\nwhile running. Continuing...", level="error")

            #The current reading is invalid so flag an error.
            return -1

        finally:
            self.ads_lock.release()

        #Actual position as a percentage at the time of reading.
        actual_position = int((voltage_0/self.valve.ref_voltage*100))

        #If this position came through as a negative number, reject it.
        if actual_position < 0:
            return -1

        return actual_position

    def get_current_position(self):
        """
        Returns the current position without querying the A2D.
        """

        return self.actual_position

    def get_requested_position(self):
        """
        Returns the most recent requested position for the gate valve.
        """

        return self.percentage

    #-------------------- SETTER METHODS --------------------
    def set_position(self, percentage):
        """
        Sets self.percentage to percentage.

        This no longer calculates the limits - doing this while the limits are
        being read could cause undefined behaviour.

        Args:
            percentage (int). The percentage between 0 and 100 to set the
                              valve to.
        """

        if isinstance(percentage, bool) \
            or not isinstance(percentage, int) \
            or percentage > 100 \
            or percentage < 0:

            raise ValueError("Invalid value for percentage: "+str(percentage))

        self.percentage = percentage

    def clutch_engage(self):
        """
        This method engages the clutch, in order for the motor to be able to move
        the gate valve.

        Usage:
            >>> clutch_engage()
            >>>
        """

        GPIO.output(self.valve.clutch_pin, GPIO.HIGH)

    def clutch_disengage(self):
        """
        This method disengages the clutch.

        Usage:
            >>> clutch_engage()
            >>>
        """

        GPIO.output(self.valve.clutch_pin, GPIO.LOW)

    #----- CONTROL METHODS -----
    def wait_exit(self):
        """
        This method is used to wait for the management thread to exit.

        This isn't a mandatory function as the management thread will shut down
        automatically when config.EXITING is set to True.

        Usage:
            >>> <ManageGateValveObject>.wait_exit()
        """

        while self.is_running:
            time.sleep(0.5)
