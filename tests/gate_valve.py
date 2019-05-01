#!/usr/bin/env python3
# gate_valve.py - V06:
#                Wimborne Model Town
#      River System Gate Valve Motor Functions
#
#  **********************************************************************
# This program carries out the following functions by putting up a Menu to:
#      a.  Move the Gate Valve to a designated position between 5 and 95% and keep it there (char 'm').
#      b.  Stop controlling the valve (char 's').
#      c.  Loop around the following sequence (char 'l'):
#          1) Turns the actuator motor to open the valve to 80%.
#          2) Waits for a programmable delay.
#          3) Turns the actuator motor to close the valve to 20%.
#          4) Repeat until interrupted.
#
# Copyright (c) 2018 Wimborne Model Town http://www.wimborne-modeltown.com/
#
#    This code is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Scheduler.py is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    with this software.  If not, see <http://www.gnu.org/licenses/>.
#
#  ***********************************************************************

import RPi.GPIO as GPIO
import threading
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c)

# Define Valve Control Pins
forward_pin   = 17                      # Motor Board Pin IN1 Pi Board Pin 11
reverse_pin_pin   = 27                      # Motor Board Pin IN2 Pi Board Pin 13
clutch_pin_pin = 19                         # Motor Board Pin IN3 Pi Board Pin 35
Pause = 1                               # Define wait time in seconds

# Initialise and setup starting conditions
GPIO.setmode(GPIO.BCM)                  # Numbers GPIOs by Broadcom Pin Numbers
GPIO.setup(forward_pin, GPIO.OUT)           # Control pins for Motor Drive Board
GPIO.setup(reverse_pin, GPIO.OUT)           # ditto
GPIO.output(forward_pin, GPIO.LOW)          # Reset both pins
GPIO.output(reverse_pin, GPIO.LOW)
GPIO.setup(clutch_pin, GPIO.OUT)            # Control pin for Motor Drive Board
GPIO.output(clutch_pin, GPIO.LOW)           # Motor Clutch disengaged

class ActuatorPosition(threading.Thread):
    def __init__(self, pos_tolerance, max_open, min_open, ref_voltage):
        """The constructor, set up some basic threading stuff."""
        self.pos_tolerance = pos_tolerance                    # Positional Tolerance in percent
        self.max_open = max_open                              # Upper limmit of valve position in percent
        self.min_open = min_open                              # Lower limmit of valve position in percent
        self.ref_voltage = ref_voltage                        # Voltage at the top of the position pot
        self._exit = False

        self.percentage = 0                                 # Set the valve closed initially.
        self.actual_position = 0                             # Used to store the measured position of the valve.
        self.high_limit = 1                                         # Initial value. Calculated from the percetage requested.
        self.low_limit = 1                                         # Initial value. Calculated from the percetage requested.
                
        self.calculate_limits()
        
        threading.Thread.__init__(self)

        self.start()

    def run(self):
        """This is the part of the code that runs in the thread"""
        while not self._exit:
            self.actual_position = self.get_position()

            if(self.actual_position <= self.high_limit and self.actual_position >= self.low_limit):
                GPIO.output(forward_pin, GPIO.LOW)              # Hold current position
                GPIO.output(reverse_pin, GPIO.LOW)
                time.sleep(Pause)

            elif(self.actual_position < self.low_limit):
                self.clutch_engage()                         # Enable the motor
                GPIO.output(forward_pin, GPIO.HIGH)             # Open the valve
                GPIO.output(reverse_pin, GPIO.LOW)

            elif(self.actual_position > self.high_limit):
                self.clutch_engage()                         # Enable the motor
                GPIO.output(forward_pin, GPIO.LOW)              # Close the valve
                GPIO.output(reverse_pin, GPIO.HIGH)

    def clutch_engage(self):
        GPIO.output(clutch_pin, GPIO.HIGH)

    def clutch_disengage(self):
        GPIO.output(clutch_pin, GPIO.LOW)

    def get_position(self):
        chan = AnalogIn(ads, ADS.P0)                                # Create the Analog reading object to read Ch 0 of the A/D
        
        try:
            v0 = chan.voltage                                       # Get voltage reading for channel 0 (the position pot slider)
        except OSError:                                             # An I/O error occured when trying to read from the A/D.
            print(" OSError. Continuing...")
            return self.actual_position                             # The current reading is invalid so return the last one.

        self.actual_position = int((v0/self.ref_voltage)*100)         # Actual position as a percentage at the time of reading
        return self.actual_position

    def calculate_limits(self):
        self.actual_position = self.get_position()
        if (self.actual_position) != self.percentage:
            if ((self.percentage + self.pos_tolerance) > (self.max_open - self.pos_tolerance)):
                self.high_limit = self.max_open
                self.low_limit = self.max_open - 6
            elif ((self.percentage - self.pos_tolerance) < self.min_open):
                self.low_limit = self.min_open
                self.high_limit = self.min_open + 1
            else:
                self.high_limit = self.percentage + self.pos_tolerance        # Set the High Limit to the required percentage
                self.low_limit = self.percentage - self.pos_tolerance        # Set the Low Limit to the required percentage

    def set_percentage(self, new_percentage):
        """Sets self.percentage to new_percentage."""
        self.percentage = new_percentage
        self.calculate_limits()

    def stop(self):
        """Stops the thread."""
        self._exit = True
        self.clutch_disengage()

def cycle():
    while True:
        gate.set_percentage(0)
        time.sleep(15)
        gate.set_percentage(100)
        time.sleep(15)


#############################################   Main Program   ##################################################

gate = ActuatorPosition(1, 90, 1, 3.3)

def menu():
    print ("Select from the following Menu")
    print ("    Press 'm' to set the valve to a position in percent and hold it there")
    print ("    Press 'c' to cycle the valve between 0% and 100%")
    print ("    Press 'e' to exit this menu or Ctrl-C to exit the program at any time")

    while True:
        char = input("Enter choice followed by <RET> ")

        if (char == "e"):
            print ("Exiting...")
            gate.stop()
            exit(0)

        elif (char == "c"):
            cycle()

        elif (char == "m"):
            percent = int(input("Enter required position in % "))
            print ("Holding Valve Position at",percent,"%")
            gate.set_percentage(percent)

try:
    menu()
except:
    print("Exiting...")
