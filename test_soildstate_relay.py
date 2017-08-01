#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Solid-State-Relay test for the River System Control and Monitoring Software Version 1.0
# This file is part of the River System Control and Monitoring Software.
# Copyright (C) 2017 Wimborne Model Town
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


import RPi.GPIO as GPIO
import time
import datetime
import sys
import getopt #Proper option handler.
import os

def RunStandalone():
    #Allows the progam to run standalone as well as being a module.
    #Do required imports.
    import Tools

    from Tools import sensorobjects
    from Tools import coretools as CoreTools

    from Tools.sensorobjects import Motor

    print("Testing. Please stand by...")

    #Create the motor object.
    TestMotor = Motor("Motorey")

    #Set the motor up.
    TestMotor.SetControlPin(15)

    #Don't use the thread here: it doesn't write to a file. TODO use a queue with the thread so we can use it here and receive messages to write them to a file, reducing duplications.
    try:
        time.sleep(3)
        print("On")
        TestMotor.TurnOn()

        time.sleep(15)
        print("Off")
        TestMotor.TurnOff()

    except BaseException as E:
        #Ignore all errors. Generally bad practice :P
        print("\nCaught Exception: ", E)

    finally:
        #Always clean up properly.
        print("Cleaning up...")

        #Reset GPIO pins.
        GPIO.cleanup()

if __name__ == "__main__":
    RunStandalone() 
