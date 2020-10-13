#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Stage Pi Logic for the River System Control and Monitoring Software
# Copyright (C) 2020 Wimborne Model Town
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
This is the stagepilogic module, which contains control logic for Stage Pi.

.. module:: stagepilogic.py
    :platform: Linux
    :synopsis: Contains control logic for Stage Pi.

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
from Tools.statetools import ControlStateABC, ControlStateMachineABC

#Don't ask for a logger name, so this works with both main.py
#and the universal monitor.
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

for handler in logging.getLogger('River System Control Software').handlers:
    logger.addHandler(handler)

csm = None
"""
The csm variable holds an instance of the StagePiControlLogic control state
machine, to enable state persistence.

Used by the stagepi_control_logic function.
Initialised by the stagepi_control_logic_setup function.
"""

levels = { 
    "G6Full": 975,
    "G6NotEmpty": 25,
    "G4Overfull": 975,
    "G4Full": 900,
    "G4VeryNearlyFull": 800,
    "G4NearlyFull": 700
    }
"""
The levels variable parameterises the relationship between measured
water level and the set of named water levels used by the Stage Pi
logic.

This variable is used in testing the logic.

All of the levels defined here are inclusive lower bounds for the named
levels. The (exclusive) upper bound for each level is implicitly
defined by the lower bound for the next level up (considering levels in
the same butts group).
"""

class StagePiReadingsParser():
    """
    This class extracts data from sensor readings and presents it
    in a format that's convenient for the Stage Pi control logic
    """
    def __init__(self):
        """
        Initialiser. Puts relevant readings data into instance variables.
        
        Throws:
            AssertionError  if the readings fail to pass suitability tests
        """
        
        #Get readings
        try:
            G4M0 =  logiccoretools.get_latest_reading("G4", "M0").get_value()
            G4FS0 = logiccoretools.get_latest_reading("G4", "FS0").get_value()
            G4FS1 = logiccoretools.get_latest_reading("G4", "FS1").get_value()
            G6M0 =  logiccoretools.get_latest_reading("G6", "M0").get_value()
            G6FS0 = logiccoretools.get_latest_reading("G6", "FS0").get_value()
            G6FS1 = logiccoretools.get_latest_reading("G6", "FS1").get_value()
        
        except RuntimeError:
            msg = "Error: Could not get readings for one or more devices on "\
                  "G4 or G6"
            print(msg)
            logger.error(msg)
        
        #Check that the float switch readings are sane.
        assert G4FS0 in ("True", "False")
        assert G4FS1 in ("True", "False")
        assert G6FS0 in ("True", "False")
        assert G6FS1 in ("True", "False")
        
        #Load readings into self
        self.G4_level = int(G4M0.replace("m", ""))
        self.G4_full = G4FS0 == "True"
        self.G4_empty = G4FS1 == "True"
        
        self.G6_level = int(G6M0.replace("m", ""))
        self.G6_full = G6FS0 == "True"
        self.G6_empty = G6FS1 == "True"
    
    def _g6sensorContradictionError(self):
        """
        Private method to to print and log an error about G6 appearing
        to be simultaneously full and empty.
        """
        msg = ("\nERROR! G6 Stage Butts Group reads as full and empty "
               "simultaneously, with sensor readings:\n"
               "G6:FS0 (high) = " + str(self.G6_full) + "\n"
               "G6:FS1 (low) = " + str(self.G6_empty) + "\n"
               "G6:M0 (depth) = " + str(self.G6_level) + "mm\n"
               "Check for sensor faults in G6.")
        print(msg)
        logger.error(msg)
        
        try:
            logiccoretools.log_event("G6 sensors contradict", "ERROR")
        except RuntimeError:
            msg = "Error while trying to log error event over network."
            print(msg)
            logger.error(msg)
    
    def g6Full(self):
        """
        Returns true if G6 is full
        """
        if(self.G6_full or self.G6_level >= levels["G6Full"]):
            if(self.G6_empty == False):
                return True
            else:
                self._g6sensorContradictionError()
                
                #The following error could be raised in __init__(), but
                #raising it here avoids stalling the logic if it doesn't
                #actually need to know whether G6 is full.
                raise ValueError("G6 sensor values contradict")
        else:
            return False
    
    def g6Empty(self):
        """
        Returns true if G6 is empty (<25mm)
        """
        if(self.G6_empty or self.G6_level < levels["G6NotEmpty"]):
            if(self.G6_full == False):
                return True
            else:
                self._g6sensorContradictionError()
                
                #The following error could be raised in __init__(), but
                #raising it here avoids stalling the logic if it doesn't
                #actually need to know whether G6 is empty.
                raise ValueError("G6 sensor values contradict")
        else:
            return False
    
    def g4Overfull(self):
        """
        Returns true if G4 is overfull (full to the limit)
        """
        return (not self.G4_empty
                and (self.G4_full or
                     self.G4_level >= levels["G4Overfull"]))
    
    def g4FullOrMore(self):
        """
        Returns true if G4 is full or more (>900mm)
        """
        return (not self.G4_empty
                and (self.G4_full or
                     self.G4_level >= levels["G4Full"]))
    
    def g4VeryNearlyFullOrMore(self):
        """
        Returns true if G4 level is very nearly full or more (>800mm)
        """
        return (not self.G4_empty
                and (self.G4_full or
                     self.G4_level >= levels["G4VeryNearlyFull"]))
    
    def g4NearlyFullOrMore(self):
        """
        Returns true if G4 level is nearly full or more (>700mm)
        """
        return (not self.G4_empty
                and (self.G4_full or
                     self.G4_level >= levels["G4NearlyFull"]))

