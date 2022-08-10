#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Temp Top Up Logic Unit Tests for the River System Control and Monitoring Software
# Copyright (C) 2017-2022 Wimborne Model Town
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

#Import modules
import unittest
import sys
from unittest.mock import Mock, patch, mock_open

sys.path.append('../../../..') #Need to be able to import Logic and Tools
import Logic.temptopuplogic as temptopuplogic
import Tools.logiccoretools
import datetime

from .testwatermodel import *

def tempTopUpWaterModel(G1Level):
    """
    Returns a WaterModel configured with items relevant for testing
    Temp Top Up logic.
    
    Args:
        G1Level (int)   initial model water level for G1
    
    Returns:
        (WaterModel)    a WaterModel for testing Temp Top Up logic
    """
    wm = WaterModel()
    
    # Populate WaterModel
    wm.addVessel("G1", G1Level)
    
    wm.addSensor(LevelSensor, "G3", "M0", "G1")
    wm.addSensor(HighLimitSensor, "G3", "FS0", "G1")
    wm.addSensor(LowLimitSensor, "G3", "FS1", "G1")
    
    wm.addDevice(Motor, "G3", "S0")
    
    return wm

class TempTopUpFakeSolenoid():
    """
    A fake solenoid device for testing the Temp Top Up logic.
    
    This allows us to hook the local device object into the WaterModel device
    control logging feature, which is otherwise only for devices controlled
    via logiccoretools.
    """
    def __init__(self, wm):
        """
        Initialiser
        
        Args:
            wm (WaterModel)     watermodel in which to log device control
        """
        self.wm = wm
    
    def enable(self):
        self.wm._attempt_to_control("G3","S0","enabled")
    
    def disable(self):
        self.wm._attempt_to_control("G3","S0","disabled")

class LogiccoretoolsTestError(RuntimeError):
    """
    Exception to be raised when testing scenarios in which
    the functions in logiccoretools raise errors.
    """
    pass

