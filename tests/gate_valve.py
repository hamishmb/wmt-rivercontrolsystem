#!/usr/bin/env python3
# gate_valve.py - V03: 
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
forward   = 17                          # Motor Board Pin IN1 Pi Board Pin 11
reverse   = 27                          # Motor Board Pin IN2 Pi Board Pin 13
clutch = 19                             # Motor Board Pin IN3 Pi Board Pin 35
Pause = 10                              # Define wait time in seconds 

# Initialise and setup starting conditions
GPIO.setmode(GPIO.BCM)                  # Numbers GPIOs by Broadcom Pin Numbers
GPIO.setup(forward, GPIO.OUT)           # Control pins for Motor Drive Board
GPIO.setup(reverse, GPIO.OUT)           # ditto
GPIO.output(forward, GPIO.LOW)          # Reset both pins
GPIO.output(reverse, GPIO.LOW)
GPIO.setup(clutch, GPIO.OUT)            # Control pin for Motor Drive Board
GPIO.output(clutch, GPIO.LOW)           # Motor Clutch disengagedimport time

class ActuatorPosition(threading.Thread):
    def __init__(self, posTolerance, maxOpen, minOpen, refVoltage):
        """The constructor, set up some basic threading stuff."""
        self.posTolerance = posTolerance                    # Positional Tolerance in percent
        self.maxOpen = maxOpen                              # Upper limmit of valve position in percent
        self.minOpen = minOpen                              # Lower limmit of valve position in percent
        self.refVoltage = refVoltage                        # Voltage at the top of the position pot
        self._exit = False

        self.percentage = 0                                 # Set the valve closed initially.
        self.actualposition = 0                             # Used to store the measured position of the valve.
        self.HL = 5                                         # Initial value. Calculated from the percetage requested.
        self.LL = 1                                         # Initial value. Calculated from the percetage requested.
                
        self.calculate_limits()
        
        threading.Thread.__init__(self)

        self.start()

    def run(self):
        """This is the part of the code that runs in the thread"""
        self.clutchEngage()                         # Enable the motor

        while not self._exit:
            self.actualposition = self.getPosition()

            if(self.actualposition <= self.HL and self.actualposition >= self.LL):
                print("Hold at ", self.actualposition)
                GPIO.output(forward, GPIO.LOW)              # Hold current position
                GPIO.output(reverse, GPIO.LOW)
                time.sleep(Pause)
            if(self.actualposition < self.LL):
                print("Open Valve a bit.")
                GPIO.output(forward, GPIO.HIGH)             # Open the valve
                GPIO.output(reverse, GPIO.LOW)
            if(self.actualposition > self.HL):
                print("Close Valve a bit.")
                GPIO.output(forward, GPIO.LOW)              # Close the valve
                GPIO.output(reverse, GPIO.HIGH)

    def clutchEngage(self):
        GPIO.output(clutch, GPIO.HIGH)

    def clutchDisengage(self):
        GPIO.output(clutch, GPIO.LOW)

    def getPosition(self):
        chan = AnalogIn(ads, ADS.P0)                                # Create the Analog reading object to read Ch 0 of the A/D
        v0 = chan.voltage                                           # Get voltage reading for channel 0 (the position pot slider)
        print (v0)
        self.actualposition = int((v0/self.refVoltage*100))         # Actual position as a percentage at the time of reading
        return self.actualposition

    def calculate_limits(self):
        self.actualposition = self.getPosition()        
        if (self.actualposition) != self.percentage:
            if (self.percentage + self.posTolerance > self.maxOpen):
                self.HL = self.maxOpen
                self.LL = self.maxOpen - (2 * self.posTolerance)
            elif (self.percentage - self.posTolerance < self.minOpen):
                self.LL = self.minOpen
                self.HL = self.minOpen + (2 * self.posTolerance)
            else:
                self.HL = self.percentage + self.posTolerance        # Set the High Limit to the required percentage
                self.LL = self.percentage - self.posTolerance        # Set the Low Limit to the required percentage

    def set_percentage(self, new_percentage):
        """Sets self.percentage to new_percentage."""
        self.percentage = new_percentage
        self.calculate_limits()

    def stop(self):
        """Stops the thread."""
        self._exit = True
        self.clutchDisengage()


#############################################   Main Program   ##################################################

gate = ActuatorPosition(1, 99, 1, 3.3)

def menu():
    print ("Select from the following Menu")
    print ("    Press 'm' to set the valve to a position in percent and hold it there")
    print ("    Press 'e' to exit this menu or Ctrl-C to exit the program at any time")

    while True:
        char = input("Enter choice followed by <RET> ")

        if (char == "e"):
            print ("Exiting...")
            gate.stop()
            exit(0)

        elif (char == "m"):
            percent = int(input("Enter required position in % "))
            print ("Holding Valve Position at",percent,"%")
            gate.set_percentage(percent)

menu()