# -------------------- Stage Pi control states ---------------------
# Each state class defines the behaviour of the control logic in that state,
# and the possible state transitions away from that state.

class StagePiInitState(ControlStateABC):
    """
    An initial state for the Stage Pi control logic, which doesn't do
    anything except transition into the appropriate state after a cold
    start.
    """
    @staticmethod
    def getStateName():
        return "StagePiInitState"
    
    def setupState(self):
        logger.info("Setting up " + self.getStateName())
        print("Setting up " + self.getStateName())
    
    @staticmethod
    def getPreferredReadingInterval():
        # Prefer a fast reading interval until we're in the right state
        return 15
    
    def doLogic(self, reading_interval):
        ri = self.getPreferredReadingInterval()
        
        #Create readings parser
        try:
            parser = StagePiReadingsParser()
        
        except AssertionError:
            msg = ("Error: Could not initialise StagePiReadingsParser. Readings"
                   " did not meet conditions.")
            print(msg)
            logger.error(msg)
            return ri
        
        try:
            #Prepare to transition to new state
            if parser.g4Overfull():
                ri = self.csm.setStateBy(StagePiG4OverfilledState, self)
    
            else:
                if parser.g6Empty():
                    ri = self.csm.setStateBy(StagePiG6EmptyState, self)
                    
                elif parser.g4FullOrMore():
                    ri = self.csm.setStateBy(StagePiG4FilledState, self)
                    
                elif parser.g4VeryNearlyFullOrMore():
                    ri = self.csm.setStateBy(StagePiG4VeryNearlyFilledState,
                                             self)
                    
                elif parser.g4NearlyFullOrMore():
                    ri = self.csm.setStateBy(StagePiG4NearlyFilledState, self)
                    
                else:
                    ri = self.csm.setStateBy(StagePiG4FillingState, self)
                    
        except ValueError:
            msg = ("Could not parse sensor readings. Control logic is "
                   "stalled.")
            print(msg)
            logger.error(msg)

        return ri

class StagePiG4OverfilledState(ControlStateABC):
    """
    Stage Pi control logic state when G4 is overfilled
    """
    @staticmethod
    def getStateName():
        return "StagePiG4OverfilledState"
    
    def setupState(self):
        logger.info("Setting up state " + self.getStateName())
        print("Setting up state " + self.getStateName())
        
        #Close V12 to stop G6/G4 water flow
        try:
            logiccoretools.attempt_to_control("VALVE12", "V12", "0%")
        
        except RuntimeError:
            msg = "Error: Error trying to control valve V12!"
            print(msg)
            logger.error(msg)
        
        #TODO: When the matrix pump is implemented, instead of closing
        #V12, we should check here whether G6 is full. If it is, we
        #should just close the valve. If it isn't full, then we should
        #pump water in reverse, from G4 to G6.
    
    def doLogic(self, reading_interval):
        ri = self.getPreferredReadingInterval()
        
        try:
            parser = StagePiReadingsParser()
        
        except AssertionError:
            msg = ("Error: Could not initialise StagePiReadingsParser. Readings"
                   " did not meet conditions.")
            print(msg)
            logger.error(msg)
            return ri
        
        try:
            #Evaluate possible transitions to new states
            if not parser.g4Overfull():
                if not parser.g6Empty():
                    ri = self.csm.setStateBy(StagePiG4FilledState, self)
                else:
                    ri = self.csm.setStateBy(StagePiG6EmptyState, self)
            
            #G4 being overfull overrides G6 being empty. If G6 is empty
            #and G4 is still overfilled, then we want to stay in
            #G4OverfilledState, so that water can be pumped back into
            #G6.
            
        except ValueError:
            msg = ("Could not parse sensor readings. Control logic is "
                   "stalled.")
            print(msg)
            logger.error(msg)
        
        return ri
    
