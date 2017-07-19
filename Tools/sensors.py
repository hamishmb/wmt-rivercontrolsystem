#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Sensor classes for the River System Control and Monitoring Software Version 1.0
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
import RPi.GPIO as GPIO

#TODO Change pins to BCM so we can change this.
GPIO.setmode(GPIO.BOARD)

class Motor: #TODO Check types of arguments before setting to avoid weird errors later. Alternatively, use Python 3's type specifiers (breaks python 2 support).
    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name): 
        """
        This is the constructor.
        Usage:

            <Variable-Name> = Motor(str Name)
        """

        #Set some semi-private variables.
        self.__MotorName = Name              #Used to keep track of which motor we're controlling. Cannot be re-set after initialisation.
        self.__State = False                 #Motor is initialised to be off.
        self.__IsVariableSpeed = False       #Assume we don't have PWM by default.
        self.__ControlPin = -1               #Needs to be set.
        self.__PWMPin = -1                   #Needs to be set.

    # ---------- INFO SETTER FUNCTIONS ----------
    def SetPWMAvailable(self, PWMAvailable, PWMPin): #TODO Hardware check to determine if PWM is avaiable.
        """
        Enables/Disables PWM support.
        Usage:

            <Motor-Object>.SetPWMAvailable(bool PWMAvailable, int PWMPin)
        """

        self.__IsVariableSpeed = PWMAvailable
        self.__PWMPin = PWMPin

    def SetControlPin(self, ControlPin): #TODO Check if this Pin is already in use. If so throw an error. Also check if this pin is a valid output pin.
        """
        Sets the control pin for the motor.
        Usage:

            <Motor-Object>.SetControlPin(int ControlPin)
        """

        #TODO: Can we un-setup an old pin?
        self.__ControlPin = ControlPin

        GPIO.setup(self.__ControlPin, GPIO.OUT)

    # ---------- INFO GETTER FUNCTIONS ----------
    def GetName(self):
        """
        Returns the name of the motor this object is representing.
        Usage:

            str <Motor-Object>.GetName()
        """

        return self.__MotorName

    def SupportsPWM(self):
        """
        Returns True if PWM is supported for this motor. Else False.
        Usage:

            bool <Motor-Object>.SupportsPWM()
        """

        return self.__IsVariableSpeed

    def GetControlPin(self):
        """
        Returns the integer that represents the control pin for this motor.
        Usage:

            int <Motor-Object>.GetControlPin()
        """

        return self.__ControlPin

    # ---------- CONTROL FUNCTIONS ----------
    def TurnOn(self):
        """
        Turn the motor on. Returns True if successful, false if not.
        Usage:

            bool <Motor-Object>.TurnOn()
        """

        #Return false if control pin isn't set.
        if self.__ControlPin == -1:
            return False

        #Turn the pin on.
        GPIO.write(self.__ControlPin, True)

        return True

    def TurnOff(self):
        """
        Turn the motor off. Returns True if successful, false if not.
        Usage:

            bool <Motor-Object>.TurnOff()
        """

        #Return false if control pin isn't set.
        if self.__ControlPin == -1:
            return False

        #Turn the pin off.
        GPIO.write(self.__ControlPin, False)

        return True

# -------------------- SENSOR PROBES --------------------

