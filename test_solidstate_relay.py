#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Solid-State-Relay test for the River System Control and Monitoring Software Version 0.9.1
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

import time
import RPi.GPIO as GPIO

def run_standalone():
    #Allows the progam to run standalone as well as being a module.
    #Do required imports.
    import Tools

    from Tools import sensorobjects

    from Tools.sensorobjects import Motor

    print("Testing. Please stand by...")

    #Create the motor object.
    ssr = Motor("Motorey")

    #Set the motor up.
    ssr.set_pins(5, _input=False)

    try:
        time.sleep(3)
        print("On")
        ssr.enable()

        time.sleep(15)
        print("Off")
        ssr.disable()

    except BaseException as err:
        #Ignore all errors. Generally bad practice :P
        print("\nCaught Exception: ", err)

    finally:
        #Always clean up properly.
        print("Cleaning up...")

        #Reset GPIO pins.
        GPIO.cleanup()

if __name__ == "__main__":
    run_standalone()
