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

#Standard Imports.
import RPi.GPIO as GPIO

import time

#TODO Check that the change to BCM hasn't screwed anything up.
GPIO.setmode(GPIO.BCM)

class BaseDeviceClass: #NOTE: Should this be in coretools?
    # ---------- CONSTRUCTOR ----------
    def __init__(self, Name):
        """
        This is the constructor.
        It is not intended to be used except as part of the initialistion for a derived class.
        """

        #Set some semi-private variables.
        self._Name = Name                   #Just a label.
        self._Pin = -1                      #Needs to be set/deleted.
        self._Pins = []                     #Needs to be set/deleted.
        self._RPins = []                    #Needs to be set/deleted.

    # ---------- INFO SETTER FUNCTIONS ---------- NOTE: If we aren't going to use some of these/they aren't applicable in some derived classes, they can be removed from the derived classes (at least sort of).
    def SetPin(self, Pin): #FIXME: Check if this Pin is already in use. If so throw an error. Also check if this pin is a valid input pin.
        """
        Sets the pin for the device.
        Usage:

            <Device-Object>.SetPin(int Pin)
        """
        self._Pin = Pin

        GPIO.setup(self._Pin, GPIO.IN)

    def SetPins(self, Pins):
        """
        Sets the pins this device will use (from low to high if a resistance probe).
        Usage:

            <Device-Object>.SetPins(tuple Pins)
        """

        self._Pins = Pins
        self._RPins = Pins[::-1]

        #Setup the pins.
        #From lowest to highest, inputs.
        for Pin in self._Pins:
            GPIO.setup(Pin, GPIO.IN)

    # ---------- INFO GETTER FUNCTIONS ---------- NOTE: If we aren't going to use some of these/they aren't applicable in some derived classes, they can be removed from the derived classes (at least sort of).
    def GetName(self):
        """
        Returns the name of the device this object is representing.
        Usage:

            str <Device-Object>.GetName()
        """

        return self._Name

    def GetPin(self):
        """
        Returns the pin for this device.
        Usage:

            int <Device-Object>.GetControlPin()
        """

        return self._Pin

    def GetPins(self):
        """
        Returns the pins for this device (from low to high if a resistance probe).
        Usage:

            tuple <Device-Object>.GetPins()
        """

        return self._Pins

class Motor(BaseDeviceClass):
    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name): 
        """
        This is the constructor.
        Usage:

            <Variable-Name> = Motor(str Name)
        """

        #Call the base class constructor.
        BaseDeviceClass.__init__(self, Name)

        #Delete some unwanted variables.
        del self._Pins
        del self._RPins

        #Set some semi-private variables.
        self._State = False                 #Motor is initialised to be off.
        self._IsVariableSpeed = False       #Assume we don't have PWM by default.
        self._PWMPin = -1                   #Needs to be set.

    # ---------- OVERRIDE IRRELEVANT FUNCTIONS ----------
    def SetPins(self, Pins):
        raise NotImplementedError

    def GetPins(self):
        raise NotImplementedError

    # ---------- INFO SETTER FUNCTIONS ----------
    def SetPWMAvailable(self, PWMAvailable, PWMPin): #TODO Hardware check to determine if PWM is avaiable.
        """
        Enables/Disables PWM support.
        Usage:

            <Motor-Object>.SetPWMAvailable(bool PWMAvailable, int PWMPin)
        """

        self._IsVariableSpeed = PWMAvailable
        self._PWMPin = PWMPin

    # ---------- INFO GETTER FUNCTIONS ----------
    def SupportsPWM(self):
        """
        Returns True if PWM is supported for this motor. Else False.
        Usage:

            bool <Motor-Object>.SupportsPWM()
        """

        return self._IsVariableSpeed

    # ---------- CONTROL FUNCTIONS ----------
    def TurnOn(self):
        """
        Turn the motor on. Returns True if successful, false if not.
        Usage:

            bool <Motor-Object>.TurnOn()
        """

        #Return false if control pin isn't set.
        if self._Pin == -1:
            return False

        #Turn the pin on.
        GPIO.output(self._Pin, True)

        return True

    def TurnOff(self):
        """
        Turn the motor off. Returns True if successful, false if not.
        Usage:

            bool <Motor-Object>.TurnOff()
        """

        #Return false if control pin isn't set.
        if self._Pin == -1:
            return False

        #Turn the pin off.
        GPIO.output(self._Pin, False)

        return True

# -------------------- SENSOR PROBES --------------------

class CapacitiveProbe(BaseDeviceClass):
    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """
        This is the constructor.
        Usage:

            <Variable-Name> = CapacitiveProbe(string ProbeName)
        """
        #Call the base class constructor.
        BaseDeviceClass.__init__(self, Name)

        #Delete some unwanted variables and methods.
        del self._Pins
        del self._RPins

        #Set some semi-private variables.
        self._Detections = 0                #Internal use only.

    # ---------- OVERRIDE IRRELEVANT FUNCTIONS ----------
    def SetPins(self, Pins):
        raise NotImplementedError

    def GetPins(self):
        raise NotImplementedError

    # ---------- PRIVATE FUNCTIONS ----------
    def IncrementDetections(self, channel):
        """Called when a falling edge is detected. Adds 1 to the number of falling edges detected"""
        self._Detections += 1

    # ---------- CONTROL FUNCTIONS ----------
    def GetLevel(self):
        """
        Returns the level of water. Takes readings for 5 seconds and then averages the result.
        Usage:

            int <CapacitiveProbe-Object>.GetLevel()
        """
        self._Detections = 0

        #Automatically call our function when a falling edge is detected.
        GPIO.add_event_detect(self._Pin, GPIO.FALLING, callback=self.IncrementDetections)

        time.sleep(5)

        #Stop calling our function.
        GPIO.remove_event_detect(self._Pin)

        #Use integer divison '//' because it's fast.
        Freq = self._Detections // 5 #Because we're measuring over 5 seconds, take the mean average over 5 seconds.

        return Freq

