#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Stage Pi Logic for the River System Control and Monitoring Software
# Copyright (C) 2020-2022 Wimborne Model Town
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
#pylint: disable=wrong-import-position
#
#Reason (logging-not-lazy): Harder to understand the logging statements that way.
#Reason (wrong-import-position): Pylint is confused by the need to modify sys.path.

"""
This is the stagepilogic module, which contains control logic for Stage Pi.

.. module:: stagepilogic.py
    :platform: Linux
    :synopsis: Contains control logic for Stage Pi.

.. moduleauthor:: Patrick Wigmore <pwbugreports@gmx.com>
.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>
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

    for _handler in logging.getLogger('River System Control Software').handlers:
        logger.addHandler(_handler)

csm = None #pylint: disable=invalid-name

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
        """
        #Get readings, check they are sane and load into self
        failed_to_get_some_readings = False

        # When there is no reading available yet, get_latest_reading
        # returns None, which we catch as an exception by detecting the
        # AttributeError that results from trying to call
        # None.get_value()

        # The Stage Pi logic is only interested in the latest reading,
        # so if there is an error getting the reading, we ultimately
        # parse it by throwing a ValueError. The logic will keep doing
        # what it was already doing, until a reading is obtained, so
        # there is no need to feed it the previous reading.

        try:
            g4m0_reading = logiccoretools.get_latest_reading("G4", "M0")
            g4m0 = g4m0_reading.get_value()
            self.g4_level = int(g4m0.replace("m", ""))

        except (RuntimeError, AttributeError) as err:
            self.g4_level = None
            failed_to_get_some_readings = True

            if isinstance(err, AttributeError) and not g4m0_reading is None:
                raise err

        try:
            g4fs0_reading = logiccoretools.get_latest_reading("G4", "FS0")
            g4fs0  = g4fs0_reading.get_value()

            if not g4fs0 in ("True", "False"):
                raise AssertionError

            self.g4_full = g4fs0 == "True"

        except (RuntimeError, AssertionError, AttributeError) as err:
            self.g4_full = None
            failed_to_get_some_readings = True

            if isinstance(err, AttributeError) and not g4fs0_reading is None:
                raise err

        try:
            g4fs1_reading = logiccoretools.get_latest_reading("G4", "FS1")
            g4fs1  = g4fs1_reading.get_value()

            if not g4fs1 in ("True", "False"):
                raise AssertionError

            self.g4_empty = g4fs1 == "True"

        except (RuntimeError, AssertionError, AttributeError) as err:
            self.g4_empty = None
            failed_to_get_some_readings = True

            if isinstance(err, AttributeError) and not g4fs1_reading is None:
                raise err

        try:
            g6m0_reading =  logiccoretools.get_latest_reading("G6", "M0")
            g6m0  =  g6m0_reading.get_value()
            self.g6_level = int(g6m0.replace("m", ""))

        except (RuntimeError, AttributeError) as err:
            self.g6_level = None
            failed_to_get_some_readings = True

            if isinstance(err, AttributeError) and not g6m0_reading is None:
                raise err

        try:
            g6fs0_reading = logiccoretools.get_latest_reading("G6", "FS0")
            g6fs0  = g6fs0_reading.get_value()

            if not g6fs0 in ("True", "False"):
                raise AssertionError

            self.g6_is_full = g6fs0 == "True"

        except (RuntimeError, AssertionError, AttributeError) as err:
            self.g6_is_full = None
            failed_to_get_some_readings = True
            if isinstance(err, AttributeError) and not g6fs0_reading is None:
                raise err

        try:
            g6fs1_reading = logiccoretools.get_latest_reading("G6", "FS1")
            g6fs1  = g6fs1_reading.get_value()

            if not g6fs1 in ("True", "False"):
                raise AssertionError

            self.g6_is_empty = g6fs1 == "True"

        except (RuntimeError, AssertionError, AttributeError) as err:
            self.g6_is_empty = None
            failed_to_get_some_readings = True
            if isinstance(err, AttributeError) and not g6fs1_reading is None:
                raise err

        if failed_to_get_some_readings:
            msg = "Error: Could not get readings for one or more devices on "\
                  "G4 or G6"

            print(msg)
            logger.error(msg)

    def _g6sensor_contradiction_error(self):
        """
        Private method to to print and log an error about G6 appearing
        to be simultaneously full and empty.
        """
        msg = ("\nERROR! G6 Stage Butts Group reads as full and empty "
               "simultaneously, with sensor readings:\n"
               "G6:FS0 (high) = " + str(self.g6_is_full) + "\n"
               "G6:FS1 (low) = " + str(self.g6_is_empty) + "\n"
               "G6:M0 (depth) = " + str(self.g6_level) + "mm\n"
               "Check for sensor faults in G6.")

        print(msg)
        logger.error(msg)

        try:
            logiccoretools.log_event("G6 sensors contradict", "ERROR")

        except RuntimeError:
            msg = "Error while trying to log error event over network."
            print(msg)
            logger.error(msg)

    def g6_full(self):
        """
        Returns true if G6 is full
        """
        if self.g6_is_full is None or self.g6_level is None or self.g6_is_empty is None:
            raise ValueError("Sensor readings unavailable.")

        if self.g6_is_full or self.g6_level >= levels["G6Full"]:
            if self.g6_is_empty is False:
                return True

            self._g6sensor_contradiction_error()

            #The following error could be raised in __init__(), but
            #raising it here avoids stalling the logic if it doesn't
            #actually need to know whether G6 is full.
            raise ValueError("G6 sensor values contradict")

        return False

    def g6_empty(self):
        """
        Returns true if G6 is empty (<25mm)
        """
        if (self.g6_is_empty is None or self.g6_level is None or self.g6_is_full is None):
            raise ValueError("Sensor readings unavailable.")

        if self.g6_is_empty or self.g6_level < levels["G6NotEmpty"]:
            if self.g6_is_full is False:
                return True

            self._g6sensor_contradiction_error()

            #The following error could be raised in __init__(), but
            #raising it here avoids stalling the logic if it doesn't
            #actually need to know whether G6 is empty.
            raise ValueError("G6 sensor values contradict")

        return False

    def g4_overfull(self):
        """
        Returns true if G4 is overfull (full to the limit)
        """
        if (self.g4_empty is None
            or self.g4_full is None
            or self.g4_level is None):
            raise ValueError("Sensor readings unavailable.")

        return (not self.g4_empty
                and (self.g4_full or
                     self.g4_level >= levels["G4Overfull"]))

    def g4_full_or_more(self):
        """
        Returns true if G4 is full or more (>900mm)
        """
        if (self.g4_empty is None
            or self.g4_full is None
            or self.g4_level is None):
            raise ValueError("Sensor readings unavailable.")

        return (not self.g4_empty
                and (self.g4_full or
                     self.g4_level >= levels["G4Full"]))

    def g4_very_nearly_full_or_more(self):
        """
        Returns true if G4 level is very nearly full or more (>800mm)
        """
        if (self.g4_empty is None
            or self.g4_full is None
            or self.g4_level is None):
            raise ValueError("Sensor readings unavailable.")

        return (not self.g4_empty
                and (self.g4_full or
                     self.g4_level >= levels["G4VeryNearlyFull"]))

    def g4_nearly_full_or_more(self):
        """
        Returns true if G4 level is nearly full or more (>700mm)
        """
        if (self.g4_empty is None
            or self.g4_full is None
            or self.g4_level is None):
            raise ValueError("Sensor readings unavailable.")

        return (not self.g4_empty
                and (self.g4_full or
                     self.g4_level >= levels["G4NearlyFull"]))