class TestTempTopUpReadingsParser(unittest.TestCase):
    """
    Full tests of class TempTopUpReadingsParser
    """
    def setUp(self):
        # Arbitrary initial water level, since we're testing several levels
        self.wm = tempTopUpWaterModel(600)
        
        # Create readings dictionary
        temptopuplogic.readings = self.wm.getReadingsDict("G1","G2","G3")
        
        # temptopuplogic looks for Tools.logiccoretools in Tools.logiccoretools
        self.wm.overrideFunctions(Tools.logiccoretools)
    
    def tearDown(self):
        temptopuplogic.readings = {}
        self.wm.unOverrideFunctions()
        self.wm = None
    
    def assertNoLoggedEvents(self):
        """
        When called by a test, asserts that the WaterModel has no
        logged events
        """
        msg = "The readings parser shouldn't have logged an event."
        self.assertIsNone(self.wm.event, msg)
        self.assertIsNone(self.wm.event_severity, msg)
    
    def assertNoLoggedStatus(self):
        """
        When called by a test, asserts that the WaterModel has no
        logged status.
        """
        msg = "The readings parser shouldn't have logged a status."
        self.assertIsNone(self.wm.pi_status, msg)
        self.assertIsNone(self.wm.sw_status, msg)
        self.assertIsNone(self.wm.current_action, msg)
    
    # No need to test logiccoretools errors, since the readings parser only
    # uses local readings.
    
    def testNoReadings(self):
        """Test that the readings parser handles the case where there are no readings yet."""
        temptopuplogic.readings = {}
            
        tturp = temptopuplogic.TempTopUpReadingsParser()
        
        # Check that all the parser's methods raise ValueError
        with self.subTest("g1NeedsTopUp"):
            with self.assertRaises(ValueError):
                tturp.g1NeedsTopUp()
                
        with self.subTest("g1ToppedUp"):
            with self.assertRaises(ValueError):
                tturp.g1ToppedUp()
        
    def testG1NeedsTopUp(self):
        """Test that TempTopUpReadingsParser.g1NeedsTopUp() behaves as expected under various conditions."""
        
        # Expected fault-free g1NeedsTopUp return values for selected G1
        # level values
        expected = {
            temptopuplogic.start_level + 100: False,
            temptopuplogic.start_level: False,
            temptopuplogic.start_level - 1: True
            }
        
        for l in expected:
            self.wm.setVesselLevel("G1", l)
            
            # Iterate through fault possibilities, including no faults
            with self.wm.faultIteration() as nextFault:
                while (nextFault()):
                    cf = self.wm.currentFault()
                    
                    # For now, only the "no faults" subtest is expected
                    # to pass because the test code does not yet
                    # reflect the desired outcome in all fault states.
                    if not all(f == 0 for f in cf.values()):
                        print("Info: Testing simulated fault states other "
                            "than \"no faults\" is not yet implemented")
                        break
                    else:
                        print("Testing the \"no faults\" state.")
                    
                    temptopuplogic.readings = self.wm.getReadingsDict(
                                                  "G1","G2","G3")
                    
                    tturp = temptopuplogic.TempTopUpReadingsParser()
                    
                    with self.subTest("\nSubtest using simulated fault states:\n"
                                    + self.wm.describeCurrentFault()
                                    + "\n",
                                    g1_level = l,
                                    faults = cf):
                        self.assertEqual(tturp.g1NeedsTopUp(), expected[l],
                                        "The readings were not parsed "
                                        "as expected. Make sure any "
                                        "simulated sensor faults were "
                                        "correctly handled.")
                        
                        # Readings parser shouldn't log events or status in any case
                        self.assertNoLoggedEvents()
                        self.assertNoLoggedStatus()
    
    def testG1ToppedUp(self):
        """Test that TempTopUpReadingsParser.g1ToppedUp() behaves as expected under various conditions."""
        # Expected fault-free g1ToppedUp return values for selected G1 levels
        expected = {
            temptopuplogic.stop_level - 15: False,
            temptopuplogic.stop_level: True,
            temptopuplogic.stop_level - 1: False,
            temptopuplogic.stop_level + 1: True
            }
        
        for l in expected:
            self.wm.setVesselLevel("G1", l)
            
            # Iterate through fault possibilities, including no faults
            with self.wm.faultIteration() as nextFault:
                while(nextFault()):
                    cf = self.wm.currentFault()
                    
                    # For now, only the "no faults" subtest is expected to pass
                    # because the test code does not yet reflect the desired
                    # outcome in all fault states.
                    if not all(f == 0 for f in cf.values()):
                        print("Info: Testing simulated fault states other "
                            "than \"no faults\" is not yet implemented")
                        break
                    else:
                        print("Testing the \"no faults\" state.")
                    
                    temptopuplogic.readings = self.wm.getReadingsDict(
                                                  "G1","G2","G3")
                    
                    tturp = temptopuplogic.TempTopUpReadingsParser()
                    
                    with self.subTest("\nSubtest using simulated fault states:\n"
                                    + self.wm.describeCurrentFault()
                                    + "\n",
                                    g1_level = l,
                                    faults = cf):
                        self.assertEqual(tturp.g1ToppedUp(), expected[l],
                                         "The readings were not parsed "
                                         "as expected. Make sure any "
                                         "simulated sensor faults were "
                                         "correctly handled.")
                        
                        # Readings parser shouldn't log events or status in any case
                        self.assertNoLoggedEvents()
                        self.assertNoLoggedStatus()

class TestTempTopUpControlLogic(unittest.TestCase):
    """
    Full tests of class TempTopUpControlLogic
    """
    def setUp(self):
        # Arbitrary initial water level, since we're testing several levels
        self.wm = tempTopUpWaterModel(600)
        
        # Create readings dictionary
        temptopuplogic.readings = self.wm.getReadingsDict("G1","G2","G3")
        
        # temptopuplogic looks for Tools.logiccoretools in Tools.logiccoretools
        self.wm.overrideFunctions(Tools.logiccoretools)
        
        temptopuplogic.solenoid = TempTopUpFakeSolenoid(self.wm)
        
        # Disable the manual override feature for the solenoid valve
        self.real_G3S0OverrideState = temptopuplogic.G3S0OverrideState
        temptopuplogic.G3S0OverrideState = Mock(return_value="auto")
    
    def tearDown(self):
        temptopuplogic.readings = {}
        self.wm.unOverrideFunctions()
        temptopuplogic.solenoid = None
        temptopuplogic.G3S0OverrideState = self.real_G3S0OverrideState
        self.wm = None
    
    # The control state machine doesn't need much testing, except to
    # confirm that it is possible to get into each of the required
    # states.
    # 
    # This makes sure none of the states has been missed out of the
    # class initialiser, and also tests that getCurrentStateName is
    # working.
    #
    # Behaviour of individual states should not be tested here.
    # We just want to know they exist in the state machine and that the
    # state machine can tell us its current state.
    
    def testIdle(self):
        """Tests that the logic can get into Idle state"""
        # Idle should be the default state, so we just need to make
        # sure the water level is not below start_level
        self.wm.setVesselLevel("G1", temptopuplogic.start_level + 10)
        temptopuplogic.readings = self.wm.getReadingsDict("G1","G2","G3")
        
        sm = temptopuplogic.TempTopUpControlLogic()
        sm.doLogic(30)
        self.assertEqual(sm.getCurrentStateName(),
                         "TTUIdleState")
    
    def testToppingUp(self):
        """Tests that the logic can get into Topping Up state"""
        # Set conditions that should put us into Topping Up state
        self.wm.setVesselLevel("G1", temptopuplogic.start_level - 10)
        temptopuplogic.readings = self.wm.getReadingsDict("G1","G2","G3")
        
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[0])
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            sm = temptopuplogic.TempTopUpControlLogic()
            sm.doLogic(30)
            self.assertEqual(sm.getCurrentStateName(),
                         "TTUToppingUpState")

