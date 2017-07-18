#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Control Tools for the River System Control and Monitoring Software Version 1.0
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

#Do future imports to support running on python 2 as well. Python 3 is the default. Use unicode strings rather than ASCII strings, as they fix potential problems.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

#Standard Imports.
import RPi.GPIO

class Motor: #TODO Check types of arguments before setting to avoid weird errors later. Alternatively, use Python 3's type specifiers (breaks python 2 support).
    # ---------- CONSTRUCTORS ----------
    def __init__(Name): 
        """
        This is the constructor.
        Usage:

            <Motor-Object> Motor(str Name)
        """

        #Set some semi-private variables.
        self.__MotorName = Name              #Used to keep track of which motor we're controlling. Cannot be re-set after initialisation.
        self.__State = False                 #Motor is initialised to be off.
        self.__IsVariableSpeed = False       #Assume we don't have PWM by default.
        self.__ControlPin = -1               #Needs to be set.
        self.__PWMPin = -1                   #Needs to be set.

    # ---------- INFO SETTER FUNCTIONS ----------
    def SetPWMAvailable(PWMAvailable, PWMPin): #TODO Hardware check to determine if PWM is avaiable.
        """
        Enables/Disables PWM support.
        Usage:

            <Motor-Object>.SetPWMAvailable(bool PWMAvailable, int PWMPin)
        """

        self.__IsVariableSpeed = PWMAvailable
        self.__PWMPin = PWMPin

    def SetControlPin(ControlPin): #TODO Check if this Pin is already in use. If so throw an error. Also check if this pin is a valid output pin.
        """
        Sets the control pin for the motor.
        Usage:

            <Motor-Object>.SetControlPin(int ControlPin)
        """

        #TODO: Can we un-setup an old pin?
        self.__ControlPin = ControlPin

        GPIO.setup(self.__ControlPin, GPIO.OUT)

    # ---------- INFO GETTER FUNCTIONS ----------
    def GetName():
        """
        Returns the name of the motor this object is representing.
        Usage:

            str <Motor-Object>.GetName()
        """

        return self.__MotorName

    def SupportsPWM():
        """
        Returns True if PWM is supported for this motor. Else False.
        Usage:

            bool <Motor-Object>.SupportsPWM()
        """

        return self.__IsVariableSpeed

    def GetControlPin():
        """
        Returns the integer that represents the control pin for this motor.
        Usage:

            int <Motor-Object>.GetControlPin()
        """

        return self.__ControlPin

    # ---------- CONTROL FUNCTIONS ----------
    def TurnOn():
        """
        Turn the motor on. Returns True if successful, false if not.
        Usage:

            bool <Motor-Object>.TurnOn()
        """

        #Return false if control pin isn't set.
        if self.__ControlPin == -1:
            return False

        #Turn the pin on.
        GPIO.write(__ControlPin, True)

        return True

    def TurnOff():
        """
        Turn the motor off. Returns True if successful, false if not.
        Usage:

            bool <Motor-Object>.TurnOff()
        """

        #Return false if control pin isn't set.
        if self.__ControlPin == -1:
            return False

        #Turn the pin off.
        GPIO.write(__ControlPin, False)

        return True