class StagePiDeviceController():
    """
    This class wraps logiccoretools.attempt_to_control with logging and
    error handling that is common to most Stage Pi control states.
    """

    def __init__(self, v12state):
        """
        Initialiser.

        Args:
            v12state (string) state to request of VALVE12:V12
        """
        self.v12state=v12state

    def control_devices(self, log_event=False):
        """
        Sets the valves and pumps to the states configured for this
        device controller.
        """
        try:
            logiccoretools.attempt_to_control("VALVE12",
                                              "V12",
                                              self.v12state)

        except RuntimeError:
            msg = "Error: Error trying to control VALVE12:V12!"
            print(msg)
            logger.error(msg)

        if log_event:
            try:
                logiccoretools.log_event("New device state required: "
                                         "VALVE12:V12: "
                                         + self.v12state,
                                         "INFO")

            except RuntimeError:
                msg = "Error while trying to log event over network."
                print(msg)
                logger.error(msg)

# -------------------- Stage Pi control states ---------------------
# Each state class defines the behaviour of the control logic in that state,
# and the possible state transitions away from that state.

class StagePiInitState(GenericControlState):
    """
    An initial state for the Stage Pi control logic, which doesn't do
    anything except transition into the appropriate state after a cold
    start.
    """

    @staticmethod
    def get_state_name():
        return "StagePiInitState"

    @staticmethod
    def get_preferred_reading_interval():
        # Prefer a fast reading interval until we're in the right state
        return 15

    def log_event(self, *args):
        try:
            logiccoretools.log_event(*args)

        except RuntimeError as err:
            raise GenericControlState.LogEventError from err

    def state_transition(self):
        parser = StagePiReadingsParser()

        try:
            #Prepare to transition to new state
            if parser.g4_overfull():
                self.csm.setStateBy(StagePiG4OverfilledState, self)

            else:
                if parser.g6_empty():
                    self.csm.setStateBy(StagePiG6EmptyState, self)

                elif parser.g4_full_or_more():
                    self.csm.setStateBy(StagePiG4FilledState, self)

                elif parser.g4_very_nearly_full_or_more():
                    self.csm.setStateBy(StagePiG4VeryNearlyFilledState, self)

                elif parser.g4_nearly_full_or_more():
                    self.csm.setStateBy(StagePiG4NearlyFilledState, self)

                else:
                    self.csm.setStateBy(StagePiG4FillingState, self)

        except ValueError as err:
            raise GenericControlState.StateTransitionError from err