class TestG3S0OverrideState(unittest.TestCase):
    """
    Full tests of function G3S0OverrideState
    """
    def testFileNotFound(self):
        """Test solenoid override state when override file not present"""
        with patch('Logic.temptopuplogic.open',
                   side_effect=FileNotFoundError):
            self.assertEqual(temptopuplogic.G3S0OverrideState(), "auto")
    
    def testOn(self):
        """Test solenoid override state 'on' (set in override file)"""
        with patch('Logic.temptopuplogic.open', mock_open(read_data="on\n")):
            self.assertEqual(temptopuplogic.G3S0OverrideState(), "on")
    
    def testOff(self):
        """Test solenoid override state 'off' (set in override file)"""
        with patch('Logic.temptopuplogic.open', mock_open(read_data="off\n")):
            self.assertEqual(temptopuplogic.G3S0OverrideState(), "off")
    
    def testAuto(self):
        """Test solenoid override state 'auto' (set in override file)"""
        with patch('Logic.temptopuplogic.open', mock_open(read_data="auto\n")):
            self.assertEqual(temptopuplogic.G3S0OverrideState(), "auto")
    
    def testFileInaccessible(self):
        """Test solenoid override state when override file inaccessible"""
        with patch('Logic.temptopuplogic.open',
                   side_effect=PermissionError):
            self.assertEqual(temptopuplogic.G3S0OverrideState(), "off")
        
        with patch('Logic.temptopuplogic.open',
                   side_effect=IsADirectoryError):
            self.assertEqual(temptopuplogic.G3S0OverrideState(), "off")
        
        with patch('Logic.temptopuplogic.open',
                   side_effect=TimeoutError):
            self.assertEqual(temptopuplogic.G3S0OverrideState(), "off")
    
    def testUnrecognisedValue(self):
        """Test solenoid override state when override file contains unrecognised value"""
        with patch('Logic.temptopuplogic.open', mock_open(read_data="foo\n")):
            self.assertEqual(temptopuplogic.G3S0OverrideState(), "off")
        
        with patch('Logic.temptopuplogic.open', mock_open(read_data="\nbar")):
            self.assertEqual(temptopuplogic.G3S0OverrideState(), "off")
        
        with patch('Logic.temptopuplogic.open', mock_open(read_data="\non")):
            self.assertEqual(temptopuplogic.G3S0OverrideState(), "off")
    
    def testRemoteOff(self):
        """Test solenoid override state 'remote/off' (set in override file)"""
        with patch('Logic.temptopuplogic.open',
                   mock_open(read_data="remote/off\n")):
            with patch('Tools.logiccoretools.get_state',
                       Mock(return_value=("Locked","None","NAS"))):
                self.assertEqual(temptopuplogic.G3S0OverrideState(), "off")
            
            with patch('Tools.logiccoretools.get_state',
                       Mock(side_effect=RuntimeError)):
                self.assertEqual(temptopuplogic.G3S0OverrideState(), "off")
            
            with patch('Tools.logiccoretools.get_state',
                       Mock(return_value=("Locked","ON","NAS"))):
                self.assertEqual(temptopuplogic.G3S0OverrideState(), "on")
            
            with patch('Tools.logiccoretools.get_state',
                       Mock(return_value=("Locked","OFF","NAS"))):
                self.assertEqual(temptopuplogic.G3S0OverrideState(), "off")
            
            with patch('Tools.logiccoretools.get_state',
                       Mock(return_value=("Locked","AUTO","NAS"))):
                self.assertEqual(temptopuplogic.G3S0OverrideState(), "auto")
            
            with patch('Tools.logiccoretools.get_state',
                       Mock(return_value=("Locked","MAYBE","NAS"))):
                self.assertEqual(temptopuplogic.G3S0OverrideState(), "off")
        
    def testRemoteAuto(self):
        """Test solenoid override state 'remote/auto' (set in override file)"""
        with patch('Logic.temptopuplogic.open',
                   mock_open(read_data="remote/auto\n")):
            with patch('Tools.logiccoretools.get_state',
                       Mock(return_value=("Locked","None","NAS"))):
                self.assertEqual(temptopuplogic.G3S0OverrideState(), "auto")
            
            with patch('Tools.logiccoretools.get_state',
                       Mock(side_effect=RuntimeError)):
                self.assertEqual(temptopuplogic.G3S0OverrideState(), "auto")
            
            with patch('Tools.logiccoretools.get_state',
                       Mock(return_value=("Locked","ON","NAS"))):
                self.assertEqual(temptopuplogic.G3S0OverrideState(), "on")
            
            with patch('Tools.logiccoretools.get_state',
                       Mock(return_value=("Locked","OFF","NAS"))):
                self.assertEqual(temptopuplogic.G3S0OverrideState(), "off")
            
            with patch('Tools.logiccoretools.get_state',
                       Mock(return_value=("Locked","AUTO","NAS"))):
                self.assertEqual(temptopuplogic.G3S0OverrideState(), "auto")
            
            with patch('Tools.logiccoretools.get_state',
                       Mock(return_value=("Locked","MAYBE","NAS"))):
                self.assertEqual(temptopuplogic.G3S0OverrideState(), "auto")