class StagePiG4FilledState(ControlStateABC):
    """
    Stage Pi control logic state when G4 is filled
    """
    @staticmethod
    def getStateName():
        return "StagePiG4FilledState"
    
    def setupState(self):
        logger.info("Setting up state " + self.getStateName())
        print("Setting up state " + self.getStateName())
        
        #Close V12 to stop G6/G4 water flow
        try:
            logiccoretools.attempt_to_control("VALVE12", "V12", "0%")
        
        except RuntimeError:
            msg = "Error: Error trying to control valve V12!"
            print(msg)
            logger.error(msg)
        
        #TODO: when the matrix pump is implemented, we need to request it to
        #be turned off and release any lock this Pi holds on using the pump.
        
        #TODO: When the matrix pump is implemented, remember to include
        #a check that the reference we get from the devices dictionary
        #is not a reference to nothing.
    
    def doLogic(self, reading_interval):
        ri = self.getPreferredReadingInterval()
        
        try:
            parser = StagePiReadingsParser()
        
        except AssertionError:
            msg = ("Error: Could not initialise StagePiReadingsParser. Readings"
                   " did not meet conditions.")
            print(msg)
            logger.error(msg)
            return ri
        
        try:
            #Evaluate possible transitions to new states
            if parser.g4Overfull():
                #If "overfull", unconditionally go into G4OverfilledState
                ri = self.csm.setStateBy(StagePiG4OverfilledState, self)
            
            elif parser.g6Empty():
                #If G6 empty and G4 not overfull go into G6EmptyState
                ri = self.csm.setStateBy(StagePiG6EmptyState, self)
                
            elif not parser.g4FullOrMore():
                #If G4 is no longer "full" and G6 is not empty and G4
                #is not overfilled, then go into G4VeryNearlyFilledState
                ri = self.csm.setStateBy(StagePiG4VeryNearlyFilledState,
                                         self)
            
            #else: G4 must be "full", so stay in this state.
        
        except ValueError:
            msg = ("Could not parse sensor readings. Control logic is "
                   "stalled.")
            print(msg)
            logger.error(msg)
        
        return ri

class StagePiG4VeryNearlyFilledState(ControlStateABC):
    """
    Stage Pi control logic state when G4 is very nearly filled
    """
    @staticmethod
    def getStateName():
        return "StagePiG4VeryNearlyFilledState"
    
    @staticmethod
    def getPreferredReadingInterval():
        # Prefer a fast reading interval, since we're so close to full
        return 15
    
    def setupState(self):
        logger.info("Setting up state " + self.getStateName())
        print("Setting up state " + self.getStateName())
        
        #Open V12 slightly to allow some water flow from G6 to G4
        try:
            logiccoretools.attempt_to_control("VALVE12", "V12", "25%")
        
        except RuntimeError:
            msg = "Error: Error trying to control valve V12!"
            print(msg)
            logger.error(msg)
        
        #TODO: when the matrix pump is implemented, we need to:
        #    (a) get the lock to control the pump before we open V12
        #    (b) either open the pump's valves to allow passive water flow,
        #        or start pumping downstream at a low rate
        
        #TODO: When the matrix pump is implemented, remember to include
        #a check that the reference we get from the devices dictionary
        #is not a reference to nothing.
    
    def doLogic(self, reading_interval):
        ri = self.getPreferredReadingInterval()
        
        try:
            parser = StagePiReadingsParser()
        
        except AssertionError:
            msg = ("Error: Could not initialise StagePiReadingsParser. Readings"
                   " did not meet conditions.")
            print(msg)
            logger.error(msg)
            return ri
        
        try:
            #Evaluate possible transitions to new states
            if not parser.g6Empty():
                if parser.g4FullOrMore():
                    ri = self.csm.setStateBy(StagePiG4FilledState, self)
                    
                elif not parser.g4VeryNearlyFullOrMore():
                    ri = self.csm.setStateBy(StagePiG4NearlyFilledState, self)
                
            else:
                ri = self.csm.setStateBy(StagePiG6EmptyState, self)
        
        except ValueError:
            msg = ("Could not parse sensor readings. Control logic is "
                   "stalled.")
            print(msg)
            logger.error(msg)
        
        return ri

