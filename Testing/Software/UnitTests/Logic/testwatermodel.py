#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Test Water Model for the River System Control and Monitoring Software
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

# pylint: disable=too-few-public-methods
#
# Reason (too-few-public-methods): Test classes don't need many public members.

"""
This is the testwatermodel module, which contains an implementation of a model
of the water system, intended to be used to simulate various system conditions
for the purpose of testing control logic.

.. module:: testwatermodel.py
    :platform: Linux
    :synopsis: Contains a model water system for testing control logic.

.. moduleauthor:: Patrick Wigmore <pwbugreports@gmx.com>
"""
import re
import sys
import os.path

sys.path.insert(0, os.path.abspath('../../../..'))
from Tools.coretools import Reading

class Vessel():
    """
    Class representing a water vessel in a WaterModel.
    Vessels have an ID and a water level greater than 0mm. They can be
    drained or filled.
    
    Butt groups and sumps are examples of items that could be represented
    by object instances of this class.
    """
    def __init__(self, site_id, init_level):
        """
        Initialises an instance of Vessel
        
        Args:
            site_id (str):   An arbitrary identifier for this Vessel
            init_level (int):   The initial water level of this Vessel, in mm 
        """
        self._id = site_id
        self._level = init_level
    
    def getLevel(self):
        """
        Returns the current water level in this Vessel
        
        Returns:
            int     the current water level
        """
        return self._level
    
    def setLevel(self, level):
        """
        Sets this Vessel's level to the specified level, in mm.
        
        If the level is less than 0, then it will be taken to be 0.
        
        Args:
            level (int):    The new water level for this Vessel, in mm
        """
        if level < 0:
            level = 0
        
        self._level = level
    
    def getID(self):
        """
        Returns the ID of this Vessel
        
        Returns:
            (str)       This Vessel's ID.
        """
        return self._id

class ModelObject():
    """
    Abstract class representing model objects with state and, optionally,
    simulated faults.
    """
    def getState(self):
        """
        Returns the current state of this ModelObject.
        
        Subclasses must override this, to provide a sensible return value.
        """
        raise NotImplementedError()
        
    
    def setFault(self, n):
        """
        Sets this ModelObject into fault state n, where n is an integer
        between 0 and the value returned by getFaultCount().
        
        When n == 0, the ModelObject simulates a state of having no faults.
        
        When n > 0, the ModelObject simulates one of a number of predetermined
        discrete fault states.
        
        Subclasses may override this method to implement their own
        numbered fault states. Each unique integer should correspond to
        one possible fault combination state for the subclass.
        
        The set of integers in the range 0 to getFaultCount() - 1
        should map to the set of possible combinations of faults that
        the subclass intends to model.
        
        EXAMPLE
        If the subclass has two items that can either be faulty or not
        faulty, in any combination, then it could be said to have four
        possible fault states and integers in the range 0 to 4 could be
        mapped to those states as follows:
            0 --> No fault.
            1 --> Item 1 faulty.
            2 --> Item 2 faulty.
            3 --> Both items faulty.
        
        However, this is just an example, and there is NO requirement
        for fault states to map onto combinations of True/False values.
        Subclasses are free to implement arbitrary fault numbering
        schemes, provided that:
        
          * 0 maps to a state in which there are no faults
        
          * setFault accepts all integer values of n between 0 and
                getFaultCount() - 1, inclusive. (i.e.: no gaps)
        
        Throws:
            ValueError, if n is too large.
        """
        if n > 0:
            raise ValueError("This model object does not support faults.")
    
    def getFaultCount(self):
        """
        Returns an integer representing the number of possible fault states
        that this ModelObject can simulate, including the "no faults" state.
        
        Subclasses should override this if they support faults, based
        on what values their setFault accepts.
        
        Returns:
            (int)   number of fault states
        """
        return 1    # Default to no fault states
    
    def identifyFault(self):
        """
        Returns a machine-readable identifier that uniquely identifes the
        current fault state of this ModelObject. This could simply be an
        integer, or anything else that identifies the fault.
        
        Subclasses should override this to describe their particular faults.
        
        Subclasses should include a list of possible return values in the
        docstring for this method.
        
        Returns:
            fault identifier
        """
        return 0
    
    def describeFault(self):
        """
        Returns a human-readable string descrbing the current fault state of
        this ModelObject.
        
        Subclasses should override this to describe their specific possible
        fault states.
        
        Returns:
            (str)   fault description
        """
        return "No fault."

class Sensor(ModelObject):
    """
    Abstract class representing a sensor in a WaterModel.
    """
    def __init__(self, vessel, site_id, sensor_id):
        """
        Initialiser for Sensor class
        
        Args:
            vessel (Vessel):    the Vessel this sensor senses
            site_id (str):      the site_id of this Sensor
            sensor_id (str):    the sensor_id of this Sensor
        """
        self._vessel = vessel
        
        # We need an ID string to put into Reading objects
        self._id_string = site_id + ":" + sensor_id
    
    def _getReadingImpl(self, time, tick, fault=False):
        """
        Returns a current reading for this Sensor.
        
        This provides a partial implementation of getReading that
        subclasses should use to implement getReading().
        
        The subclass only needs to add code that sets the 'fault'
        argument depending on the subclass' fault state. This way,
        fault states are only handled in the subclass, rather than
        being spread across two classes.
        
        The time and tick arguments should be created as required for
        reading_time and reading_tick in the initialiser for Tools.Reading.
        
        Args:
            time (str):    The time to say the reading is from
            tick (int):    The tick to say the reading is from
            fault (bool):  If True, the reading will indicate a sensor fault
        """
        # Status should normally be "OK", but can also be "FAULT DETECTED".
        status = "OK" if not fault else "FAULT DETECTED"
        return Reading(time, tick, self._id_string, self.getState(), status)
    
    def getReading(self, time, tick):
        """
        Returns a current reading for this Sensor.
        
        The time and tick arguments should be created as required for
        reading_time and reading_tick in the initialiser for Tools.Reading.
        
        This is an abstract method, but subclasses should use the
        partial implementation in in _getReadingImpl() to implement it.
        
        Args:
            time (str):    The time to say the reading is from
            tick (int):    The tick to say the reading is from
        
        Returns:
            (Reading)   A reading for this Sensor
        """
        raise NotImplementedError()