def singleStateTestSetUp(testInstance, stateClassUnderTest, G1Level):
    """
    Generic setUp for test cases that test a single control state
    
    Args:
        testInstance (Object)           the TestCase we are setting up
        stateClassUnderTest (Class)     the ControlStateABC subclass under test
        G1Level (int)                   initial model water level for G1
    """
    testInstance.wm = tempTopUpWaterModel(G1Level)
    
    # Create readings dictionary
    temptopuplogic.readings = testInstance.wm.getReadingsDict("G1","G2","G3")
    
    # temptopuplogic looks for Tools.logiccoretools in Tools.logiccoretools
    testInstance.wm.overrideFunctions(Tools.logiccoretools)
    
    # Fake solenoid to log solenoid control events in the WaterModel
    temptopuplogic.solenoid = TempTopUpFakeSolenoid(testInstance.wm)
    
    # Control states need a control state machine
    testInstance.csm = Mock(spec=temptopuplogic.TempTopUpControlLogic)
    
    # Instantiate the control state
    testInstance.s = stateClassUnderTest(testInstance.csm)
    
def singleStateTestTearDown(testInstance):
    """
    Generic tearDown for test cases that test a single control state
    
    Args:
        testInstance (Object)       the TestCase we are tearing down
    """
    temptopuplogic.readings = {}
    testInstance.wm.unOverrideFunctions()
    temptopuplogic.solenoid = None
    testInstance.wm = None
    testInstance.csm = None
    testInstance.s = None