class StagePiG4NearlyFilledState(ControlStateABC):
    """
    Stage Pi control state when G4 is nearly filled
    """
    @staticmethod
    def getStateName():
        return "StagePiG4NearlyFilledState"
    
    @staticmethod
    def getPreferredReadingInterval():
        # Prefer a fastish reading interval since we're near full
        return 30
    
    def setupState(self):
        logger.info("Setting up state " + self.getStateName())
        print("Setting up state " + self.getStateName())
        
        #Open V12 a bit to allow some water flow from G6 to G4
        try:
            logiccoretools.attempt_to_control("VALVE12", "V12", "50%")
        
        except RuntimeError:
            msg = "Error: Error trying to control valve V12!"
            print(msg)
            logger.error(msg)
        
        #TODO: when the matrix pump is implemented, we need to:
        #    (a) get the lock to control the pump before we open V12
        #    (b) either open the pump's valves to allow passive water flow,
        #        or start pumping downstream at a medium rate
        
        #TODO: When the matrix pump is implemented, remember to include
        #a check that the reference we get from the devices dictionary
        #is not a reference to nothing.
    
    def doLogic(self, reading_interval):
        ri = self.getPreferredReadingInterval()
        
        try:
            parser = StagePiReadingsParser()
        
        except AssertionError:
            msg = ("Error: Could not initialise StagePiReadingsParser. Readings"
                   " did not meet conditions.")
            print(msg)
            logger.error(msg)
            return ri
        
        try:
            #Evaluate possible transitions to new states
            if not parser.g6Empty():
                if parser.g4VeryNearlyFullOrMore():
                    ri = self.csm.setStateBy(StagePiG4VeryNearlyFilledState,
                                             self)
                    
                elif not parser.g4NearlyFullOrMore():
                    ri = self.csm.setStateBy(StagePiG4FillingState, self)
                
            else:
                ri = self.csm.setStateBy(StagePiG6EmptyState, self)
        
        except ValueError:
            msg = ("Could not parse sensor readings. Control logic is "
                   "stalled.")
            print(msg)
            logger.error(msg)
        
        return ri

class StagePiG4FillingState(ControlStateABC):
    """
    Stage Pi control state when G4 is filling and not nearly full
    """
    @staticmethod
    def getStateName():
        return "StagePiG4FillingState"
    
    def setupState(self):
        logger.info("Setting up state " + self.getStateName())
        print("Setting up state " + self.getStateName())
        
        #Open V12 fully to allow water flow from G6 to G4
        try:
            logiccoretools.attempt_to_control("VALVE12", "V12", "100%")
        
        except RuntimeError:
            msg = "Error: Error trying to control valve V12!"
            print(msg)
            logger.error(msg)
        
        #TODO: when the matrix pump is implemented, we need to:
        #    (a) get the lock to control the pump before we open V12
        #    (b) either open the pump's valves to allow passive water flow,
        #        or start pumping downstream at a high rate
        
        #TODO: When the matrix pump is implemented, remember to include
        #a check that the reference we get from the devices dictionary
        #is not a reference to nothing.
    
    def doLogic(self, reading_interval):
        ri = self.getPreferredReadingInterval()
        
        try:
            parser = StagePiReadingsParser()
        
        except AssertionError:
            msg = ("Error: Could not initialise StagePiReadingsParser. Readings"
                   " did not meet conditions.")
            print(msg)
            logger.error(msg)
            return ri
        
        try:
            #Evaluate possible transitions to new states
            if not parser.g6Empty():
                if parser.g4NearlyFullOrMore():
                    ri = self.csm.setStateBy(StagePiG4NearlyFilledState, self)
                    
            else:
                ri = self.csm.setStateBy(StagePiG6EmptyState, self)
        
        except ValueError:
            msg = ("Could not parse sensor readings. Control logic is "
                   "stalled.")
            print(msg)
            logger.error(msg)
        
        return ri
    