class LevelSensor(Sensor):
    """
    Class representing a water level sensor in a WaterModel.
    
    Does not represent any specific kind of sensor, except that it returns
    a water level value in millimetres, for a Vessel.
    
    TODO: Fault conditions: not yet implemented
    """
    def __init__(self, vessel, site_id, sensor_id):
        super().__init__(vessel, site_id, sensor_id)
        self._sensor_fault = False
    
    def getState(self):
        """
        Refer to Sensor superclass documentation
        """
        return str(self._vessel.getLevel()) + "mm"
    
    def getReading(self, time, tick):
        """
        Refer to Sensor superclass documentation
        """
        return self._getReadingImpl(time, tick, self._sensor_fault)
    
    def setFault(self, n):
        """
        Refer to Sensor superclass documentation
        """
        self._sensor_fault = (n == 1)
    
    def getFaultCount(self):
        """
        Refer to Sensor superclass documentation
        """
        return 2
    
    def identifyFault(self):
        """
        Refer to Sensor superclass documentation
        """
        return 0 if not self._sensor_fault else 1
    
    def describeFault(self):
        """
        Refer to Sensor superclass documentation
        """
        return ("No fault." if not self._sensor_fault
                else "Reading status fault.")

class LimitSensor(Sensor):
    """
    Abstract class representing a sensor that indicates that the water level
    in a Vessel is at some limit.
    """
    def __init__(self, vessel, site_id, sensor_id):
        super().__init__(vessel, site_id, sensor_id)
        self._stuck = False
        self._stuckState = None
        self._sensor_fault = False
    
    def getReading(self, time, tick):
        """
        Refer to Sensor superclass documentation
        """
        return self._getReadingImpl(time, tick, self._sensor_fault)
    
    def setFault(self, n):
        """
        Refer to Sensor superclass documentation
        
        0 --> No fault
        1 --> Stuck on, not indicated in Readings
        2 --> Stuck off, not indicated in Readings
        3 --> Stuck on, with indication in Readings
        4 --> Stuck off, with indication in Readings
        5 --> Unaccountable fault indication in Readings
        """
        
        # This could conceivably be reduced to just four states, if it
        # proves necessary to reduce the number of combinations that
        # the model has to iterate through in total. The strictly
        # necessary fault states are those currently numbered 0, 1, 2
        # and 5. Logic failures that depend on the presence of both
        # kinds of faults ("stuck" and "indicated in Readings") are
        # fairly unlikely.
        
        # Of course, identifyFault and describeFault need to be amended
        # if the list of acceptable fault states changes.
        if n > self.getFaultCount() - 1:
            raise ValueError("Fault state out of range.")
        
        if n > 2: # i.e. n in [3, 4, 5]; indicating a fault in Readings
            self._sensor_fault = True
            
        if n in [0, 5]: # not "stuck"
            self._stuck = False
            
        else: # "stuck"...
            self._stuck = True
            
            if n in [1, 3]: # ...and not indicating a fault in Readings
                self._stuckState = True
            elif n in [2, 4]: # ... and indicating a fault in Readings
                self._stuckState = False
    
    def getFaultCount(self):
        """
        Refer to Sensor superclass documentation
        """
        return 6    # was 3
    
    def identifyFault(self):
        """
        Refer to Sensor superclass documentation
        
        Returns:
            (int)   0 if no fault
                    1 if stuck on and not indicating fault in Readings
                    2 if stuck off and not indicating fault in Readings
                    3 if stuck on and indicating fault in Readings
                    4 if stuck off and indicating fault in Readings
                    5 if Readings unaccountably indicate a fault
        """
        if self._stuck:
            if self._stuckState:
                if not self._sensor_fault:
                    return 1    # stuck on, no reading fault indication
                else:
                    return 3    # stuck on, reading fault indication
            else:
                if not self._sensor_fault:
                    return 2    # stuck off, no reading fault indication
                else:
                    return 4    # stuck off, reading fault indication
        else:
            if self._sensor_fault:
                return 5        # unaccountable reading fault indication
            else:
                return 0        # no fault
    
    def describeFault(self):
        """
        Refer to Sensor superclass documentation
        """
        n = self.identifyFault()
        if n == 0:
            return "No fault."
        elif n == 1:
            return "Stuck in 'True' state. No fault indicated in Readings."
        elif n == 2:
            return "Stuck in 'False' state. No fault indicated in Readings."
        elif n == 3:
            return "Stuck in 'True' state. Fault indicated in Readings."
        elif n == 4:
            return "Stuck in 'False' state. Fault indicated in Readings."
        else:
            return "Unaccountable fault indication in Readings."

