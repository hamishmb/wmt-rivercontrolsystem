#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 'Temporary Top Up' Logic for the River System Control and Monitoring Software
# Copyright (C) 2021 Wimborne Model Town
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3 or,
# at your option, any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#pylint: disable=logging-not-lazy
#
#Reason (logging-not-lazy): Harder to understand the logging statements that way.

"""
This is the temptopuplogic module, which contains interim control logic for Lady Hanham Pi to provide a daily mains water top-up.

This logic features a manual override function for the G3:S0 mains water inlet
solenoid valve. The manual override can be activated by creating the file
> rivercontrolsystem/overrides/device/S0
containing the word 'on', 'off', or 'auto', where 'rivercontrolsystem' is the
root of the River Control System software package.

A value of 'on' on the first line of the override file forces the solenoid
valve to open, 'off' forces it to close and 'auto' requests normal operation.
If the file is not present, 'auto' is assumed. If the file contains a value
other than these, or if the file is present but not accessible, then 'off' is
assumed. Only the first line of the override file is read, and whitespace is
ignored.

N.B. The solenoid override will override failsafe_end_time.

This logic is intended as an interim measure to reduce the burden of manually
topping up with mains water, until the "full" control logic is available for
the Lady Hanham Pi/SAC module.

When the full logic is available, this Temporary Top Up logic will become
redundant.

.. module:: temptopuplogic.py
    :platform: Linux
    :synopsis: Contains interim control logic for Lady Hanham Pi.

.. moduleauthor:: Patrick Wigmore <pwbugreports@gmx.com>
"""

import logging
import sys
import os.path

# Add root of rivercontrolsystem to path
# this was done using sys.path.insert(0, os.path.abspath('..'))
# but that doesn't work when running unit tests. This does:
sys.path.insert(0, os.path.abspath(os.path.split(os.path.dirname(__file__))[0]))


from Tools import logiccoretools
from Tools.statetools import ControlStateMachineABC, GenericControlState
import datetime

#Don't ask for a logger name, so this works with both main.py
#and the universal monitor.
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

for handler in logging.getLogger('River System Control Software').handlers:
    logger.addHandler(handler)

def reconfigure_logger():
    """
    Reconfigures the logging level for this module.
    """

    logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

    for handler in logging.getLogger('River System Control Software').handlers:
        logger.addHandler(handler)

csm = None
"""
The csm variable holds an instance of the TempTopUpLogic control state
machine, to enable state persistence.

Used by the temptopup_control_logic function.
Initialised by the temptopup_control_logic_setup function.
"""

solenoid = None
"""
The solenoid variable holds a reference to the solenoid valve device object.
It should be initialised by the temptopup_control_logic function.
"""

readings = {}
"""
The readings variable holds a reference to the local readings dictionary.
It should be set by the temptopup_control_logic function.
"""

start_time = (datetime.time(14), datetime.time(14,2))
"""
Defines a window in time during which the daily mains-water top-up can begin.
A tuple. First element is the beginning of the window, second is the end.
The length of this period should be at least 2 minutes to account for the
reading interval.
This does not constrain the end time of the top-up.
"""

failsafe_end_time = datetime.time(15,00)
"""
Defines a cut-off time for the top-up as a last resort failsafe to limit water
wastage in the event of a sensor failure. This should not normally come into
play.
"""

start_level = 500
"""
Mains water top-up will begin when the water is below start_level
"""

stop_level = 500
"""
Mains water top-up will end when the water rises above stop_level
"""

