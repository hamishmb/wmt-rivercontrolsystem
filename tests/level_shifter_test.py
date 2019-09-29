#!/usr/bin/env python3
# Level_Shifter_Test.py:
#      Wimborne Model Town
#        River System
#      Level Shifter Test Code:
#       1.  Toggles GPIO Pins 5 and 18 at approx 0.1 Hz (SSR drivers)
#       2.  Monitors Pins 7 and 8 to identify when the pins are connected to ground.
#           (Empty and Full Float switches respectively)
#
# Copyright (c) 2018 Wimborne Model Town http://www.wimborne-modeltown.com/
#
#    This code is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    PWM_Dimmer.py is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    with this software.  If not, see <http://www.gnu.org/licenses/>.
# 
#  ***********************************************************************

import RPi.GPIO as GPIO
from time import sleep

ButtsPin = 5
SumpPin = 18
EmptyFloatSwitchPin = 7
FullFloatSwitchPin = 8

def setup():
    GPIO.setmode(GPIO.BCM)                      # Number GPIOs by Broadcom Numbers
    GPIO.setup(ButtsPin, GPIO.OUT)              # Set ButtsPin's mode is output
    GPIO.setup(SumpPin, GPIO.OUT)               # Set SumpPin's mode is output)
    GPIO.output(ButtsPin, GPIO.HIGH)            # Set both pins high (0 V across a pulled-up
    GPIO.output(SumpPin, GPIO.HIGH)             # open-collector output)
    GPIO.setup(FullFloatSwitchPin, GPIO.IN)     # Set Butts Group Full Float Switch Pin's mode as input)
    GPIO.setup(EmptyFloatSwitchPin, GPIO.IN)    # Set Butts Group Empty Float Switch Pin's mode as input)

def loop():
        while True:
                print('...Butts SSR on')
                GPIO.output(ButtsPin, GPIO.LOW)    # Butts SSR On
                print('...Sump SSR off')
                GPIO.output(SumpPin, GPIO.HIGH)      # Sump SSR Off
                print('')
                if GPIO.input(FullFloatSwitchPin):
                    print("Butts Group Full Float Switch High")
                else:
                    print("Butts Group Full Float Switch Low")
                if GPIO.input(EmptyFloatSwitchPin):
                    print("Butts Group Empty Float Switch High")
                else:
                    print("Butts Group Empty Float Switch Low")
                print('...Butts SSR off')
                GPIO.output(ButtsPin, GPIO.HIGH)     # Butts SSR Off
                print('...Sump SSR on')
                GPIO.output(SumpPin, GPIO.LOW)     # Sump SSR On
                print('')
                print('')
                sleep(10)
                

def destroy():
    GPIO.output(ButtsPin, GPIO.HIGH)     # Butts SSR off 
    GPIO.output(SumpPin, GPIO.HIGH)     # Sump SSR off
    GPIO.cleanup()                     # Release resource

if __name__ == '__main__':     # Program start from here
    setup()
    try:
        loop()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        destroy()