class HighLimitSensor(LimitSensor):
    """
    Class representing a sensor that indicates a full state of a Vessel.
    
    Does not represent any specific type of sensor, except that it returns
    a true/false value depending on whether the vessel is "full".
    """
    def getState(self):
        """
        Refer to LimitSensor superclass documentation
        """
        if self._stuck:
            # Return fake value if simulating being "stuck".
            return str(self._stuckState)
        
        else:
            # We'll assume the sensor triggers a bit before 1000mm water depth
            return str(self._vessel.getLevel() > 987)

class LowLimitSensor(LimitSensor):
    """
    Class representing a sensor that indicates an empty state of a Vessel.
    
    Does not represent any specific type of sensor, except that it returns
    a true/false value depending on whether the vessel is "empty".
    """
    def getState(self):
        """
        Refer to LimitSensor superclass documentation
        """
        if self._stuck:
            # Return fake value if simulating being "stuck".
            return str(self._stuckState)
        
        else:
            # We'll assume the sensor triggers a bit before 0mm water depth
            return str(self._vessel.getLevel() < 22)

class ControllableDevice():
    """
    Class representing devices in the model that can be controlled.
    """
    def __init__(self):
        self._locked_to = None
        
    def setState(self, state):
        """
        Sets this ControllableDevice's state to the given state.
        
        Subclasses must override this method in a way that is meaningful for
        them.
        
        Args:
            state (str)     a state that's meaningful for this device
        """
        raise NotImplementedError()
    
    def getLock(self, locker):
        """
        Tries to get a lock on this model object for a specified
        controlling entity (a "locker").
        
        The return value indicates whether the lock was granted.
        
        'locker' should be a value that is meaningful within the
        WaterModel, but is otherwise an arbitrary value used only for
        this method and the corresponding releaseLock method. It
        should identify a unique controlling entity. (i.e. a Pi or
        other device.)
        
        Example usage of locker value:
            0 = this pi
            1 = another pi
        
        Args:
            locker (int):   Identifies who will get the lock
        
        Returns:
            (bool):     True if lock is granted, otherwise False
        """
        if self._locked_to is None:
            self._locked_to = locker
            return True
        
        elif self._locked_to == locker:
            return True
        
        else:
            return False
    
    def getLockState(self):
        """
        Returns the current lock state of the device.
        
        The current locker value is an integer as provided to getLock.
        
        If the device is not locked, returns None.
        
        Returns:
            (int):  current locker or None
        """
        return self._locked_to
    
    def releaseLock(self, locker):
        """
        Releases a lock held by a given controlling entity ("locker").
        
        If the given locker does not hold the lock, then the method
        does nothing.
        
        The value of the locker argument should be consistent with that
        used in a previous call of getLock().
        
        Args:
            locker (int):   Identifies who has the lock
        """
        if self._locked_to is not None:
            if self._locked_to == locker:
                self._locked_to = None

class Valve(ModelObject, ControllableDevice):
    """
    Class representing a valve that can be opened a percentage amount.
    """
    def __init__(self):
        super().__init__()
        self._position = 0
        self._has_been_set = False
        
        # Compile regular expression to match valid valve state values
        self._state_pattern = re.compile('[0-9]{1,3}%')
    
    def getState(self):
        """
        Refer to ModelObject superclass documentation
        """
        if self._has_been_set:
            return str(self._position) + "%"
        else:
            return "Unspecified"
    
    def setState(self, state):
        """
        Refer to ControllableDevice superclass documentation
        """
        # Intentionally there is no error raised if the state is not
        # usable, since the logic ought to cope with real devices not
        # raising an error.
        if isinstance(state, str):
            m = self._state_pattern.match(state)
            if m.group() == state: # if the whole string matches the regex
                self._position = int(state[:-1]) # remove % and convert to int
                self._has_been_set = True

class Motor(ModelObject, ControllableDevice):
    """
    Class representing a motor that can be enabled or disabled.
    """
    def __init__(self):
        super().__init__()
        self._state = "disabled"
        self._has_been_set = False
        
        # COmpile regular expression to match valid motor state values
        self._state_pattern = re.compile('enabled|disabled')
    
    def getState(self):
        """
        Refer to ModelObject superclass documentation
        """
        if self._has_been_set:
            return self._state
        else:
            return "Unspecified"
    
    def setState(self, state):
        """
        Refer to ControllableDevice superclass documentation
        """
        # Intentionally there is no error raised if the state is not
        # usable, since the logic ought to cope with real devices not
        # raising an error.
        if isinstance(state, str):
            m = self._state_pattern.match(state)
            if m.group() == state: # if the whole string matches the regex
                self._state = state
                self._has_been_set = True

class WaterModelNoMoreFaults(Exception):
    """
    Exception to be raised by WaterModel._nextFault() when there are no more
    fault states to enter.
    """
    pass