class TempTopUpReadingsParser():
    """
    This class extracts data from sensor readings and presents it
    in a format that's convenient for the Temporary Top Up control logic.
    
    This is probably over the top for temporary logic, but since we
    already have the basic outline for doing a readings parser, lets write
    one anyway, because it gives us error handling we might not otherwise
    think of doing.
    """
    def __init__(self):
        """
        Initialiser. Puts relevant readings data into instance variables.
        """      
        #Get readings, check they are sane and load into self
        failed_to_get_some_readings = False
        
        # When there is no reading available yet in the readings
        # dictionary, we should get a KeyError. If we get a "None"
        # reading, then we'll get an AttributeError when we try to call
        # get_value() on it.
        
        # The Temporary Top Up logic is only interested in the latest
        # reading, so if there is an error getting the reading, we
        # ultimately parse it by throwing a ValueError. The logic will
        # keep doing what it was already doing, until a reading is
        # obtained, so there is no need to feed it the previous reading.
        
        # G1 butts group sensors are at G3:M0, G3:FS0, G3:FS1
        # (The G3 site handles the G1, G2 and G3 butts groups.)
        try:
            G3M0r =  readings["G3:M0"]
            G3M0  =  G3M0r.get_value()
            self.G1_level = int(G3M0.replace("m", ""))
        except (RuntimeError, AttributeError, KeyError) as e:
            self.G1_level = None
            failed_to_get_some_readings = True
            if isinstance(e, AttributeError) and not G3M0r is None:
                raise e
        
        try:
            G3FS0r = readings["G3:FS0"]
            G3FS0  = G3FS0r.get_value()
            if not G3FS0 in ("True", "False"): raise AssertionError
            self.G1_full = G3FS0 == "True"
        except (RuntimeError, AssertionError, AttributeError, KeyError) as e:
            self.G1_full = None
            failed_to_get_some_readings = True
            if isinstance(e, AttributeError) and not G3FS0r is None:
                raise e
        
        try:
            G3FS1r = readings["G3:FS1"]
            G3FS1  = G3FS1r.get_value()
            if not G3FS1 in ("True", "False"): raise AssertionError
            self.G1_empty = G3FS1 == "True"
        except (RuntimeError, AssertionError, AttributeError, KeyError) as e:
            self.G1_empty = None
            failed_to_get_some_readings = True
            if isinstance(e, AttributeError) and not G3FS1r is None:
                raise e
        
        if failed_to_get_some_readings:
            msg = "Error: Could not get readings for one or more devices on "\
                  "butts group G1 (which is within site G3)."
            print(msg)
            logger.error(msg)
        
    
    def _g1sensorContradictionError(self):
        """
        Private method to to print and log an error about G1 appearing
        to be simultaneously full and empty.
        """
        msg = ("\nERROR! G1 Lady Hanham Butts Group reads as full and empty "
               "simultaneously, with sensor readings:\n"
               "G3:FS0 (high) = " + str(self.G1_full) + "\n"
               "G3:FS1 (low) = " + str(self.G1_empty) + "\n"
               "G3:M0 (depth) = " + str(self.G1_level) + "mm\n"
               "Check for sensor faults in G1.")
        print(msg)
        logger.error(msg)
        
        try:
            logiccoretools.log_event("G1 sensors contradict", "ERROR")
        except RuntimeError:
            msg = "Error while trying to log error event over network."
            print(msg)
            logger.error(msg)
    
    def g1NeedsTopUp(self):
        """
        Returns true if G1 needs a top-up
        """
        if (self.G1_full is None
            or self.G1_level is None
            or self.G1_empty is None):
            raise ValueError("Sensor readings unavailable.")
        
        if (self.G1_empty or self.G1_level < start_level):
            if(self.G1_full == False):
                return True
            else:
                self._g1sensorContradictionError()
                
                #The following error could be raised in __init__(), but
                #raising it here avoids stalling the logic if it doesn't
                #actually need to know whether G1 needs a top up.
                raise ValueError("G1 sensor values contradict")
        else:
            return False
    
    def g1ToppedUp(self):
        """
        Returns true if G1 has been fully topped-up.
        """
        if (self.G1_full is None
            or self.G1_level is None
            or self.G1_empty is None):
            raise ValueError("Sensor readings unavailable.")
        
        if (self.G1_full or self.G1_level >= stop_level):
            if(self.G1_empty == False):
                return True
            else:
                self._g1sensorContradictionError()
                
                #The following error could be raised in __init__(), but
                #raising it here avoids stalling the logic if it doesn't
                #actually need to know whether G1 is topped up.
                raise ValueError("G1 sensor values contradict")
        else:
            return False