class TestTTUIdleState(unittest.TestCase):
    """
    Full tests of class TTUIdleState
    """
    def setUp(self):
        # Initial water level should be above start_level for these tests
        singleStateTestSetUp(self,
                             temptopuplogic.TTUIdleState,
                             temptopuplogic.start_level + 10)
    
    def tearDown(self):
        singleStateTestTearDown(self)
    
    def testGetStateName(self):
        """Tests whether getStateName returns the correct state name"""
        self.assertEqual(self.s.getStateName(), "TTUIdleState")
    
    def testGetPreferredReadingInterval(self):
        """Tests whether the state has the correct preferred reading interval"""
        self.assertEqual(self.s.getPreferredReadingInterval(), 60)
    
    def assertStateControlOutputsCorrect(self):
        """
        Asserts that the control outputs of the state under test were
        correct for staying in that state.
        """
        # Check that only the solenoid was controlled
        self.assertEqual(self.wm.controlled_devices, ["G3:S0"])
        
        # Check that the solenoid was closed
        self.assertEqual(self.wm.getDeviceState("G3", "S0"), "disabled")
    
    def assertStateNoControlOutputs(self):
        """
        Asserts that there were no control outputs from the state under
        test.
        """
        self.assertListEqual(self.wm.controlled_devices, [],
                             "TTUIdleState should not have attempted to "
                             "control any devices.")
    
    def testSetupState(self):
        """Tests whether TTUIdleState has the correct control outputs when first set up."""
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[1])
        time = time - datetime.timedelta(hours=1)
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Disable solenoid valve override for this test
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="auto"):
                # Check that TTUIdle tries to turn off the solenoid valve
                self.s.setupState()
                self.assertStateControlOutputsCorrect()
    
    def testNoTransition(self):
        """Tests that TTUToppingUpState does not transition into another state under the expected conditions.
        
        The initial conditions should be chosen so that they do not
        justify a transition. This permits the other tests to assume
        that no transition would have occurred if they did not alter
        the conditions.
        
        (However, in this case, we cannot easily include time or
        solenoid override state in the initial conditions.)
        """
        
        # Check that transition does not occur with water above threshold,
        # time before start_time range
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[0])
        time = time - datetime.timedelta(hours=1)
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Disable solenoid valve override for this test
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="auto"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_not_called()
                self.assertStateControlOutputsCorrect()
        
        # Check that transition does not occur with water above threshold,
        # time at start of start_time range
        self.wm.controlled_devices = []
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[0])
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="auto"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_not_called()
                self.assertStateControlOutputsCorrect()
        
        # Check that transition does not occur with water below threshold and
        # time outside start_time range
        self.wm.controlled_devices = []
        self.wm.setVesselLevel("G1", temptopuplogic.start_level - 10)
        temptopuplogic.readings = self.wm.getReadingsDict("G1","G2","G3")
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[0])
        time = time - datetime.timedelta(hours=1)
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="auto"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_not_called()
                self.assertStateControlOutputsCorrect()
        
        # Check that transition does not occur with water below threshold,
        # time at start of start_time range and solenoid overridden to 'off'
        self.wm.controlled_devices = []
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[0])
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="off"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_not_called()
                self.assertStateControlOutputsCorrect()
    
    def testTransitionToToppingUp(self):
        """Tests whether TTUIdleState will transition into TTUToppingUpState under the expected conditions."""
        
        # Check that transition occurs with water below threshold and time
        # at start of start_time range
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[0])
        
        self.wm.setVesselLevel("G1", temptopuplogic.start_level - 10)
        temptopuplogic.readings = self.wm.getReadingsDict("G1","G2","G3")
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="auto"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_called_once_with(
                    temptopuplogic.TTUToppingUpState,
                    self.s)
        
        # Check that transition occurs with water below threshold and time
        # in middle of start_time range
        self.csm.setStateBy.reset_mock()
        time = (datetime.datetime.combine(datetime.date.today(),
                                          temptopuplogic.start_time[0])
                +
                ( (datetime.datetime.combine(datetime.date.today(),
                                             temptopuplogic.start_time[1])
                   -
                   datetime.datetime.combine(datetime.date.today(),
                                             temptopuplogic.start_time[0]))
                   / 2))
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="auto"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_called_once_with(
                    temptopuplogic.TTUToppingUpState,
                    self.s)
        
        # Check that transition occurs with water below threshold and time
        # at end of start_time range
        self.csm.setStateBy.reset_mock()
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[1])
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="auto"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_called_once_with(
                    temptopuplogic.TTUToppingUpState,
                    self.s)
        
        # Check that transition occurs with water above threshold, time
        # before start_time and solenoid overridden to 'on'
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G1", temptopuplogic.start_level + 10)
        temptopuplogic.readings = self.wm.getReadingsDict("G1","G2","G3")
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[0])
        time = time - datetime.timedelta(hours=1)
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="on"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_called_once_with(
                    temptopuplogic.TTUToppingUpState,
                    self.s)
        
        # None of the above should have caused control outputs
        self.assertStateNoControlOutputs()