class StagePiG6EmptyState(ControlStateABC):
    """
    Stage Pi control state when G6 is empty and G4 is NOT overfilled
    """
    @staticmethod
    def getStateName():
        return "StagePiG6EmptyState"
    
    def setupState(self):
        logger.info("Setting up state " + self.getStateName())
        print("Setting up state " + self.getStateName())
        
        #Close V12 fully, since there's no water to flow either direction
        try:
            logiccoretools.attempt_to_control("VALVE12", "V12", "0%")
        
        except RuntimeError:
            msg = "Error: Error trying to control valve V12!"
            print(msg)
            logger.error(msg)
        
        #TODO: when the matrix pump is implemented, we need to request it to
        #be turned off and release any lock this Pi holds on using the pump.
        
        #TODO: When the matrix pump is implemented, remember to include
        #a check that the reference we get from the devices dictionary
        #is not a reference to nothing.
    
    def doLogic(self, reading_interval):
        ri = self.getPreferredReadingInterval()
        
        try:
            parser = StagePiReadingsParser()
        
        except AssertionError:
            msg = ("Error: Could not initialise StagePiReadingsParser. Readings"
                   " did not meet conditions.")
            print(msg)
            logger.error(msg)
            return ri
        
        try:
            #Evaluate possible transitions to new states
            
            #Unlike the other four states, we can enter G4OverfilledState even if
            #G6 remains empty
            if(parser.g4Overfull()):
                ri = self.csm.setStateBy(StagePiG4OverfilledState, self)
            
            #If G6 is no longer empty, enter the appropriate filling state for
            #the current G4 fill level
            elif not parser.g6Empty():
                if parser.g4FullOrMore():
                    ri = self.csm.setStateBy(StagePiG4FilledState, self)
                
                elif parser.g4VeryNearlyFullOrMore():
                    ri = self.csm.setStateBy(StagePiG4VeryNearlyFilledState,
                                             self)
                
                elif parser.g4NearlyFullOrMore():
                    ri = self.csm.setStateBy(StagePiG4NearlyFilledState, self)
                
                else:
                    ri = self.csm.setStateBy(StagePiG4FillingState, self)
        
        except ValueError:
            msg = ("Could not parse sensor readings. Control logic is "
                   "stalled.")
            print(msg)
            logger.error(msg)
        
        return ri

# ---------------- Stage Pi control state machine ------------------
# The control state machine class (StagePiControlLogic) defines the
# state machine within which the control states exist.

class StagePiControlLogic(ControlStateMachineABC):
    """
    This class represents the control logic for stagepi.
    
    It inherits its main public method "doLogic" from
    ControlStateMachineABC, which, in turn, delegates entirely to the
    object representing the current state.
    
    .. figure:: ../docs/source/stagepistatediagram.png
       :alt: The diagram describes the following operation:
             
             If G6 is empty, then there is nothing to do until either G6 is no
             longer empty, or G4 becomes overfilled. Sit in "G6 Empty" state.
            
             If G6 is not empty, then transfer water from G6 to G4 until either
             G4 is filled or G6 is empty. A series of fill level states are
             defined for G4 based on the rising or falling level in G4, each
             with a different rate of water transfer. ("G4 Overfilled",
             "G4 Filled", "G4 Very Nearly Filled", "G4 Nearly Filled" and, the
             least full, "G4 Filling".)
             
             Regardless of whether or not G6 is empty, if G4 becomes overfilled,
             (the "G4 Overfilled" state) water is pumped from G4 to G6 to
             prevent G4 from overflowing.
             
             If the matrix pump is not available, actions involving it are not
             taken.
    
       This diagram describes the state model for the Stage Pi control logic. In
       the diagram, "entry/" denotes the action upon first entering the state
       and "do/" denotes the action during the state.
    
    .. The state diagram was created using Dia (https://live.gnome.org/Dia).
       Source file at ../docs/source/stagepistatediagram.dia.
    """
    def __init__(self):
        #Run superclass initialiser
        super().__init__()
        
        #Initialise dictionary of allowable states
        self._addState(StagePiInitState)
        self._addState(StagePiG4OverfilledState)
        self._addState(StagePiG4FilledState)
        self._addState(StagePiG4VeryNearlyFilledState)
        self._addState(StagePiG4NearlyFilledState)
        self._addState(StagePiG4FillingState)
        self._addState(StagePiG6EmptyState)
        
        #Set initial state
        self.setState(StagePiInitState)
    
    @staticmethod
    def getStateMachineName():
        return "StagePiControlLogic"