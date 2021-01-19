#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# State Tools for the River System Control and Monitoring Software
# Copyright (C) 2017-2020 Wimborne Model Town
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
This is the statetools module, which contains abstract classes
for implementing The State Pattern in control logic, initially
written for the Sump Pi control logic but intended to be useful
for other control logic too.

.. module:: statetools.py
    :platform: Linux
    :synopsis: Tools for implementing The State Pattern in control logic.

.. moduleauthor:: Patrick Wigmore <pwbugreports@gmx.com>
"""
import logging
from abc import ABCMeta, abstractmethod

#Don't ask for a logger name, so this works with both main.py
#and the universal monitor.
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

for handler in logging.getLogger('River System Control Software').handlers:
    logger.addHandler(handler)

class ControlStateABC(metaclass=ABCMeta):
    """
    Abstract Base Class for control states.
    
    Defines a template for classes that represent a state in a control logic
    state machine. Forms part of an implementation of the well-known Design
    Pattern named the "State Pattern".
    
    Don't instantiate objects of this class; use a subclass instead.
    """
    def __init__(self, controlStateMachine):
        """
        Initialiser for control state objects
        
        Args:
            controlStateMachine (ControlStateMachineABC):   A reference to the control state machine that this state belongs to.
        """
        self.csm = controlStateMachine
    
    @abstractmethod
    def setupState(self):
        """
        Performs actions required when entering this state. (e.g. set
        valves and pumps.)
        
        Abstract method: should raise NotImplementedError in base
        class. Implement in subclasses.
        """
        raise NotImplementedError
    
    @staticmethod
    def getPreferredReadingInterval():
        """
        Returns the preferred reading interval for this state.
        
        Subclasses should override if they require a non-default
        reading interval.
        
        Returns:
            int     The preferred reading interval in seconds
        """
        return 60
    
    @abstractmethod
    def doLogic(self, reading_interval):
        """
        Performs control logic appropriate to this state, returns an
        updated reading_interval, and transitions to another state if
        appropriate.
        
        Abstract method: should raise NotImplementedError in base
        class. Implement in subclasses.
        
        Returns:
            int     The reading interval requested by the logic
        """
        raise NotImplementedError
    
    @abstractmethod
    def getStateName():
        """
        Returns the name of the state represented by this class.
        
        Abstract method: raises NotImplementedError in base class.
        Implement as static method in subclasses.
        
        Returns:
            string: state name
        """
        raise NotImplementedError

class ControlStateMachineABC(metaclass=ABCMeta):
    """
    Abstract Base Class representing a state-machine-based control logic
    strategy for a Pi.
    
    Provides a doLogic static method which can be executed in the main loop of
    the river control system on a given Pi.
    
    Don't instantiate objects of this class; use a subclass instead.
    
    To create a new control logic strategy, create a new subclass that inherits
    from this class. Child classes will need to instantiate their full range of possible states in their initialiser and then enter an initial state. States should be subclasses of ControlStateABC and should each implement doLogic for that state.
    
    This class endeavours to implement the well-known Object-Oriented Design
    Pattern named the "State Pattern".
    """
    def __init__(self):
        """
        Initialiser to peform initialisation that's common to all
        subclasses.
        
        Subclass initialisers can call this using super().__init__().
        """
        self.states = {} # initialise dictionary to hold list of states
    
    def _addState(self, stateClass):
        """
        Adds a new state to this machine's dictionary of possible
        states. This method is only for use in subclass initialisers.
        
        Adding a state using this method facilitates the automatic
        functioning of getNamedState.
        
        Args:
            stateClass (ControlStateABC): state class to add
        """
        self.states[stateClass.getStateName()] = stateClass(self)
    
    def _getNamedState(self, stateName):
        """
        Returns a reference to a named state of this machine.
        
        Args:
            stateName (string): name of state to get
        """
        return self.states[stateName]
    
    def setState(self, stateClass):
        """
        Sets the current state of the state machine to the state having
        the specificed class. State objects may use this method to
        execute a state transition.
        
        Args:
            stateClass (Class (ControlStateABC)): the state to make current
        
        Returns:
            int     The preferred reading interval of the new state in seconds
        """
        #TODO: throw a more meaningful exception if there is no
        #      matching state in self.states. (Currently will throw an
        #      index out of bounds exception.)
        self.setNamedState(stateClass.getStateName())
        return stateClass.getPreferredReadingInterval()
    
    def setStateBy(self, stateClass, requester):
        """
        As setState, sets the current state of the state machine to the
        state having the specified class, but prints and logs a message
        saying which class requested the state transition. State
        objects should use this method to execute a state transition.
        
        Args:
            stateClass (Class (ControlStateABC)): the state to make current
            requester (ControlStateABC): the state requesting the transition
        
        Returns:
            int     The preferred reading interval of the new state in seconds
        """
        msg = (requester.getStateName()
               + " requests transition into "
               + stateClass.getStateName())
        logger.info(msg)
        print(msg)
        
        return self.setState(stateClass)
    
    def setNamedState(self, stateName):
        """
        Sets the current state of the state machine to the state
        corresponding to the specified name.
        
        This method is primarily intended for restoring the state from
        persistent storage, where it is more convenient to deal with a
        text string than a state object.
        
        Args:
            stateName (string): the name of the state to make current
        """
        try:
            stateChangeMsg = (self.getStateMachineName() + ": Transitioning from "
                            + self.getCurrentStateName() + " to "
                            + stateName)
            
        except (NameError, AttributeError):
            #This exception is expected when setting the initial state
            #(i.e. when self.state does not exist)
            stateChangeMsg = (self.getStateMachineName()
                            + ": Setting initial state "
                            + stateName)
        
        logger.info(stateChangeMsg)
        print(stateChangeMsg)
        
        self.state = self._getNamedState(stateName)
        
        self.state.setupState()
    
    def getCurrentStateName(self):
        """
        Returns the name of the current state of the state machine.
        
        This method is primarily intended for storing the current
        state in persistent storage, where it is more convenient to
        deal with a text string than a state object
        
        Returns:
            string: the name of the current state
        """
        return self.state.getStateName()
    
    @abstractmethod
    def getStateMachineName():
        """
        Returns the human-readable identifier of this state machine,
        for use in logs and console output.
        
        Abstract method: raises NotImplementedError in base class.
        Implement as static method in subclasses.
        """
        raise NotImplementedError
    
    def doLogic(self, reading_interval):
        """
        Executes the control logic of this control strategy.

        Delegated to the object that represents the current state.
        
        Args:
            readings (list):                A list of the latest readings for each probe/device.

            devices  (list):                A list of all master pi device objects.

            monitors (list):                A list of all master pi monitor objects.

            sockets (list of Socket):       A list of Socket objects that represent
                                            the data connections between pis. Passed
                                            here so we can control the reading
                                            interval at that end.

            reading_interval (int):     The current reading interval, in
                                        seconds.

        Returns:
            int: The reading interval, in seconds.

        Usage:

            >>> reading_interval = sumppi_control_logic(<listofreadings>,
            >>>                                     <listofprobes>, <listofmonitors>,
            >>>                                     <listofsockets>, <areadinginterval)

        """
        return self.state.doLogic(reading_interval)

class GenericControlState(ControlStateABC):
    """
    A generic control state implementation allowing for defined state
    transitions and control outputs and some built-in logging and event
    output.
    
    This abstract class implements more specific functionality than the
    base ControlStateABC class. This functionality is useful for
    concrete control state classes.
    
    Subclasses of GenericControlState should implement an initialiser
    that provides the required dependencies by calling
    GenericControlState.__init__().
    """
    class StateTransitionError(RuntimeError):
        """
        Exception to be raised by stateTransition in the event that it
        was not possible to determine whether a state transition should
        occur, due to a problem parsing readings.
        """
        pass
    
    class LogEventError(RuntimeError):
        """
        Exception to be raised by logEvent in the event that it was not
        possible to log an event.
        """
        pass
    
    @abstractmethod
    def stateTransition(self):
        """
        Defines the state transition function for this control state.
        
        It should raise StateTransitionError in the event that it was
        not possible to determine whether a state transition should
        occur, due to a problem parsing readings.
        
        This is an abstract method in GenericControlState, and should
        be overridden by each subclass.
        
        Raises:
            StateTransitionError
        """
        raise NotImplementedError
    
    def controlDevices(self, logEvent=False):
        """
        Defines the device control function for this control state.
        
        It should control some devices so that they end up in the state
        required by this control state. If logEvent is True, then it
        should also log an event about the control of the devices by
        calling self.logEventCE().
        
        If this state requires device control, then the subclass should
        override this method with one containing suitable logic.
        
        If this state does not require device control, then this method
        should simply do nothing. (i.e. If device control is not
        required, don't override this version, which does nothing.)
        """
        pass
    
    @abstractmethod
    def logEvent(self, *args):
        """
        Log an event.
        
        This method should implement the function signature of
        Tools.logiccoretools.log_event() and should log an event.
        
        This method should raise self.LogEventError in the event of
        failure to log an event.
        
        For the purposes of error messages, this method will be
        assumed to log events over a network.
        
        This is an abstract method, which subclasses must override in
        order to specify a means of logging errors.
        """
        raise NotImplementedError
    
    def logEventCE(self, *args):
        """
        Log an event and catch errors.
        
        Accepts any arguments accepted by self.logEvent.
        """
        try:
            self.logEvent(*args)
        
        except self.LogEventError:
            msg = "Error while trying to log event over network."
            print(msg)
            logger.error(msg)
    
    def setupState(self):
        logger.info("Setting up state " + self.getStateName())
        print("Setting up state " + self.getStateName())
        self.logEventCE("Entering " + self.getStateName())
        self.controlDevices(logEvent=True)
    
    def noTransition(self):
        """
        This should be called by stateTransition if no transition is
        currently required.
        """
        self.controlDevices()
    
    def doLogic(self, reading_interval):
        ri = self.getPreferredReadingInterval()
        
        try:
            self.stateTransition()
            
        except self.StateTransitionError:
            msg = ("Could not parse sensor readings. Control logic is "
                   "stalled.")
            print(msg)
            logger.error(msg)
            
            #If state transition failed, we can still refresh device
            #control for this state
            self.controlDevices()
        
        return ri