def G3S0OverrideState():
    """
    This function returns the current state of the mains water inlet
    solenoid manual override; one of 'on', 'off' or 'auto'.
    """
    
    file_root = os.path.abspath(os.path.split(os.path.dirname(__file__))[0])
    
    file_path = file_root + "/overrides/device/S0"
    
    try:
        with open(file_path, "r") as f:
            # read first line only and discard whitespace (e.g. newline)
            file_text = f.readline().strip()
            msg = "Found manual override file: " + file_path
            logger.warn(msg)
    
    except FileNotFoundError:
        # This is the 'normal' case (no manual override requested).
        # So, no need to output messages about it.
        file_text = "auto"
    
    except (PermissionError, IsADirectoryError, TimeoutError):
        msg = ("Found manual override file: " + file_path +
               "...but could not read its value.\n" +
               "Defaulting to 'off'.")
        logger.error(msg)
        file_text = "off"
    
    allowable_values = ["on", "off", "auto"]
    notifiable_values = ["on", "off"]
    
    if file_text not in allowable_values:
        msg = ("The override file did not contain a recognised text value.\n"
               "Defaulting to 'off'.")
        logger.error(msg)
        
        file_text = "off"
    
    if file_text in notifiable_values:
        msg = ("Solenoid is in manual override and will be held '" +
               file_text + "'.")
        logger.warn(msg)
            
    return file_text

class TempTopUpDeviceController():
    """
    This class wraps logiccoretools.attempt_to_control with logging and
    error handling that is common to most Temp Top Up control states.
    """
    def __init__(self, solenoidState):
        """
        Initialiser.
        
        Args:
            solenoidState (string) state to request of G3:S0
        """
        self.solenoidState=solenoidState
        
    
    def controlDevices(self, logEvent=False):
        """
        Sets the valves and pumps to the states configured for this
        device controller.
        """
        try:
            if(self.solenoidState == "enable"):
                solenoid.enable()
            else:
                solenoid.disable()
        
        except (AttributeError, RuntimeError):
            msg = "Error: Error trying to control G3:S0!"
            print(msg)
            logger.error(msg)
        
        if logEvent:
            try:
                logiccoretools.log_event("New device state required: "
                                         "G3:S0: "
                                         + self.solenoidState,
                                         "INFO")
            except RuntimeError:
                msg = "Error while trying to log event over network."
                print(msg)
                logger.error(msg)


# -------------------- Temp Top Up control states ---------------------
# Each state class defines the behaviour of the control logic in that state,
# and the possible state transitions away from that state.

class TTUIdleState(GenericControlState):
    """
    Idle state for the Temporary Top Up control logic; when no top-up is
    underway.
    """
    @staticmethod
    def getStateName():
        return "TTUIdleState"
    
    def logEvent(self, *args):
        try:
            logiccoretools.log_event(*args)
        except RuntimeError as e:
            raise GenericControlState.LogEventError from e
    
    def controlDevices(self, logEvent=False):
        #This state requires the solenoid closed
        dc = TempTopUpDeviceController("disable")
        dc.controlDevices(logEvent)
    
    def stateTransition(self):
        parser = TempTopUpReadingsParser()
        s0_override = G3S0OverrideState() # solenoid override state
        
        try:
            #Evaluate possible transitions to new states
            if s0_override == 'off':
                # Stay in idle state to keep solenoid off
                self.noTransition()
                
            elif s0_override == 'on':
                # Enter topping up state to switch solenoid on
                self.csm.setStateBy(TTUToppingUpState, self)
                
            elif (parser.g1NeedsTopUp()
                  and datetime.datetime.now().time() >= start_time[0]
                  and datetime.datetime.now().time() <= start_time[1]):
                # Start daily top-up
                ri = self.csm.setStateBy(TTUToppingUpState, self)
            
            else:
                self.noTransition()
                    
        except ValueError as e:
            raise GenericControlState.StateTransitionError from e

