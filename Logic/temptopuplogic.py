#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 'Temporary Top Up' Logic for the River System Control and Monitoring Software
# Copyright (C) 2021-2022 Wimborne Model Town
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
This is the temptopuplogic module, which contains interim control logic for Lady
Hanham Pi to provide a daily mains water top-up.

This logic features a manual override function for the G3:S0 mains water inlet
solenoid valve. The manual override can be activated by creating the file::

    rivercontrolsystem/overrides/device/S0

containing the word 'on', 'off', 'auto', 'remote/off' or 'remote/auto', where
'rivercontrolsystem' is the root of the River Control System software package.

If the file contains a value other than these, or if the file is present but not
accessible, then 'off' is assumed. Only the first line of the override file is
read, and whitespace is ignored.

If the override file contains a value of:

- 'on', the solenoid valve is held open indefinitely
- 'off', the solenoid valve is held closed indefinitely
- 'auto', normal operation occurs; i.e. no override
- 'remote/off', a remote override is applied, with fallback to 'off'
- 'remote/auto', a remote override is applied, with fallback to 'auto'

For remote overrides, use logiccoretools device control to request a G3:S0
device state of:

- 'None', to make no request and enter the fallback state
- 'ON', to hold the solenoid valve open indefinitely
- 'OFF', to hold the solenoid valve closed indefinitely, or
- 'AUTO' to request automatic operation.

The fallback state for 'remote/off' and 'remote/auto' occurs when the
requested state is 'None', but also when there is a failure to determine the
requested state (for example, due to a network failure or a database failure).

N.B. The solenoid override will override FAILSAFE_END_TIME. Do not leave an 'on'
override unattended!

This logic is intended as an interim measure to reduce the burden of manually
topping up with mains water, until the "full" control logic is available for
the Lady Hanham Pi/SAC module.

When the full logic is available, this Temporary Top Up logic will become
redundant.

.. module:: temptopuplogic.py
    :platform: Linux
    :synopsis: Contains interim control logic for Lady Hanham Pi.

.. moduleauthor:: Patrick Wigmore <pwbugreports@gmx.com>
.. moduleauthor:: Hamish McIntyre-Bhatty <contact@hamishmb.com>
"""

import logging
import sys
import os.path
import datetime

# Add root of rivercontrolsystem to path
# this was done using sys.path.insert(0, os.path.abspath('..'))
# but that doesn't work when running unit tests. This does:
sys.path.insert(0, os.path.abspath(os.path.split(os.path.dirname(__file__))[0]))

from Tools import logiccoretools
from Tools.coretools import rcs_print as print #pylint: disable=redefined-builtin
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
The csm variable holds an instance of the TempTopUpLogic control state
machine, to enable state persistence.

Used by the temptopup_control_logic function.
Initialised by the temptopup_control_logic_setup function.
"""

solenoid = None #pylint: disable=invalid-name
"""
The solenoid variable holds a reference to the solenoid valve device object.
It should be initialised by the temptopup_control_logic function.
"""

readings = {}
"""
The readings variable holds a reference to the local readings dictionary.
It should be set by the temptopup_control_logic function.
"""

START_TIME = (datetime.time(14), datetime.time(14,2))
"""
Defines a window in time during which the daily mains-water top-up can begin.
A tuple. First element is the beginning of the window, second is the end.
The length of this period should be at least 2 minutes to account for the
reading interval.
This does not constrain the end time of the top-up.
"""

FAILSAFE_END_TIME = datetime.time(15,00)
"""
Defines a cut-off time for the top-up as a last resort failsafe to limit water
wastage in the event of a sensor failure. This should not normally come into
play.
"""

START_LEVEL = 500
"""
Mains water top-up will begin when the water is below START_LEVEL
"""