class WaterModelFaultIterationContextManager():
    """
    Context manager for iterating through fault combinations.
    
    Using a context manager for this functionality ensures that the
    iteration always starts from the initial, "no faults" state and
    that the WaterModel is left in "no faults" state afterwards.
    """
    def __init__(self, waterModel):
        """
        Args:
            waterModel  The WaterModel associated with this context manager
        """
        self.wm = waterModel
        self.started = False
    
    def __enter__(self):
        self.wm.resetFaults()
        return self.nextFault
    
    def __exit__(self, exc_type, exc_value, traceback):
        # Catch WaterModelNoMoreFaults at end of iteration
        if exc_type == WaterModelNoMoreFaults:
            # No need to reset faults; WaterModel.nextFault() does this
            # for us, before raising WaterModelNoMoreFaults.
            return True     # Suppress this expected exception
        else:
            self.wm.resetFaults()
            return False
    
    def nextFault(self):
        """
        Advances the WaterModel to the next fault state.
        """
        # We want to return the no-fault state on the first call of
        # nextFault, so that it can be used as a while loop condition
        #
        # This differs from the behaviour of WaterModel._nextFault(),
        # hence this check to see whether we've started.
        if self.started:
            self.wm._nextFault()
        else:
            self.started = True
        
        # Always return True
        # We end iteration using an exception, not by returning False
        return True