class StagePiG4OverfilledState(GenericControlState):
    """
    Stage Pi control logic state when G4 is overfilled
    """

    @staticmethod
    def get_state_name():
        return "StagePiG4OverfilledState"

    def log_event(self, *args):
        try:
            logiccoretools.log_event(*args)

        except RuntimeError as err:
            raise GenericControlState.LogEventError from err

    def control_devices(self, log_event=False):
        #This state requires V12 closed to stop G6-G4 water flow
        device_controller = StagePiDeviceController("0%")
        device_controller.control_devices(log_event)

    def state_transition(self):
        parser = StagePiReadingsParser()

        try:
            #Evaluate possible transitions to new states
            if not parser.g4_overfull():
                if not parser.g6_empty():
                    self.csm.setStateBy(StagePiG4FilledState, self)

                else:
                    self.csm.setStateBy(StagePiG6EmptyState, self)

            #G4 being overfull overrides G6 being empty. If G6 is empty
            #and G4 is still overfilled, then we want to stay in
            #G4OverfilledState, so that water can be pumped back into
            #G6.

            else:
                self.noTransition()

        except ValueError as err:
            raise GenericControlState.StateTransitionError from err

class StagePiG4FilledState(GenericControlState):
    """
    Stage Pi control logic state when G4 is filled
    """

    @staticmethod
    def get_state_name():
        return "StagePiG4FilledState"

    def log_event(self, *args):
        try:
            logiccoretools.log_event(*args)

        except RuntimeError as err:
            raise GenericControlState.LogEventError from err

    def control_devices(self, log_event=False):
        #Close V12 to stop G6/G4 water flow
        device_controller = StagePiDeviceController("0%")
        device_controller.control_devices(log_event)

    def state_transition(self):
        parser = StagePiReadingsParser()

        try:
            #Evaluate possible transitions to new states
            if parser.g4_overfull():
                #If "overfull", unconditionally go into G4OverfilledState
                self.csm.setStateBy(StagePiG4OverfilledState, self)

            elif parser.g6_empty():
                #If G6 empty and G4 not overfull go into G6EmptyState
                self.csm.setStateBy(StagePiG6EmptyState, self)

            elif not parser.g4_full_or_more():
                #If G4 is no longer "full" and G6 is not empty and G4
                #is not overfilled, then go into G4VeryNearlyFilledState
                self.csm.setStateBy(StagePiG4VeryNearlyFilledState, self)

            else:
                self.noTransition()

        except ValueError as err:
            raise GenericControlState.StateTransitionError from err

class StagePiG4VeryNearlyFilledState(GenericControlState):
    """
    Stage Pi control logic state when G4 is very nearly filled
    """

    @staticmethod
    def get_state_name():
        return "StagePiG4VeryNearlyFilledState"

    @staticmethod
    def get_preferred_reading_interval():
        # Prefer a fast reading interval, since we're so close to full
        return 15

    def log_event(self, *args):
        try:
            logiccoretools.log_event(*args)

        except RuntimeError as err:
            raise GenericControlState.LogEventError from err

    def control_devices(self, log_event=False):
        #Open V12 slightly to allow some water flow from G6 to G4
        device_controller = StagePiDeviceController("25%")
        device_controller.control_devices(log_event)

    def state_transition(self):
        parser = StagePiReadingsParser()

        try:
            #Evaluate possible transitions to new states
            if not parser.g6_empty():
                if parser.g4_full_or_more():
                    self.csm.setStateBy(StagePiG4FilledState, self)

                elif not parser.g4_very_nearly_full_or_more():
                    self.csm.setStateBy(StagePiG4NearlyFilledState, self)

                else:
                    self.noTransition()

            else:
                self.csm.setStateBy(StagePiG6EmptyState, self)

        except ValueError as err:
            raise GenericControlState.StateTransitionError from err