STOP_LEVEL = 500
"""
Mains water top-up will end when the water rises above STOP_LEVEL
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
            g3m0_reading =  readings["G3:M0"]
            g3m0  =  g3m0_reading.get_value()
            self.g1_level = int(g3m0.replace("m", ""))

        except (RuntimeError, AttributeError, KeyError) as err:
            self.g1_level = None
            failed_to_get_some_readings = True

            if isinstance(err, AttributeError) and not g3m0_reading is None:
                raise err

        try:
            g3fs0_reading = readings["G3:FS0"]
            g3fs0  = g3fs0_reading.get_value()

            if not g3fs0 in ("True", "False"):
                raise AssertionError

            self.g1_is_full = g3fs0 == "True"

        except (RuntimeError, AssertionError, AttributeError, KeyError) as err:
            self.g1_is_full = None
            failed_to_get_some_readings = True

            if isinstance(err, AttributeError) and not g3fs0_reading is None:
                raise err

        try:
            g3fs1_reading = readings["G3:FS1"]
            g3fs1  = g3fs1_reading.get_value()

            if not g3fs1 in ("True", "False"):
                raise AssertionError

            self.g1_is_empty = g3fs1 == "True"

        except (RuntimeError, AssertionError, AttributeError, KeyError) as err:
            self.g1_is_empty = None
            failed_to_get_some_readings = True

            if isinstance(err, AttributeError) and not g3fs1_reading is None:
                raise err

        if failed_to_get_some_readings:
            msg = "Error: Could not get readings for one or more devices on "\
                  "butts group G1 (which is within site G3)."

            print(msg, level="error")
            logger.error(msg)

    def _g1sensor_contradiction_error(self):
        """
        Private method to to print and log an error about G1 appearing
        to be simultaneously full and empty.
        """
        msg = ("\nERROR! G1 Lady Hanham Butts Group reads as full and empty "
               "simultaneously, with sensor readings:\n"
               "G3:FS0 (high) = " + str(self.g1_is_full) + "\n"
               "G3:FS1 (low) = " + str(self.g1_is_empty) + "\n"
               "G3:M0 (depth) = " + str(self.g1_level) + "mm\n"
               "Check for sensor faults in G1.")

        print(msg, level="error")
        logger.error(msg)

        try:
            logiccoretools.log_event("G1 sensors contradict", "ERROR")

        except RuntimeError:
            msg = "Error while trying to log error event over network."
            print(msg, level="error")
            logger.error(msg)

    def g1_needs_top_up(self):
        """
        Returns true if G1 needs a top-up
        """
        if self.g1_is_full is None or self.g1_level is None or self.g1_is_empty is None:
            raise ValueError("Sensor readings unavailable.")

        if self.g1_is_empty or self.g1_level < START_LEVEL:
            if self.g1_is_full is False:
                return True

            self._g1sensor_contradiction_error()

            #The following error could be raised in __init__(), but
            #raising it here avoids stalling the logic if it doesn't
            #actually need to know whether G1 needs a top up.
            raise ValueError("G1 sensor values contradict")

        return False

    def g1_topped_up(self):
        """
        Returns true if G1 has been fully topped-up.
        """
        if self.g1_is_full is None or self.g1_level is None or self.g1_is_empty is None:
            raise ValueError("Sensor readings unavailable.")

        if self.g1_is_full or self.g1_level >= STOP_LEVEL:
            if self.g1_is_empty is False:
                return True

            self._g1sensor_contradiction_error()

            #The following error could be raised in __init__(), but
            #raising it here avoids stalling the logic if it doesn't
            #actually need to know whether G1 is topped up.
            raise ValueError("G1 sensor values contradict")

        return False

def g3s0_override_state():
    """
    This function returns the current state of the mains water inlet
    solenoid manual override; one of 'on', 'off' or 'auto'.
    """

    file_root = os.path.abspath(os.path.split(os.path.dirname(__file__))[0])

    file_path = file_root + "/overrides/device/S0"

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            # read first line only and discard whitespace (e.g. newline)
            ovr_state = file.readline().strip()
            msg = "Found manual override file: " + file_path
            logger.warning(msg)

    except FileNotFoundError:
        # This is the 'normal' case (no manual override requested).
        # So, no need to output messages about it.
        ovr_state = "auto"

    except (PermissionError, IsADirectoryError, TimeoutError):
        msg = ("Found manual override file: " + file_path +
               "...but could not read its value.\n" +
               "Defaulting to 'off'.")
        logger.error(msg)
        ovr_state = "off"

    # Values allowed in the FILE
    allowable_values = ("on", "off", "auto", "remote/off", "remote/auto")

    if ovr_state not in allowable_values:
        msg = ("The override file did not contain a recognised text value.\n"
               "Defaulting to 'off'.")

        logger.error(msg)

        ovr_state = "off"

    if ovr_state in ("remote/off", "remote/auto"):
        logger.warning("Solenoid is under remote manual override.")

        try:
            # Device state should be in second (1th) element of tuple
            # Convert to lowercase for case-insensitivity
            remote_ovr = str(logiccoretools.get_state("G3","S0")[1]).lower()

        except RuntimeError:
            remote_ovr = None

        if remote_ovr in ("on", "off", "auto"):
            ovr_state = remote_ovr

        else:
            # There's no override.

            # Output an explanation for why there's no override
            # (Test for "none" not "None", because converted to lowercase)
            if remote_ovr == "none":
                logger.info("Remote control requests no solenoid override "
                            "(requested state: 'None').")

            elif remote_ovr is None:
                logger.error("Error while trying to check whether an override "
                             "state has been requested remotely.")

            else:
                logger.error("Unrecognised remote solenoid override state "
                             "request: '" + remote_ovr + "'.")

            # Apply the "no override", defaulting to "off" or "auto"
            # as applicable
            if ovr_state == "remote/off":
                ovr_state = "off"
                msg = ("Defaulting solenoid to 'off' while in "
                      "'remote/off' mode.")

            else: # ovr_state == "remote_auto"
                ovr_state = "auto"
                msg = ("Defaulting solenoid to 'auto' while in "
                       "'remote/auto' mode.")

            logger.info(msg)

    notifiable_values = ("on", "off")

    if ovr_state in notifiable_values:
        msg = ("Solenoid is in manual override and will be held '" +
               ovr_state + "'.")

        logger.warning(msg)

    return ovr_state

class TempTopUpDeviceController():
    """
    This class wraps logiccoretools.attempt_to_control with logging and
    error handling that is common to most Temp Top Up control states.
    """

    def __init__(self, solenoid_state):
        """
        Initialiser.

        Args:
            solenoid_state (string) state to request of G3:S0
        """
        self.solenoid_state = solenoid_state

    def control_devices(self, log_event=False):
        """
        Sets the valves and pumps to the states configured for this
        device controller.
        """

        try:
            if self.solenoid_state == "enable":
                solenoid.enable()

            else:
                solenoid.disable()

        except (AttributeError, RuntimeError):
            msg = "Error: Error trying to control G3:S0!"
            print(msg, level="error")
            logger.error(msg)

        if log_event:
            try:
                logiccoretools.log_event("New device state required: "
                                         "G3:S0: "
                                         + self.solenoid_state,
                                         "INFO")

            except RuntimeError:
                msg = "Error while trying to log event over network."
                print(msg, level="error")
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
    def get_state_name():
        return "TTUIdleState"

    def log_event(self, *args):
        try:
            logiccoretools.log_event(*args)

        except RuntimeError as err:
            raise GenericControlState.LogEventError from err

    def control_devices(self, log_event=False):
        #This state requires the solenoid closed
        device_controller = TempTopUpDeviceController("disable")
        device_controller.control_devices(log_event)

    def state_transition(self):
        parser = TempTopUpReadingsParser()
        s0_override = g3s0_override_state() # solenoid override state

        try:
            #Evaluate possible transitions to new states
            if s0_override == 'off':
                # Stay in idle state to keep solenoid off
                self.no_transition()

            elif s0_override == 'on':
                # Enter topping up state to switch solenoid on
                self.csm.set_state_by(TTUToppingUpState, self)

            elif (parser.g1_needs_top_up()
                  and datetime.datetime.now().time() >= START_TIME[0]
                  and datetime.datetime.now().time() <= START_TIME[1]):
                # Start daily top-up
                self.csm.set_state_by(TTUToppingUpState, self)

            else:
                self.no_transition()

        except ValueError as err:
            raise GenericControlState.StateTransitionError from err

class TTUToppingUpState(GenericControlState):
    """
    Topping up state for the Temporary Top Up control logic; when a top-up is
    underway.
    """

    @staticmethod
    def get_state_name():
        return "TTUToppingUpState"

    def log_event(self, *args):
        try:
            logiccoretools.log_event(*args)

        except RuntimeError as err:
            raise GenericControlState.LogEventError from err

    def control_devices(self, log_event=False):
        #This state requires the solenoid open
        device_controller = TempTopUpDeviceController("enable")
        device_controller.control_devices(log_event)

    def state_transition(self):
        parser = TempTopUpReadingsParser()
        s0_override = g3s0_override_state() # solenoid override state

        try:
            #Evaluate possible transitions to new states
            if s0_override == 'on':
                # Stay in topping up state to keep solenoid on
                self.no_transition()

            elif s0_override == 'off':
                # Enter idle state to switch solenoid off
                self.csm.set_state_by(TTUIdleState, self)

            elif (parser.g1_topped_up()
                  or datetime.datetime.now().time() >= FAILSAFE_END_TIME
                  or datetime.datetime.now().time() < START_TIME[0]):
                # Terminate daily top-up
                self.csm.set_state_by(TTUIdleState, self)

            else:
                self.no_transition()

        except ValueError:
            msg = ("Could not parse sensor readings. "
                   "Falling back to TTUIdleState as failsafe.")

            print(msg, level="error")
            logger.error(msg)
            self.csm.set_state_by(TTUIdleState, self)

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
             In Idle state, if the time of day is within the START_TIME
             range, and the G1 water level is below START_LEVEL, then
             the state machine transitions to the Topping Up state.
             In the topping up state, the solenoid valve is open, allowing
             mains water to enter G1 and increase its level.
             In Topping Up state, if the water level reaches or exceeds
             STOP_LEVEL, or if the time of day is after FAILSAFE_END_TIME
             or before the START_TIME range, then the state machine
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
        self._add_state(TTUIdleState)
        self._add_state(TTUToppingUpState)

        #Set initial state
        self.set_state(TTUIdleState)

    @staticmethod
    def get_state_machine_name():
        return "TempTopUpControlLogic"