class WaterModel():
    """
    Class representing a rough model of the water system for the purpose of
    testing control logic.
    
    Note that this class is not, in itself, tested, except by the tests
    that make use of it.
    
    Each test that wants to use a WaterModel should initialise the model with
    the set of Vessels, Sensors and Devices needed for the purposes of the
    test. The WaterModel does not care whether these items actually exist in
    the system, or whether they form a complete system model. Individual tests
    are free to use the WaterModel class to model an arbitrary system to suit
    their requirements.
    
    The model is not intended to accurately simulate the behaviour of the
    water in the real river system. It is only meant to test the behaviour
    of the control logic. Accurate water simulation is explicitly
    out-of-scope for this class.
    
    The WaterModel provides three basic services to control logic tests:
    
    1. You can use the model to generate plausible fictitious sensor readings,
       to test specific scenarios.
    
    2. You can use the model to automate the simulation of sensor faults, to
       easily test the handling of faulty sensor data in each test scenario.
    
    3. You can use the model to receive control output from the control logic,
       to provide visibility of the control actions taken by control logic in
       response to test scenarios.
    
    Usage:
        Instantiate a WaterModel
        >>> w = WaterModel()
        >>> w.overrideFunctions(Tools.logiccoretools)
        
        Set up a test case with some vessels, sensors and devices
        >>> w.addVessel("G4", 500)
        >>> w.addSensor(LevelSensor, "G4", "M0")
        >>> w.addSensor(HighLimitSensor, "G4", "FS0")
        >>> w.addVessel("G6", 500)
        >>> w.addSensor(LevelSensor, "G6", "M0")
        >>> w.addSensor(HighLimitSensor, "G6", "FS0")
        >>> w.addSensor(LowLimitSensor, "G6", "FS1")
        >>> w.addDevice(Valve, "VALVE12", "V12")

        After running the control logic under test, see what's changed
        >>> w.getState("VALVE12", "V12")
        "100%"
        
        Test the same scenario under different sensor fault combinations
        >>> with w.faultIteration() as nextFault:
                while(nextFault()):
                    (run the control logic)
                    w.getDeviceState("VALVE12", "V12")
                    
                    # No need to clean up fault state afterwards
                
                
    """
    # Locker identifiers for device locking:
    THIS_SITE = 0
    OTHER_SITE = 1
    
    def __init__(self):
        """
        Initialises an instance of WaterModel
        """
        self._vessels = {}  # To contain the model vessels
        self._devices = {}  # To contain the model Sensors and Devices
        self._current_fault = 0 # Index of current error combination
        self._total_faults = 1  # Number of fault combinations
        
        # Properties to hold details logged by _log_event()
        self.event = None
        self.event_severity = None
        
        # Properties to hold details logged by _update_status()
        self.pi_status = None
        self.sw_status = None
        self.current_action = None
        
        # Property to log whether control of devices was attempted
        self.controlled_devices = []
    
    def _validateID(self, an_id, context):
        """
        Validates a site_id or a sensor_id
        
        context is a human-readable string to be included in any
        resulting ValueError.
        
        context must end with a noun describing what the ID identifies,
        but it may provide context before this. For example:
        "When doing X, Y".
        
        Args:
            an_id (str):   an ID to validate
            context (str): (human-readable) context, ending with noun
        
        Throws:
            ValueError, if validation fails.
        """
        if (not isinstance(an_id, str) or
            an_id == ""):
            raise ValueError(context + " must be a (non-empty) string.")

    def _validateDevice(self, site_id, sensor_id, context):
        """
        Performs validation to ensure that the device identified by the
        given site_id and sensor_id exists in the WaterModel.
        
        If the device does not exist, a suitable error will be raised.
        
        context should describe in human-readable terms what action is
        being taken when the validation occurs, so that the error
        messages will be meaningful. It should be written so that it
        makes sense when prepended to wording of the form:
        "variable X must fulful condition Y."
        
        Args:
            site_id (str)       The site ID of the device
            sensor_id (str)     The sensor ID of the device
            context (str)       (human-readable) context action description
        
        Returns:
            (object)    The device identified by site_id and sensor_id
        """
        self._validateID(site_id, context + "site_id ")
        self._validateID(sensor_id, context + "site_id ")
        
        try:
            return self._devices[site_id][sensor_id]
        except KeyError as e:
            raise ValueError("The device " + site_id + ":" +sensor_id +
                             " does not exist in this WaterModel.") \
                             from e
    
    def addVessel(self, site_id, init_level):
        """
        Adds a water vessel to the water model.
        
        site_id  should be the site_id that the control logic under test
        is expected to use to read sensor values on said vessel. If not,
        it will be necessary to use the vessel_id argument when calling
        addSensor.
        
        Args:
            site_id (str):   An arbitrary identifier for the new vessel
            init_level (int):   The initial water level of the vessel, in mm
        
        Throws:
            ValueError, if the arguments are invalid.
        """
        self._validateID(site_id, "WaterModel Vessel identifier")
        
        if (not isinstance(init_level, int) or
            init_level < 0):
            raise ValueError("Initial water level for vessel in WaterModel "
                             "must be a non-negative integer.")
        
        v = Vessel(site_id, init_level)
        self._vessels[site_id] = v
        
        self.resetFaults()
    
    def addSensor(self, sensor_class, site_id, sensor_id, vessel_id=None):
        """
        Adds a Sensor to the water model.
        
        If vessel_id is not specified, then site_id must match the site_id
        of a Vessel that has already been added to the model.
        
        If the site_id of the sensor does not match the site_id of the
        vessel that it will take readings of, then vessel_id must be
        specified to override that assumption and specify the vessel's
        site_id directly.
        
        site_id and sensor_id should be the site_id and sensor_id that
        the control logic under test is expected to use to read sensor
        values from the sensor.
        
        sensor_class specifies what kind of sensor to add.
        
        The sensor_class should be a subclass of the Sensor class in this
        module. Do not attempt to use a class from Tools.deviceobjects.
        Nevertheless, to remain flexible to possible duck-type
        alternatives, sensor_class is not validated.
        
        Args:
            sensor_class (Sensor):  name of a subclass of testwatermodel.Sensor
            site_id (str):       An arbitrary site ID for the sensor
            sensor_id (str):     An arbitrary sensor ID for the sensor
            vessel_id (str):     (Optional) site ID of the vessel to measure
        
        Throws:
            ValueError, if the arguments are invalid, given the current model.
        """
        self._validateID(site_id,
                         "When adding a Sensor to a WaterModel, site_id")
        
        if vessel_id is None:
            vessel_id = site_id
        
        if (not isinstance(vessel_id, str) or 
            vessel_id == "" or
            not isinstance(self._vessels[vessel_id], Vessel)):
            raise ValueError("When adding a Sensor to a WaterModel, either "
                             "site_id or vessel_id must match the site_id "
                             "of a Vessel that has already been loaded into "
                             "the model.")
        
        self._validateID(sensor_id,
                         "When adding a Sensor to a WaterModel, sensor_id")

        s = sensor_class(self._vessels[vessel_id], site_id, sensor_id)
        
        if (site_id in self._devices
            and isinstance(self._devices[site_id], dict)):
            self._devices[site_id][sensor_id] = s
        else:
            self._devices[site_id] = { sensor_id : s }
        
        self.resetFaults()
    
    def addDevice(self, device_class, site_id, sensor_id):
        """
        Adds a Device to the water model.
        
        site_id and sensor_id should be the site_id and sensor_id that the
        control_logic under test is expected to use to control the
        device.
        
        device_class specifies what kind of device to add.
        
        The device_class should be a subclass of the Device class in this
        module. Do not attempt to use a class from Tools.deviceobjects.
        Nevertheless, to remain flexible to possible duck-type
        alternatives, device_class is not validated.
        
        Args:
            device_class (Device):  name of a subclass of testwatermodel.Device
            site_id (str):       An arbitrary site ID for the device
            sensor_id (str):     An arbitrary sensor ID for the device
        
        Throws:
            ValueError, if the arguments are invalid.
        """
        self._validateID(site_id,
                         "When adding a Device to a WaterModel, site_id")
        self._validateID(sensor_id,
                         "When adding a Device to a WaterModel, sensor_id")
        
        d = device_class()
        
        if (site_id in self._devices
            and isinstance(self._devices[site_id], dict)):
            self._devices[site_id][sensor_id] = d
        else:
            self._devices[site_id] = { sensor_id : d }
        
        self.resetFaults()
    
    def setVesselLevel(self, site_id, level):
        """
        Sets the water level of the Vessel identified by site_id.
        
        Args:
            site_id (str):  The site ID identifying the vessel
            level (int):    The new water level for the vessel, in mm
        """
        if isinstance(level, int):
            try:
                self._vessels[site_id].setLevel(level)
            
            except KeyError as e:
                raise ValueError("There is no Vessel with site ID '"
                                 + str(site_id)
                                 + "' in this WaterModel" ) from e
            
        else:
            raise ValueError("New water level for Vessel must be an integer.")
    
    def getDeviceState(self, site_id, sensor_id):
        """
        Tries to return the status of the device in the WaterModel identified
        by the given site_id and sensor_id.
        
        Only Sensors and Devices can report a state value. Vessels cannot.
        
        Args:
            site_id (str):      site_id of the device
            sensor_id (str):    sensor_id of the device
            
        Throws:
            ValueError, if the site_id and sensor_id do not identify a device.
            
            AttributeError, if the device cannot report a state value.
        """
        d = self._validateDevice(site_id, sensor_id, "")
        
        try:
            return d.getState()
        
        except AttributeError:
            raise
    
    def _applyFaultsToDevice(self, f, d):
        """
        Part of the implementation of _applyFaults.
        
        Given a device d, strips off and applies that device's share of
        the fault combination number f, returning the remaining share
        of f for subsequent devices.
        
        Args:
            f (int)             fault combination number
            d (ModelObject)     a device
        """
        c = d.getFaultCount()
        if c > 0:   # Ignore devices that can't have faults
            d.setFault(round(f % c))
            f = f // c
            
        return f
    
    def _applyFaults(self):
        """
        Applies the current fault combination to the devices in the model.
        """
        # Start with the fault combination number
        f = self._current_fault
        
        # And then proceed through the known devices, applying their faults,
        # leaving remaining faults to apply to subsequent devices.
        for d in self._devices.values():
            if isinstance(d, dict):
                for d2 in d.values():
                    f = self._applyFaultsToDevice(f, d2)
            else:
                # This branch should never be reached, but belt and braces.
                f = self._applyFaultsToDevice(f, d)
        
        # NOTE: It is critical that the for loop always proceeds in the
        #       same order as it did last time, otherwise, when we
        #       increment _current_fault, we will not proceeed through
        #       a sequence of unique fault combinations. In Python, the
        #       ordering should be consistent each time, but that would
        #       not necessarily be true in all languages or language
        #       constructs.
        #
        #       One consequence of this requirement is that
        #       _current_fault must be reset when a new device is added
        #       to the WaterModel.

    def _addFaults(self, device):
        """
        Adds device's total faults to this WaterModel's total faults.
        
        (Adds is a bit of a misnomer here, as we need to multiply to
        find out the number of combinations that are to be added. Think
        of adding to a collection rather than arithmetic addition.)
        """
        self._total_faults = self._total_faults * device.getFaultCount()

    def resetFaults(self):
        """
        Clears all simulated sensor faults and recalculates how many fault
        combinations are possible.
        """
        self._current_fault = 0
        self._applyFaults()
        
        # Start from 1. There is always a "no faults" state
        # (Also, _addFaults needs a non-zero value here, but that's not the
        # justification for the value.)
        self._total_faults = 1
        
        # Re-calculate total possible fault combinations
        for d in self._devices.values():
            if isinstance(d, dict):
                for d2 in d.values():
                    self._addFaults(d2)
            else:
                # This branch should never be reached, but belt and braces.
                self._addFaults(d)

    def _hasMoreFaults(self):
        """
        Returns true if there are more sensor error combinations available.
        
        Don't use this method directly. Instead, use the context manager
        returned by getFaultStateCM().
        
        Returns:
            bool    True if there are more sensor error combinations available.
                    False if there are not.
        """
        # e.g. if _total_faults = 9 and _current_fault == 8, then return False
        return self._current_fault < self._total_faults - 1

    def _nextFault(self):
        """
        Advances the WaterModel to its next sensor fault combination.
        
        Rather than calling this method directly, use the context
        manager returned by getFaultStateCM().
        
        If there are no more fault combinations possible, then the
        exception WaterModelNoMoreFaults is raised, and the fault state
        is returned to "no faults".
        
        Note that the WaterModel always starts in the initial no-fault
        state, so if you use _nextFault() as a while loop condition,
        (which you shouldn't do) the loop will miss off the no-fault
        state at the beginning.
        
        Throws:
            WaterModelNoMoreFaults      if here are no more faults
        """
        if self._hasMoreFaults():
            self._current_fault = self._current_fault + 1
            self._applyFaults()
        else:
            self._current_fault = 0
            raise WaterModelNoMoreFaults()

    def faultIteration(self):
        """
        Returns a context manager that can be used to iterate through
        fault states of the WaterModel.
        
        The iteration will begin with the initial "no faults" state.
        
        Use the context manager in a with statement with a target:
            with <WaterModel object>.faultIteration() as target:
        
        The target of the with statement will have a 'next fault state'
        function assigned to it, which can be used as the condition for
        a while loop, to iterate through all fault states including "no
        faults":
            while(target()):
        
        Returns:
            WaterModelFaultIterationContextManager  a context manager
        
        Usage:
            # Where 'wm' is a WaterModel instance
            with wm.faultIteration() as nextFault:
                while(nextFault()):
                    # Do something (per fault state)
                    
            # After the last fault state, the loop and the 'with'
            # context are safely terminated automatically
        """
        # Pass in a reference to this WaterModel as an argument
        return WaterModelFaultIterationContextManager(self)

    def currentFault(self):
        """
        Returns a machine-readable representation of the current fault
        combination.
        
        Returns a dictionary, indexed by device identifier, containing
        a representation of each device's state.
        
        This provides a way for unit tests to handle particular failure
        conditions as a specific case, in the context of having to test
        against every possible condition.
        
        The values in the returned dictionary will be specific to each
        device in the model and each one should uniquely identify a
        particular failure combination for that device. Refer to
        each device's identifyFault() documentation for details.
        
        Returns
            (dict)     dictionary of device fault states
        """
        f = {}
        for site_id, s in self._devices.items():
            if isinstance(s, dict):
                for sensor_id, d in s.items():
                    f[site_id + ":" + sensor_id] = d.identifyFault()
            else:
                # This branch should never be reached, but belt and braces
                f[site_id] = s.identifyFault()
                
        return f

    def describeCurrentFault(self):
        """
        Returns a human-readable listing of the current faults being
        simulated by the model.
        
        Returns:
            (str)   human-readable fault listing
        """
        f = ""
        for site_id, s in self._devices.items():
            if isinstance(s, dict):
                for sensor_id, d in s.items():
                    f = (f + "[" + site_id + ":" + sensor_id + "]: " +
                         d.describeFault() + "\n")
            else:
                # This branch should never be reached, but belt and braces
                f = f + "[" + site_id + "]: " + d.describeFault() + "\n"
        
        return f.rstrip("\n") # remove trailing newline

    def _getReadingsDict(self, site_id):
        """
        Provides a 'readings dictionary' for sensors in a given site_id,
        similar to that which is passed into control logic functions as an
        argument.
        
        The dictionary will be limited to containing only sensors in the
        given site_id.
        
        Args:
            site_id (str)   specify which site ID to return readings for
        
        Returns:
            (dict)          readings dictionary
        """
        self._validateID(site_id,
                         "When getting a readings dictionary, site_id")
        
        try:
            site_devices = self._devices[site_id]
        except KeyError:
            # If the site_id has no devices, then we should return no devices
            return {}
        
        # For now, just use arbitrary time and tick values for readings
        # (If the method of determining time/tick is changed, then also
        # change it in _get_latest_reading.)
        
        tick = 0
        time = "2020-09-23 16:19:17.413922"
        
        output_dict = {}
        for key, device in site_devices.items():
            # We're only interested in sensors here
            if isinstance(device, Sensor):
                output_dict[site_id + ":" + key] = device.getReading(time, tick)
        
        return output_dict

    def getReadingsDict(self, *site_ids):
        """
        Provides a 'readings dictionary' for sensors in the given site_ids,
        similar to that which is passed into control logic functions as an
        argument.
        
        The dictionary will be limited to containing only sensors with the
        given site_ids. site_ids may be a tuple of strings or a single
        string.
        
        Args:
            site_id (str)    one or more site IDs to return readings for
        
        Returns:
            (dict)                  readings dictionary
        """
        if isinstance(site_ids, str):
            output_dict = self._getReadingsDict(site_ids)
        
        elif isinstance(site_ids, tuple):
            output_dict = {}
            for site_id in site_ids:
                output_dict.update(self._getReadingsDict(site_id))
        
        return output_dict

    def overrideFunctions(self, module):
        """
        Overrides functions found in the given module with methods of this
        WaterModel.
        
        This method is intended to be used to override Tools.logiccoretools
        so that control logic under test will interact with the WaterModel
        instead of with the real river control system.
        
        This method should override the complete interface presented to
        control logic by logiccoretools. Any function in that interface
        that is not implemented in WaterModel should be overridden to the
        value None, in case the control logic under test tries to call
        that function.
        
        Args:
            module (Module):   Name of module in which to override functions
        """
        self._overridden_module = module
        
        self._overridden_get_latest_reading = module.get_latest_reading
        self._overridden_get_n_latest_readings = module.get_n_latest_readings
        self._overridden_get_state = module.get_state
        self._overridden_get_status = module.get_status
        self._overridden_attempt_to_control = module.attempt_to_control
        self._overridden_release_control = module.release_control
        self._overridden_log_event = module.log_event
        self._overridden_update_status = module.update_status
        self._overridden_store_tick = module.store_tick
        self._overridden_store_reading = module.store_reading
        
        module.get_latest_reading = self._get_latest_reading
        module.get_n_latest_readings = self._get_n_latest_readings
        module.get_state = self._get_state
        module.get_status = None
        module.attempt_to_control = self._attempt_to_control
        module.release_control = self._release_control
        module.log_event = self._log_event
        module.update_status = self._update_status
        module.store_tick = None
        module.store_reading = None
    
    def unOverrideFunctions(self):
        """
        Undoes the actions of overrideFunctions.
        
        This method is intended to be used where tests need to restore the
        original state of the overridden functions.
        """
        self._overridden_module.get_latest_reading = \
            self._overridden_get_latest_reading
        
        self._overridden_module.get_n_latest_readings = \
            self._overridden_get_n_latest_readings
        
        self._overridden_module.get_state = \
            self._overridden_get_state
        
        self._overridden_module.get_status = \
            self._overridden_get_status
        
        self._overridden_module.attempt_to_control = \
            self._overridden_attempt_to_control
        
        self._overridden_module.release_control = \
            self._overridden_release_control
        
        self._overridden_module.log_event = \
            self._overridden_log_event
        
        self._overridden_module.update_status = \
            self._overridden_update_status
        
        self._overridden_module.store_tick = \
            self._overridden_store_tick
        
        self._overridden_module.store_reading = \
            self._overridden_store_reading
    
    def resetLoggedItems(self):
        """
        Clears any logged events or statuses in the WaterModel
        """
        self.event = None
        self.event_severity = None
        self.pi_status = None
        self.sw_status = None
        self.current_action = None
    
    def _get_latest_reading(self, site_id, sensor_id, retries=3):
        """
        Implementation of logiccoretools.get_latest_reading which takes
        its readings from this WaterModel.
        
        The argument 'retries' has no meaning or effect in this
        implementation and is included only for compatibility.
        
        Args:
            site_id (str).            The site we want the reading from.
            sensor_id (str).          The sensor we want the reading for.

        Named args:
            retries[=3] (int).        Ignored by this implementation.

        Returns:
            A Reading object.   The latest reading for that sensor at that site.

            OR

            None.               There is no reading available to return.

        Throws:
            RuntimeError, if query failure simulation is enabled.
            ValueError, if site_id or sensor_id is invalid.
        """
        # For now, just hard code arbitrary tick and time values
        # TODO: maybe implement something more elaborate for determining
        # realistic and/or test-specified tick and time values.
        # (If the method of determining time/tick is changed, then also
        # change it in _getReadingsDict.)
        self._validateID(site_id, "When fetching readings, site_id")
        self._validateID(site_id, "When fetching readings, sensor_id")
        tick = 0
        time = "2020-09-23 16:19:17.413922"
        return self._devices[site_id][sensor_id].getReading(time, tick)
    
    def _get_n_latest_readings(self, site_id, sensor_id, number, retries=3):
        """
        Implementation of logiccoretools.get_n_latest_readings which
        takes its readings from this WaterModel.
        
        Currently this method is limited to returning one reading,
        because the WaterModel does not model historical state.
        
        The argument 'retries' has no meaning or effect in this
        implementation and is included only for compatibility.
        """
        # For now, just return a list containing only the output of
        # _get_latest_reading():
        return [self._get_latest_reading(site_id, sensor_id)]
    
    def _get_state(self, site_id, sensor_id, retries=3):
        """
        Implementation of logiccoretools.get_state, which takes state
        from this WaterModel.
        
        The argument 'retries' has no meaning or effect in this
        implementation and is included only for compatibility.
        """
        # The purpose of this wrapper around self.getDeviceState is to
        # accept and then ignore the retries argument and (TODO) to
        # implement query failure simulation
        return self.getDeviceState(site_id, sensor_id)
    
    def getLockState(self, site_id, sensor_id):
        """
        Returns the current lock state of a modelled device.
        
        Tests may use this method to check whether the logic has
        appropriately taken or released a lock on a particular device.
        
        Args:
            site_id (str):      The site ID of the device
            sensor_id (str):    The sensor ID of the device
        
        Returns:
            (str):              "this" if the lock is held by "this site"
                                "other" if the lock is held by "another site"
                                "none" if the lock is held by nothing
        """
        d = self._validateDevice(site_id, sensor_id, "To query a lock state, ")
        l = d.getLockState()
        
        return "none" if l is None \
          else "this" if l == self.THIS_SITE \
          else "other"
    
    def otherPiLock(self, site_id, sensor_id, lock):
        """
        Sets or releases a lock on a modelled device, held by "another"
        Pi.
        
        Use this in tests to simulate inability of the logic to get a
        lock on a device. Call with lock = True to simulate "another"
        Pi holding the lock, or with lock = False to simulate that lock
        being released ready for "this" Pi to take it.
        
        Args:
            site_id (str):      The site ID of the device
            sensor_id (str):    The sensor ID of the device
            lock (bool):       Device foreign lock state; True = locked
        
        Returns:
            (bool):             True if requested lock state set, else False
        
        Throws:
            ValueError, if site_id or sensor_id is invalid.
        """
        d = self._validateDevice(site_id, sensor_id, "To lock a device, ")
        
        try:
            if lock:
                return d.getLock(self.OTHER_SITE)
            else:
                return d.releaseLock(self.OTHER_SITE)
        
        except NameError as e:
            raise ValueError("The device " + site_id + ":" + sensor_id +
                             " does does not support being locked.") from e
    
    def _attempt_to_control(self, site_id, sensor_id, request, retries=3):
        """
        Implementation of logiccoretools.attempt_to_control, which acts
        upon this WaterModel.
        
        The argument 'retries' has no meaning or effect in this
        implementation and is included only for compatibility.
        
        Args:
            site_id.         The site that holds the device we're interested in.
            sensor_id.       The sensor we want to know about.
            request (str).   What state we want the device to be in.

        Named args:
            retries[=3] (int).  Has no effect in this implementation.

        Returns:
            boolean.      True - We are now in control of the device.
                          False - The device is locked and in use by another pi.

        Throws:
            RuntimeError, if query failure simulation is enabled.
            ValueError, if site_id or sensor_id is invalid.
        """
        d = self._validateDevice(site_id, sensor_id,
                                 "When trying to control a device, ")
        
        self.controlled_devices.append(site_id + ":" + sensor_id)
        
        if d.getLock(self.THIS_SITE): # If we have the lock or can get it
            d.setState(request)
            return True
        
        else: # If we can't get the lock
            return False
    
    def _release_control(self, site_id, sensor_id, retries=3):
        """
        Implementation of logiccoretools.release_control, which acts
        upon this WaterModel.
        
        The argument 'retries' has no meaning or effect in this
        implementation and is included only for compatibility.
        
        Args:
            site_id.         The site that holds the device we're interested in.
            sensor_id.       The sensor we want to know about.

        Named args:
            retries[=3] (int).  Has no effect in this implementation.
        """
        d = self._validateDevice(site_id, sensor_id,
                        "When trying to release control of a device, ")
        d.releaseLock(self.THIS_SITE)
    
    def _log_event(self, event, severity="INFO", retries=3):
        """
        Implementation of logiccoretools.log_event, which acts upon
        this WaterModel.
        
        The argument 'retries' has no meaning or effect in this
        implementation and is included only for compatibility.
        
        The current implementation logs only the most recent event,
        since generally tests will only be testing for the presence of
        one specific event log.
        """
        if isinstance(event, str) and isinstance(severity, str):
            self.event = event
            self.event_severity = severity
    
    def _update_status(self, pi_status, sw_status, current_action, retries=3):
        """
        Implementation of logiccoretools.update_status, which acts upon
        this WaterModel.
        
        The argument 'retries' has no meaning or effect in this
        implementation and is included only for compatibility.
        
        The current implementation logs only the most recent status,
        since generally tests will only be testing for the presence of
        one specific status update.
        """
        if (isinstance(pi_status, str)
        and isinstance(sw_status, str)
        and isinstance(current_action, str)):
            self.pi_status = pi_status
            self.sw_status = sw_status
            self.current_action = current_action