class TTUToppingUpState(GenericControlState):
    """
    Topping up state for the Temporary Top Up control logic; when a top-up is
    underway.
    """
    @staticmethod
    def getStateName():
        return "TTUToppingUpState"
    
    def logEvent(self, *args):
        try:
            logiccoretools.log_event(*args)
        except RuntimeError as e:
            raise GenericControlState.LogEventError from e
    
    def controlDevices(self, logEvent=False):
        #This state requires the solenoid open
        dc = TempTopUpDeviceController("enable")
        dc.controlDevices(logEvent)
    
    def stateTransition(self):
        parser = TempTopUpReadingsParser()
        s0_override = G3S0OverrideState() # solenoid override state
        
        try:
            #Evaluate possible transitions to new states
            if s0_override == 'on':
                # Stay in topping up state to keep solenoid on
                self.noTransition()
                
            elif s0_override == 'off':
                # Enter idle state to switch solenoid off
                self.csm.setStateBy(TTUIdleState, self)
                
            elif (parser.g1ToppedUp()
                  or datetime.datetime.now().time() >= failsafe_end_time
                  or datetime.datetime.now().time() < start_time[0]):
                # Terminate daily top-up
                ri = self.csm.setStateBy(TTUIdleState, self)
            
            else:
                self.noTransition()
            
        except ValueError as e:
            msg = ("Could not parse sensor readings. "
                   "Falling back to TTUIdleState as failsafe.")
            print(msg)
            logger.error(msg)
            self.csm.setStateBy(TTUIdleState, self)


# ---------------- Temporary Top Up control state machine ------------------
# The control state machine class (TempTopUpControlLogic) defines the
# state machine within which the control states exist.

class TempTopUpControlLogic(ControlStateMachineABC):
    """
    This class represents the temporary top up control logic.
    
    It inherits its main public method "doLogic" from
    ControlStateMachineABC, which, in turn, delegates entirely to the
    object representing the current state.
    
    .. figure:: temptopupstatediagram.png
       :alt:
             The diagram describes the following operation:   
             At the start, the state machine enters the Idle state.
             In the idle state, the G1:S0 mains water inlet solenoid
             valve is closed.
             In Idle state, if the time of day is within the start_time
             range, and the G1 water level is below start_level, then
             the state machine transitions to the Topping Up state.
             In the topping up state, the solenoid valve is open, allowing
             mains water to enter G1 and increase its level.
             In Topping Up state, if the water level reaches or exceeds
             stop_level, or if the time of day is after failsafe_end_time
             or before the start_time range, then the state machine
             transitions into Idle state.
             In addition to this normal operation, a manual override can
             be enabled with a value of 'off', 'on' or 'auto'.
             When the manual override is 'off', all transitions into
             Topping Up state are blocked. If Topping Up is the current
             state, then there will be a transition into Idle state,
             regardless of water level or time of day.
             When the manual override is 'on', all transitions into Idle
             state are blocked. If Idle is the current state, then there
             will be a transition into Topping Up state, regardless of
             water level or time of day.
             (A manual override value of 'auto' has no effect on the
            normal operation.)
    
       This diagram describes the state model for the Temporary Top Up
       control logic. In the diagram, "do/" denotes the action during the
       state.
    
    .. The state diagram was created using Dia (https://live.gnome.org/Dia).
       Source file at ../docs/source/temptopupstatediagram.dia.
    """
    def __init__(self):
        #Run superclass initialiser
        super().__init__()
        
        #Initialise dictionary of allowable states
        self._addState(TTUIdleState)
        self._addState(TTUToppingUpState)
        
        #Set initial state
        self.setState(TTUIdleState)
    
    @staticmethod
    def getStateMachineName():
        return "TempTopUpControlLogic"