class ResistanceProbe: #TODO Handle improper setup better.
    # ---------- CONSTRUCTORS ----------
    def __init__(self, ProbeName):
        """
        This is the constructor.
        Usage:

            <Variable-Name> = ResistanceProbe(string ProbeName)
        """

        #Set some semi-private variables.
        self.__ProbeName = ProbeName         #Used to keep track of which probe we're controlling. Cannot be re-set after initialisation.
        self.__ActiveState = False           #Active low by default.
        self.__Pins = []                     #Needs to be set.
        self.__RPins = []                    #Needs to be set.

    # ---------- INFO SETTER FUNCTIONS ----------
    def SetActiveState(self, State):
        """
        Sets the active state for the pins. True for active high, False for active low.
        Usage:

            <ResistanceProbe-Object>.SetActiveState(bool State)
        """

        self.__ActiveState = State

    def SetPins(self, Pins):
        """
        Sets the pins this probe will use, from low to high.
        Usage:

            <ResistanceProbe-Object>.SetPins(tuple Pins)
        """

        self.__Pins = Pins
        self.__RPins = Pins[::-1]

        #Setup the pins.
        #10 Inputs. 0 is for the lowest depth, 9 the highest.
        GPIO.setup(self.__Pins[0], GPIO.IN)
        GPIO.setup(self.__Pins[1], GPIO.IN)
        GPIO.setup(self.__Pins[2], GPIO.IN)
        GPIO.setup(self.__Pins[3], GPIO.IN)
        GPIO.setup(self.__Pins[4], GPIO.IN)
        GPIO.setup(self.__Pins[5], GPIO.IN)
        GPIO.setup(self.__Pins[6], GPIO.IN)
        GPIO.setup(self.__Pins[7], GPIO.IN)
        GPIO.setup(self.__Pins[8], GPIO.IN)
        GPIO.setup(self.__Pins[9], GPIO.IN)

    # ---------- INFO GETTER FUNCTIONS ----------
    def GetName(self):
        """
        Returns the name of this probe.
        Usage:

            string <ResistanceProbe-Object>.GetName()
        """

        return self.__ProbeName

    def GetActiveState(self):
        """
        Returns the active state for the pins.
        Usage:

            bool <ResistanceProbe-Object>.GetActiveState()
        """

        return self.__ActiveState

    def GetPins(self):
        """
        Returns the pins this probe is using, from high to low.
        Usage:

            tuple <ResistanceProbe-Object>.GetPins()
        """

        return self.__Pins

    # ---------- CONTROL FUNCTIONS ---------- 
    def GetLevel(self):
        """
        Gets the level of the water in the probe.
        Usage:

            (int, string) <ResistanceProbe-Object>.GetLevel()
        """

        for Pin in self.__RPins:
            #Ignore pins until we find one that is in the active state.
            if GPIO.input(Pin) != self.__ActiveState:
                continue

            #This pin must be active.
            Index = self.__Pins.index(Pin)

            #Log the states of all the pins.
            StateText = ""

            for Pin in self.__Pins:
                StateText += unicode(GPIO.input(Pin))

            #Check for faults.
            self.CheckForFaults(Index, StateText)

            #Return the level, assume pin 0 is at 0mm. Also return FaultText
            return Index*100, StateText

        #No pins were high.
        return -1, "1111111111"

    def CheckForFaults(self, HighestActivePin, StateText): #TODO setup and use a logger for this. TODO Actually do something with the data instead of just printing it and then throwing it away.
        """Checks for faults in the sensor. Isn't capable of finding all faults without another sensor to compare against.
        Usage:

            bool <ResistanceProbe-Object>.CheckForFaults(int HighestActivePin)
        """

        print("Highest active Pin index: "+str(HighestActivePin))
        
        Faulty = False

        print("Checking that "+str(StateText[:HighestActivePin]) +" only contains active pins.")

        print(bool(Pin), self.__ActiveState)

        #All pins before this one should be active.
        for Pin in StateText[:HighestActivePin]:
            print(bool(Pin), self.__ActiveState)

            if bool(Pin) != self.__ActiveState:
                print("FAULT on pin at index "+StateText.index(Pin)+"!")
                Faulty = True

        print("Checking that "+str(StateText[HighestActivePin:]) +" only contains inactive pins.")

        #All pins after this one should be inactive.
        for Pin in StateText[HighestActivePin+1:]:
            if bool(Pin) == self.__ActiveState:
                print("FAULT on pin at index "+StateText.index(Pin)+"!")
                Faulty = True

        return Faulty

class HallEffectDevice: #TODO Handle improper setup better.
    # ---------- CONSTRUCTORS ----------
    def __init__(self, DeviceName):
        """
        This is the constructor.
        Usage:

            <Variable-Name> = HallEffectDevice(string DeviceName)
        """

        #Set some semi-private variables.
        self.__DeviceName = DeviceName         #Used to keep track of which probe we're controlling. Cannot be re-set after initialisation.
        self.__Pin = -1                        #Needs to be set.

    # ---------- INFO SETTER FUNCTIONS ----------
    def SetPin(self, Pin):
        """
        Sets the input pin for this hall effect device.
        Usage:

            <HallEffectDevice-Object>.SetPin(int Pin)
        """

        self.__Pin = Pin

    # ---------- INFO GETTER FUNCTIONS ----------
    def GetName(self):
        """
        Returns the name of this probe.
        Usage:

            string <HallEffectDevice-Object>.GetName()
        """

        return self.__DeviceName

    def GetPin(self):
        """
        Returns the pin this probe is using.
        Usage:

            int <HallEffectDevice-Object>.GetPin()
        """

        return self.__Pin

    # ---------- CONTROL FUNCTIONS ---------- 
    def Read(self):
        """
        Returns the state of the input pin.
        Usage:

            bool <HallEffectDevice-Object>.Read()
        """

        return GPIO.input(__Pin)
    