class TestTTUToppingUpState(unittest.TestCase):
    """
    Full tests of class TTUToppingUpState
    """
    def setUp(self):
        # Initial water level should be less than stop_level for these tests
        singleStateTestSetUp(self,
                             temptopuplogic.TTUToppingUpState,
                             temptopuplogic.stop_level - 10)
    
    def tearDown(self):
        singleStateTestTearDown(self)
    
    def testGetStateName(self):
        """Tests whether getStateName returns the correct state name"""
        self.assertEqual(self.s.getStateName(), "TTUToppingUpState")
    
    def testGetPreferredReadingInterval(self):
        """Tests whether the state has the correct preferred reading interval"""
        self.assertEqual(self.s.getPreferredReadingInterval(), 60)
    
    def assertStateControlOutputsCorrect(self):
        """
        Asserts that the control outputs of the state under test were
        correct for staying in that state.
        """
        # Check that only the solenoid was controlled
        self.assertEqual(self.wm.controlled_devices, ["G3:S0"])
        
        # Check that the solenoid was opened
        self.assertEqual(self.wm.getDeviceState("G3", "S0"), "enabled")
    
    def assertStateNoControlOutputs(self):
        """
        Asserts that there were no control outputs from the state under
        test.
        """
        self.assertListEqual(self.wm.controlled_devices, [],
                             "TTUToppingUpState should not have "
                             "attempted to control any devices.")
    
    def testSetupState(self):
        """Tests whether TTUToppingUpState has the correct control outputs when first set up."""
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[1])
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            self.s.setupState()
            self.assertStateControlOutputsCorrect()
    
    def testNoTransition(self):
        """Tests that TTUToppingUpState does not transition into another state under the initial test conditions.
        
        The initial conditions should be chosen so that they do not
        justify a transition. This permits the other tests to assume
        that no transition would have occurred if they did not alter
        the conditions.
        
        (However, in this case, we cannot easily include time or
        solenoid override state in the initial conditions.)
        """
        
        # Check that transition does not occur with water below stop_level
        # and time at end of start_time
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[1])
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="auto"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_not_called()
                self.assertStateControlOutputsCorrect()
        
        # Check that transition does not occur with time at
        # failsafe_end_time and solenoid override set to 'on'
        self.wm.controlled_devices = []
        
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.failsafe_end_time)
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="on"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_not_called()
                self.assertStateControlOutputsCorrect()
        
        # Check that transition does not occur with water above stop_level
        # and solenoid override set to 'on'
        self.wm.controlled_devices = []
        
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[1])
        
        self.wm.setVesselLevel("G1", temptopuplogic.stop_level + 10)
        temptopuplogic.readings = self.wm.getReadingsDict("G1","G2","G3")
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="on"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_not_called()
                self.assertStateControlOutputsCorrect()
    
    def testTransitionToTTUIdle(self):
        """Tests whether TTUToppingUpState will transition into TTUIdleState under the expected conditions"""
        
        # Check that transition occurs when G1 reaches stop_level
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[1])
        self.wm.setVesselLevel("G1", temptopuplogic.stop_level)
        temptopuplogic.readings = self.wm.getReadingsDict("G1","G2","G3")
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="auto"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_called_once_with(
                    temptopuplogic.TTUIdleState,
                    self.s)
        
        # Check that transition occurs when time passes failsafe_end_time
        self.csm.setStateBy.reset_mock()
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.failsafe_end_time)
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="auto"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_called_once_with(
                    temptopuplogic.TTUIdleState,
                    self.s)
        
        # Check that transition occurs when solenoid override is 'off' but
        # when water level and time are such that no transition would occur
        # without an override
        self.csm.setStateBy.reset_mock()
        time = datetime.datetime.combine(datetime.date.today(),
                                         temptopuplogic.start_time[1])
        self.wm.setVesselLevel("G1", temptopuplogic.stop_level - 10)
        temptopuplogic.readings = self.wm.getReadingsDict("G1","G2","G3")
        
        with patch('datetime.datetime') as mock_dt:
            # Override the 'now' method, keep the others available
            mock_dt.now.return_value = time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch('Logic.temptopuplogic.G3S0OverrideState',
                       return_value="off"):
                self.s.doLogic(30)
                self.csm.setStateBy.assert_called_once_with(
                    temptopuplogic.TTUIdleState,
                    self.s)
        
        # None of the above should have caused control outputs
        self.assertStateNoControlOutputs()

class TestTempTopUpControlLogicFunction(unittest.TestCase):
    @unittest.expectedFailure
    def testsNotImplemented(self):
        # Fail as a reminder to write these tests.
        self.fail("These tests have not yet been written.")