class StagePiG4NearlyFilledState(GenericControlState):
    """
    Stage Pi control state when G4 is nearly filled
    """

    @staticmethod
    def get_state_name():
        return "StagePiG4NearlyFilledState"

    @staticmethod
    def get_preferred_reading_interval():
        # Prefer a fastish reading interval since we're near full
        return 30

    def log_event(self, *args):
        try:
            logiccoretools.log_event(*args)

        except RuntimeError as err:
            raise GenericControlState.LogEventError from err

    def control_devices(self, log_event=False):
        #Open V12 a bit to allow some water flow from G6 to G4
        device_controller = StagePiDeviceController("50%")
        device_controller.control_devices(log_event)

    def state_transition(self):
        parser = StagePiReadingsParser()

        try:
            #Evaluate possible transitions to new states
            if not parser.g6_empty():
                if parser.g4_very_nearly_full_or_more():
                    self.csm.setStateBy(StagePiG4VeryNearlyFilledState, self)

                elif not parser.g4_nearly_full_or_more():
                    self.csm.setStateBy(StagePiG4FillingState, self)

                else:
                    self.noTransition()

            else:
                self.csm.setStateBy(StagePiG6EmptyState, self)

        except ValueError as err:
            raise GenericControlState.StateTransitionError from err

class StagePiG4FillingState(GenericControlState):
    """
    Stage Pi control state when G4 is filling and not nearly full
    """

    @staticmethod
    def get_state_name():
        return "StagePiG4FillingState"

    def log_event(self, *args):
        try:
            logiccoretools.log_event(*args)

        except RuntimeError as err:
            raise GenericControlState.LogEventError from err

    def control_devices(self, log_event=False):
        #Open V12 fully to allow water flow from G6 to G4
        device_controller = StagePiDeviceController("100%")
        device_controller.control_devices(log_event)

    def state_transition(self):
        parser = StagePiReadingsParser()

        try:
            #Evaluate possible transitions to new states
            if not parser.g6_empty():
                if parser.g4_nearly_full_or_more():
                    self.csm.setStateBy(StagePiG4NearlyFilledState, self)

                else:
                    self.noTransition()

            else:
                self.csm.setStateBy(StagePiG6EmptyState, self)

        except ValueError as err:
            raise GenericControlState.StateTransitionError from err

class StagePiG6EmptyState(GenericControlState):
    """
    Stage Pi control state when G6 is empty and G4 is NOT overfilled
    """

    @staticmethod
    def get_state_name():
        return "StagePiG6EmptyState"

    def log_event(self, *args):
        try:
            logiccoretools.log_event(*args)

        except RuntimeError as err:
            raise GenericControlState.LogEventError from err

    def control_devices(self, log_event=False):
        #Close V12 fully, since there's no water to flow either
        #direction
        device_controller = StagePiDeviceController("0%")
        device_controller.control_devices(log_event)

    def state_transition(self):
        parser = StagePiReadingsParser()

        try:
            #Evaluate possible transitions to new states

            #Unlike the other four states, we can enter G4OverfilledState
            #even if G6 remains empty
            if parser.g4_overfull():
                self.csm.setStateBy(StagePiG4OverfilledState, self)

            #If G6 is no longer empty, enter the appropriate filling state for
            #the current G4 fill level
            elif not parser.g6_empty():
                if parser.g4_full_or_more():
                    self.csm.setStateBy(StagePiG4FilledState, self)

                elif parser.g4_very_nearly_full_or_more():
                    self.csm.setStateBy(StagePiG4VeryNearlyFilledState, self)

                elif parser.g4_nearly_full_or_more():
                    self.csm.setStateBy(StagePiG4NearlyFilledState, self)

                else:
                    self.csm.setStateBy(StagePiG4FillingState, self)

            else:
                self.noTransition()

        except ValueError as err:
            raise GenericControlState.StateTransitionError from err

# ---------------- Stage Pi control state machine ------------------
# The control state machine class (StagePiControlLogic) defines the
# state machine within which the control states exist.

class StagePiControlLogic(ControlStateMachineABC):
    """
    This class represents the control logic for stagepi.

    It inherits its main public method "doLogic" from
    ControlStateMachineABC, which, in turn, delegates entirely to the
    object representing the current state.

    .. figure:: stagepistatediagram.png
       :alt:
             The diagram describes the following operation:
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
    def get_state_machine_name():
        return "StagePiControlLogic"