class ResistanceProbe(BaseDeviceClass):
    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """
        This is the constructor.
        Usage:

            <Variable-Name> = ResistanceProbe(string ProbeName)
        """
        #Call the base class constructor.
        BaseDeviceClass.__init__(self, Name)

        #Delete some unwanted variables and methods.
        del self._Pin

        #Set some semi-private variables.
        self._ActiveState = False           #Active low by default.

    # ---------- OVERRIDE IRRELEVANT FUNCTIONS ----------
    def SetPin(self, Pins):
        raise NotImplementedError

    def GetPin(self):
        raise NotImplementedError

    # ---------- INFO SETTER FUNCTIONS ----------
    def SetActiveState(self, State):
        """
        Sets the active state for the pins. True for active high, False for active low.
        Usage:

            <ResistanceProbe-Object>.SetActiveState(bool State)
        """

        self._ActiveState = State

    # ---------- INFO GETTER FUNCTIONS ----------
    def GetActiveState(self):
        """
        Returns the active state for the pins.
        Usage:

            bool <ResistanceProbe-Object>.GetActiveState()
        """

        return self._ActiveState

    # ---------- CONTROL FUNCTIONS ----------
    def GetLevel(self):
        """
        Gets the level of the water in the probe.
        Usage:

            (int, string) <ResistanceProbe-Object>.GetLevel()
        """

        for Pin in self._RPins:
            #Ignore pins until we find one that is in the active state.
            if GPIO.input(Pin) != self._ActiveState:
                continue

            #This pin must be active.
            Index = self._Pins.index(Pin)

            #Log the states of all the pins.
            StateText = ""

            for Pin in self._Pins:
                StateText += str(GPIO.input(Pin))

            #Check for faults.
            StateText = self.CheckForFaults(Index, StateText)

            #Return the level, assume pin 0 is at 0mm. Also return FaultText
            return Index*100, StateText

        #No pins were high.
        return -1, "1111111111"

    def CheckForFaults(self, HighestActivePin, StateText): #TODO setup and use a logger for this (later).
        """Checks for faults in the sensor. Isn't capable of finding all faults without another sensor to compare against.
        Usage:

            bool <ResistanceProbe-Object>.CheckForFaults(int HighestActivePin)
        """
        #Must convert string to int first, because any string except "" evals to boolean True. 
       
        FaultText = ""

        #All pins before this one should be active.
        for Pin in StateText[:HighestActivePin]:
            if bool(int(Pin)) != self._ActiveState:
                print("FAULT DETECTED")
                FaultText = "FAULT DETECTED"

        #All pins after this one should be inactive.
        for Pin in StateText[HighestActivePin+1:]:
            if bool(int(Pin)) == self._ActiveState:
                print("FAULT DETECTED")
                FaultText = "FAULT DETECTED"

        return StateText+" "+FaultText

class HallEffectDevice(BaseDeviceClass):
    # ---------- CONSTRUCTORS ----------
    def __init__(self, Name):
        """
        This is the constructor.
        Usage:

            <Variable-Name> = HallEffectDevice(string DeviceName)
        """

        #Call the base class costructor.
        BaseDeviceClass.__init__(self, Name)

        #Delete some unwanted variables and methods.
        del self._Pins
        del self._RPins

        #Set some semi-private variables.
        self._Detections = 0                  #Internal use only.

    # ---------- OVERRIDE IRRELEVANT FUNCTIONS ----------
    def SetPins(self, Pins):
        raise NotImplementedError

    def GetPins(self):
        raise NotImplementedError

    # ---------- PRIVATE FUNCTIONS ----------
    def IncrementDetections(self, channel):
        """Called when a falling edge is detected. Adds 1 to the number of falling edges detected"""
        self._Detections += 1

    # ---------- CONTROL FUNCTIONS ---------- 
    def GetRPM(self):
        """
        Returns the rate at with the hall effect device is rotating. Takes readings for 5 seconds and then averages the result.
        Usage:

            int <HallEffectDevice-Object>.GetRPM()
        """
        self._Detections = 0

        #Automatically call our function when a falling edge is detected.
        GPIO.add_event_detect(self._Pin, GPIO.FALLING, callback=self.IncrementDetections)

        time.sleep(5)

        #Stop calling our function.
        GPIO.remove_event_detect(self._Pin)

        #Use integer divison '//' because it's fast.
        RevsPer5Sec = self._Detections // 5 #Because we're measuring over 5 seconds, take the mean average over 5 seconds.

        #Then multiply by 12 to get RPM.
        RPM = RevsPer5Sec * 12

        return RPM    
