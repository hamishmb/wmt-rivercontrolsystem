#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Stage Pi Logic Unit Tests for the River System Control and Monitoring Software
# Copyright (C) 2017-2019 Wimborne Model Town
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
from unittest.mock import Mock

sys.path.append('../../../..') #Need to be able to import Logic and Tools
import Logic.stagepilogic as stagepilogic
import Tools.logiccoretools
from testwatermodel import *

def stagePiWaterModel(G6Level, G4Level):
    """
    Returns a WaterModel configured with items relevant for testing
    Stage Pi logic.
    
    Args:
        G6Level (int)   initial model water level for G6
        G4Level (int)   initial model water level for G4
    
    Returns:
        (WaterModel)    a WaterModel for testing Stage Pi logic
    """
    wm = WaterModel()
    
    # Populate WaterModel with items relevant to Stage Pi Logic.
    wm.addVessel("G6", G6Level)
    wm.addVessel("G4", G4Level)
    
    wm.addSensor(LevelSensor, "G6", "M0")
    wm.addSensor(HighLimitSensor, "G6", "FS0")
    wm.addSensor(LowLimitSensor, "G6", "FS1")
    wm.addSensor(LevelSensor, "G4", "M0")
    wm.addSensor(HighLimitSensor, "G4", "FS0")
    wm.addSensor(LowLimitSensor, "G4", "FS1")
    
    wm.addDevice(Valve, "VALVE12", "V12")
    
    return wm

class TestStagePiReadingsParser(unittest.TestCase):
    """
    Full tests of class StagePiReadingsParser
    """
    def setUp(self):
        # Arbitrary initial water levels, since we're testing several levels
        self.wm = stagePiWaterModel(500, 500)
        
        # stagepilogic looks for Tools.logiccoretools in Tools.logiccoretools
        self.wm.overrideFunctions(Tools.logiccoretools)
    
    def tearDown(self):
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
        
    def testG6Full(self):
        """
        Test that StagePiReadingsParser.g6Full() behaves as expected
        under various conditions.
        """
        # Expected fault-free g6Full return values for selected G6 level values
        expected = {
            stagepilogic.levels["G6Full"] + 100: True, # well within range
            stagepilogic.levels["G6Full"]: True,       # at lower bound
            stagepilogic.levels["G6Full"] - 1: False   # 1mm below lower bound
            }
        
        for l in expected:
            self.wm.setVesselLevel("G6", l)
            
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
                    
                    sprp = stagepilogic.StagePiReadingsParser()
                    
                    with self.subTest("\nSubtest using simulated fault states:\n"
                                    + self.wm.describeCurrentFault()
                                    + "\n",
                                    g6_level = l,
                                    faults = cf):
                                        
                        if expected[l] and cf["G6:FS1"] in [1,3]:
                            # if full with low limit float switch stuck on
                            self.assertRaises(ValueError, sprp.g6Full(),
                                            "The readings parser should "
                                            "have raised an error due to "
                                            "the contradictory sensor "
                                            "readings.")
                        
                        else:
                            self.assertEqual(sprp.g6Full(), expected[l],
                                            "The readings were not parsed "
                                            "as expected. Make sure any "
                                            "simulated sensor faults were "
                                            "correctly handled.")
                        
                        # Readings parser shouldn't log events or status in any case
                        self.assertNoLoggedEvents()
                        self.assertNoLoggedStatus()
    
    def testG6Empty(self):
        """
        Test that StagePiReadingsParser.g6Empty() behaves as expected
        under various conditions.
        """
        # Expected fault-free g6Empty return values for selected G6 levels
        expected = {
            # N.B. G6 Empty is defined by the lower bound for "not empty"
            # so this is slightly different than in the other tests here,
            # which deal with the lower bound of the category under test
            stagepilogic.levels["G6NotEmpty"] - 15: True, # within range
            stagepilogic.levels["G6NotEmpty"]: False,     # over upper bound
            stagepilogic.levels["G6NotEmpty"] - 1: True,  # 1mm under bound
            stagepilogic.levels["G6Full"]: False          # well over upper bound
            }
        
        for l in expected:
            self.wm.setVesselLevel("G6", l)
            
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
                    
                    sprp = stagepilogic.StagePiReadingsParser()
                    
                    with self.subTest("\nSubtest using simulated fault states:\n"
                                    + self.wm.describeCurrentFault()
                                    + "\n",
                                    g6_level = l,
                                    faults = cf):
                        
                        if expected[l] and cf["G6:FS0"] in [1,3]:
                            # if empty with high limit float switch stuck on
                            self.assertRaises(ValueError, sprp.g6Empty(),
                                            "The readings parser should "
                                            "have raised an error due to "
                                            "the contradictory sensor "
                                            "readings.")
                        
                        else:
                            self.assertEqual(sprp.g6Empty(), expected[l],
                                            "The readings were not parsed "
                                            "as expected. Make sure any "
                                            "simulated sensor faults were "
                                            "correctly handled.")
    
    def testG4Overfull(self):
        """
        Test that StagePiReadingsParser.g4Overfull() behaves as
        expected under various conditions.
        """
        # Expected fault-free g4Overfull return values for selected G4 levels
        expected = {
            stagepilogic.levels["G4Overfull"] + 100: True, # within range
            stagepilogic.levels["G4Overfull"]: True,      # on lower bound
            stagepilogic.levels["G4Overfull"] - 1: False  # 1mm under bound
            }
        
        for l in expected:
            self.wm.setVesselLevel("G4", l)
            
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
                    
                    sprp = stagepilogic.StagePiReadingsParser()
                    
                    with self.subTest("\nSubtest using simulated fault states:\n"
                                    + self.wm.describeCurrentFault()
                                    + "\n",
                                    g4_level = l,
                                    faults = cf):
                        
                        self.assertEqual(sprp.g4Overfull(), expected[l],
                                            "The readings were not parsed "
                                            "as expected. Make sure any "
                                            "simulated sensor faults were "
                                            "correctly handled.")
    
    def testG4FullOrMore(self):
        """
        Test that StagePiReadingsParser.g4FullOrMore() behaves as
        expected under various conditions.
        """
        # Expected fault-free g4FullOrMore return values for selected G4 levels
        expected = {
            # N.B. "full or more"; there is no upper bound
            3000: True,    # guaranteed very full
            stagepilogic.levels["G4Full"] + 100: True, # within range
            stagepilogic.levels["G4Full"]: True,       # on lower bound
            stagepilogic.levels["G4Full"] - 1: False   # 1mm under bound
            }
        
        for l in expected:
            self.wm.setVesselLevel("G4", l)
            
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
                    
                    sprp = stagepilogic.StagePiReadingsParser()
                    
                    with self.subTest("\nSubtest using simulated fault states:\n"
                                    + self.wm.describeCurrentFault()
                                    + "\n",
                                    g4_level = l,
                                    faults = cf):
                        
                        self.assertEqual(sprp.g4FullOrMore(), expected[l],
                                            "The readings were not parsed "
                                            "as expected. Make sure any "
                                            "simulated sensor faults were "
                                            "correctly handled.")
    
    def testG4VeryNearlyFullOrMore(self):
        """
        Test that StagePiReadingsParser.g4VeryNearlyFullOrMore()
        behaves as expected under various conditions.
        """
        # Expected fault-free g4Overfull return values for selected G4 levels
        expected = {
            # N.B. "very nearly full or more"; there is no upper bound
            3000: True,    # guaranteed very full
            stagepilogic.levels["G4VeryNearlyFull"] + 100: True, # within range
            stagepilogic.levels["G4VeryNearlyFull"]: True,       # on lower bound
            stagepilogic.levels["G4VeryNearlyFull"] - 1: False   # 1mm under bound
            }
        
        for l in expected:
            self.wm.setVesselLevel("G4", l)
            
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
                    
                    sprp = stagepilogic.StagePiReadingsParser()
                    
                    with self.subTest("\nSubtest using simulated fault states:\n"
                                    + self.wm.describeCurrentFault()
                                    + "\n",
                                    g4_level = l,
                                    faults = cf):
                        
                        self.assertEqual(sprp.g4VeryNearlyFullOrMore(), expected[l],
                                            "The readings were not parsed "
                                            "as expected. Make sure any "
                                            "simulated sensor faults were "
                                            "correctly handled.")
    
    def testG4NearlyFullOrMore(self):
        """
        Test that StagePiReadingsParser.g4NearlyFullOrMore() behaves as
        expected under various conditions.
        """
        # Expected fault-free g4Overfull return values for selected G4 levels
        expected = {
            # N.B. "nearly full or more"; there is no upper bound
            3000: True,    # guaranteed very full
            stagepilogic.levels["G4NearlyFull"] + 100: True, # within range
            stagepilogic.levels["G4NearlyFull"]: True,       # on lower bound
            stagepilogic.levels["G4NearlyFull"] - 1: False   # 1mm under bound
            }
        
        for l in expected:
            self.wm.setVesselLevel("G4", l)
            
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
                    
                    sprp = stagepilogic.StagePiReadingsParser()
                    
                    with self.subTest("\nSubtest using simulated fault states:\n"
                                    + self.wm.describeCurrentFault()
                                    + "\n",
                                    g4_level = l,
                                    faults = cf):
                        
                        self.assertEqual(sprp.g4NearlyFullOrMore(), expected[l],
                                            "The readings were not parsed "
                                            "as expected. Make sure any "
                                            "simulated sensor faults were "
                                            "correctly handled.")
    
class TestStagePiControlLogic(unittest.TestCase):
    """
    Full tests of class StagePiControlLogic
    """
    def setUp(self):
        # Arbitrary initial water levels, since we're testing several levels
        self.wm = stagePiWaterModel(500, 500)
        
        # stagepilogic looks for Tools.logiccoretools in Tools.logiccoretools
        self.wm.overrideFunctions(Tools.logiccoretools)
    
    def tearDown(self):
        self.wm.unOverrideFunctions()
        self.wm = None
    
    # The control state machine doesn't need much testing, except to
    # confirm that it is possible to get into each of the required
    # states.
    # 
    # This makes sure none of the states has been missed out of the
    # class initialiser, and also tests that getCurrentStateName is
    # working.
    #
    # As a side effect, we end up testing StagePiInitState's ability to
    # transition into each other state.
    #
    # Behaviour of other individual states should not be tested here.
    # We just want to know they exist in the state machine and that the
    # state machine can tell us its current state.
    
    def testStagePiInitState(self):
        """
        Tests that the logic can get into StagePiInitState
        """
        # Logic should go into StagePiInitState by default
        sm = stagepilogic.StagePiControlLogic()
        self.assertEqual(sm.getCurrentStateName(), "StagePiInitState")
    
    def testG6Empty(self):
        """
        Tests that the logic can get into G6Empty state
        """
        
        # Set conditions that should put us into G6Empty
        self.wm.setVesselLevel("G6", 0)
        
        sm = stagepilogic.StagePiControlLogic()
        sm.doLogic(30)
        self.assertEqual(sm.getCurrentStateName(),
                         "StagePiG6EmptyState")
    
    def testG4Overfilled(self):
        """
        Tests that the logic can get into G4Overfilled state
        """
        # Set conditions that should put us into G4Overfilled
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4Overfull"])
        
        sm = stagepilogic.StagePiControlLogic()
        sm.doLogic(30)
        self.assertEqual(sm.getCurrentStateName(),
                         "StagePiG4OverfilledState")
    
    def testG4Filled(self):
        """
        Tests that the logic can get into G4Filled state
        """
        # Set conditions that should put us into G4Filled
        # G6 is at 500, as per setUp()
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4Full"])
        
        sm = stagepilogic.StagePiControlLogic()
        sm.doLogic(30)
        self.assertEqual(sm.getCurrentStateName(),
                         "StagePiG4FilledState")
    
    def testG4VeryNearlyFilled(self):
        """
        Tests that the logic can get into G4VeryNearlyFilled state
        """
        # Set conditions that should put us into G4VeryNearlyFilled
        # G6 is at 500, as per setUp()
        self.wm.setVesselLevel("G4",
                               stagepilogic.levels["G4VeryNearlyFull"])
        
        sm = stagepilogic.StagePiControlLogic()
        sm.doLogic(30)
        self.assertEqual(sm.getCurrentStateName(),
                         "StagePiG4VeryNearlyFilledState")
    
    def testG4NearlyFilled(self):
        """
        Tests that the logic can get into G4NearlyFilled state
        """
        # Set conditions that should put us into G4NearlyFilled
        # G6 is at 500, as per setUp()
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4NearlyFull"])
        
        sm = stagepilogic.StagePiControlLogic()
        sm.doLogic(30)
        self.assertEqual(sm.getCurrentStateName(),
                         "StagePiG4NearlyFilledState")
    
    def testG4Filling(self):
        """
        Tests that the logic can get into G4Filling state
        """
        # Set conditions that should put us into G4Filling
        # G6 is at 500, as per setUp()
        self.wm.setVesselLevel("G4",
                               stagepilogic.levels["G4NearlyFull"] - 1)
        
        sm = stagepilogic.StagePiControlLogic()
        sm.doLogic(30)
        self.assertEqual(sm.getCurrentStateName(),
                         "StagePiG4FillingState")

def singleStateTestSetUp(testInstance, stateClassUnderTest, G6Level, G4Level):
    """
    Generic setUp for test cases that test a single control state
    
    Args:
        testInstance (Object)           the TestCase we are setting up
        stateClassUnderTest (Class)     the ControlStateABC subclass under test
        G6Level (int)                   initial model water level for G6
        G4Level (int)                   initial model water level for G4
    """
    testInstance.wm = stagePiWaterModel(G6Level, G4Level)
    
    # stagepilogic looks for Tools.logiccoretools in Tools.logiccoretools
    testInstance.wm.overrideFunctions(Tools.logiccoretools)
    
    # Control states need a control state machine
    testInstance.csm = Mock(spec=stagepilogic.StagePiControlLogic)
    
    # Instantiate the control state
    testInstance.s = stateClassUnderTest(testInstance.csm)
    
def singleStateTestTearDown(testInstance):
    """
    Generic tearDown for test cases that test a single control state
    
    Args:
        testInstance (Object)       the TestCase we are tearing down
    """
    testInstance.wm.unOverrideFunctions()
    testInstance.wm = None
    testInstance.csm = None
    testInstance.s = None

class TestStagePiInitState(unittest.TestCase):
    """
    Full tests of class StagePiInitState
    """
    def setUp(self):
        # Arbitrary initial water levels, since we're testing several levels
        singleStateTestSetUp(self, stagepilogic.StagePiInitState, 500, 500)
    
    def tearDown(self):
        singleStateTestTearDown(self)
    
    def testGetStateName(self):
        """
        Tests whether getStateName returns the correct state name
        """
        self.assertEqual(self.s.getStateName(), "StagePiInitState")
    
    def testGetPreferredReadingInterval(self):
        """
        Tests whether the state has the correct preferred reading interval
        """
        self.assertEqual(self.s.getPreferredReadingInterval(), 15)
    
    def testSetupState(self):
        """
        Tests whether StagePiInitState has the correct control outputs
        when first set up.
        """
        # Check that StagePiInitState does not try to control any devices
        self.s.setupState()
        self.assertListEqual(self.wm.controlled_devices, [],
                             "StagePiInitState should not have "
                             "attempted to control any devices.")
    
    def testTransitionToG6Empty(self):
        """
        Tests whether StagePiInitState will transition into
        StagePiG6EmptyState under the expected conditions.
        """
        self.wm.setVesselLevel("G6", 0)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG6EmptyState,
            self.s)
    
    def testTransitionToG4Overfilled(self):
        """
        Tests whether StagePiInitState will transition into
        StagePiG4OverfilledState under the expected conditions.
        """
        self.wm.setVesselLevel("G4",
                               stagepilogic.levels["G4Overfull"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4OverfilledState,
            self.s)
    
    def testTransitionToG4Filled(self):
        """
        Tests whether StagePiInitState will transition into
        StagePiG4FilledState under the expected conditions.
        """
        self.wm.setVesselLevel("G4",
                               stagepilogic.levels["G4Full"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4FilledState,
            self.s)
    
    def testTransitionToG4VeryNearlyFilled(self):
        """
        Tests whether StagePiInitState will transition into
        StagePiG4VeryNearlyFilledState under the expected conditions.
        """
        self.wm.setVesselLevel("G4",
                               stagepilogic.levels["G4VeryNearlyFull"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4VeryNearlyFilledState,
            self.s)
    
    def testTransitionToG4NearlyFilled(self):
        """
        Tests whether StagePiInitState will transition into
        StagePiG4NearlyFilledState under the expected conditions.
        """
        self.wm.setVesselLevel("G4",
                               stagepilogic.levels["G4NearlyFull"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4NearlyFilledState,
            self.s)
    
    def testTransitionToG4Filling(self):
        """
        Tests whether StagePiInitState will transition into
        StagePiG4FillingState under the expected conditions.
        """
        self.wm.setVesselLevel("G4",
                               stagepilogic.levels["G4NearlyFull"] - 1)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4FillingState,
            self.s)

class TestStagePiG6EmptyState(unittest.TestCase):
    """
    Full tests of class StagePiG6EmptyState
    """
    def setUp(self):
        # Start with G6 modelled as being empty, as this will be needed
        # for most of the tests. Arbitrary level for G4.
        singleStateTestSetUp(self,
                             stagepilogic.StagePiG6EmptyState,
                             stagepilogic.levels["G6NotEmpty"] - 1,
                             500)
    
    def tearDown(self):
        singleStateTestTearDown(self)
    
    def testGetStateName(self):
        """
        Tests whether getStateName returns the correct state name
        """
        self.assertEqual(self.s.getStateName(), "StagePiG6EmptyState")
    
    def testGetPreferredReadingInterval(self):
        """
        Tests whether the state has the correct preferred reading interval
        """
        self.assertEqual(self.s.getPreferredReadingInterval(), 60)
    
    def testSetupState(self):
        """
        Tests whether StagePiG6EmptyState has the correct control
        outputs when first set up.
        """
        # Check that only V12 was controlled
        self.s.setupState()
        self.assertEqual(self.wm.controlled_devices, ["VALVE12:V12"])
        
        # Check that V12 was fully closed
        self.assertEqual(self.wm.getDeviceState("VALVE12", "V12"), "0%")
        
        #TODO: This test will need to change if the matrix pump is to be used
    
    def testNoTransition(self):
        """
        Tests that StagePiG6EmptyState does not transition into another
        state under the initial test conditions.
        
        The initial conditions should be chosen so that they do not
        justify a transition. This permits the other tests to assume
        that no transition would have occurred if they did not alter
        the conditions.
        """
        self.s.doLogic(30)
        self.csm.setStateBy.assert_not_called()
    
    def testTransitionToG4Overfilled(self):
        """
        Tests whether StagePiG6EmptyState will transition into
        StagePiG4OverfilledState under the expected conditions
        """
        # Check that transition occurs when G4 is overfull and G6 is
        # still empty
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4Overfull"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4OverfilledState,
            self.s)
        
        # Check that transition occurs when G4 is overfull and G6 is no
        # longer empty
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G6", stagepilogic.levels["G6NotEmpty"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4OverfilledState,
            self.s)
    
    def testTransitionToG4Filled(self):
        """
        Tests whether StagePiG6EmptyState will transition into
        StagePiG4FilledState under the expected conditions
        """
        # Check that there is no transition when G6 remains empty
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4Full"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_not_called()
        
        # Check that there is a transition when G6 is no longer empty
        self.wm.setVesselLevel("G6", stagepilogic.levels["G6NotEmpty"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4FilledState,
            self.s)
    
    def testTransitionToG4VeryNearlyFilled(self):
        """
        Tests whether StagePiG6EmptyState will transition into
        StagePiG4VeryNearlyFilledState under the expected conditions
        """
        # Check that there is no transition when G6 remains empty
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4VeryNearlyFull"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_not_called()
        
        # Check that there is a transition when G6 is no longer empty
        self.wm.setVesselLevel("G6", stagepilogic.levels["G6NotEmpty"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4VeryNearlyFilledState,
            self.s)
    
    def testTransitionToG4NearlyFilled(self):
        """
        Tests whether StagePiG6EmptyState will transition into
        StagePiG4NearlyFilledState under the expected conditions
        """
        # Check that there is no transition when G6 remains empty
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4NearlyFull"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_not_called()
        
        # Check that there is a transition when G6 is no longer empty
        self.wm.setVesselLevel("G6", stagepilogic.levels["G6NotEmpty"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4NearlyFilledState,
            self.s)
    
    def testTransitionToG4Filling(self):
        """
        Tests whether StagePiG6EmptyState will transition into
        StagePiG4FillingState under the expected conditions
        """
        # Check that there is no transition when G6 remains empty
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4NearlyFull"] - 1)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_not_called()
        
        # Check that there is a transition when G6 is no longer empty
        self.wm.setVesselLevel("G6", stagepilogic.levels["G6NotEmpty"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4FillingState,
            self.s)

class TestStagePiG4OverfilledState(unittest.TestCase):
    """
    Full tests of class StagePiG4OverfilledState
    """
    def setUp(self):
        # Start with G4 modelled as being overfilled, as this will be
        # needed for most of the tests. Arbitrary level for G6.
        singleStateTestSetUp(self,
                             stagepilogic.StagePiG4OverfilledState,
                             500,
                             stagepilogic.levels["G4Overfull"])
    
    def tearDown(self):
        singleStateTestTearDown(self)
    
    def testGetStateName(self):
        """
        Tests whether getStateName returns the correct state name
        """
        self.assertEqual(self.s.getStateName(), "StagePiG4OverfilledState")
    
    def testGetPreferredReadingInterval(self):
        """
        Tests whether the state has the correct preferred reading interval
        """
        self.assertEqual(self.s.getPreferredReadingInterval(), 60)
    
    def testSetupState(self):
        """
        Tests whether StagePiG4OverfilledState has the correct control
        outputs when first set up.
        """
        # Check that only V12 was controlled
        self.s.setupState()
        self.assertEqual(self.wm.controlled_devices, ["VALVE12:V12"])
        
        # Check that V12 was fully closed
        self.assertEqual(self.wm.getDeviceState("VALVE12", "V12"), "0%")
        
        #TODO: this test will need to change if the matrix pump is to be used
    
    def testNoTransition(self):
        """
        Tests that StagePiG4OverfilledState does not transition into another
        state under the initial test conditions.
        
        The initial conditions should be chosen so that they do not
        justify a transition. This permits the other tests to assume
        that no transition would have occurred if they did not alter
        the conditions.
        """
        self.s.doLogic(30)
        self.csm.setStateBy.assert_not_called()
    
    def testTransitionToG6Empty(self):
        """
        Tests whether StagePiG4OverfilledState will transition into
        StagePiG6EmptyState under the expected conditions.
        """
        # Should NOT transition if G6 becomes empty but G4 remains overfull
        self.wm.setVesselLevel("G6", stagepilogic.levels["G6NotEmpty"] - 1)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_not_called()
        
        # But should transition if G4 then becomes less than overfull
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4Full"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG6EmptyState,
            self.s)
    
    def testTransitionToG4Filled(self):
        """
        Tests whether StagePiG4OverfilledState will transition into
        StagePiG4FilledState under the expected conditions.
        """
        # Should transition if G4 becomes less than overfull
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4Full"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4FilledState,
            self.s)
        
        # Should transition if G4 becomes much less than overfull
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G4", 0)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4FilledState,
            self.s)
        
        # If G6 is empty, should transition there instead
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G6", 0)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG6EmptyState,
            self.s)

class TestStagePiG4FilledState(unittest.TestCase):
    """
    Full tests of class StagePiG4FilledState
    """
    def setUp(self):
        # Start with G4 modelled as being filled, as this will be
        # needed for most of the tests. Arbitrary level for G6.
        singleStateTestSetUp(self,
                             stagepilogic.StagePiG4FilledState,
                             500,
                             stagepilogic.levels["G4Full"])
    
    def tearDown(self):
        singleStateTestTearDown(self)
    
    def testGetStateName(self):
        """
        Tests whether getStateName returns the correct state name
        """
        self.assertEqual(self.s.getStateName(), "StagePiG4FilledState")
    
    def testGetPreferredReadingInterval(self):
        """
        Tests whether the state has the correct preferred reading interval
        """
        self.assertEqual(self.s.getPreferredReadingInterval(), 60)
    
    def testSetupState(self):
        """
        Tests whether StagePiG4FilledState has the correct control
        outputs when first set up.
        """
        # Check that only V12 was controlled
        self.s.setupState()
        self.assertEqual(self.wm.controlled_devices, ["VALVE12:V12"])
        
        # Check that V12 was fully closed
        self.assertEqual(self.wm.getDeviceState("VALVE12", "V12"), "0%")
        
        #TODO: this test will need to change if the matrix pump is to be used
    
    def testNoTransition(self):
        """
        Tests that StagePiG4FilledState does not transition into another
        state under the initial test conditions.
        
        The initial conditions should be chosen so that they do not
        justify a transition. This permits the other tests to assume
        that no transition would have occurred if they did not alter
        the conditions.
        """
        self.s.doLogic(30)
        self.csm.setStateBy.assert_not_called()
    
    def testTransitionToG6Empty(self):
        """
        Tests whether StagePiG4FilledState will transition into
        StagePiG6EmptyState under the expected conditions.
        """
        # Should transition if G6 becomes empty
        self.wm.setVesselLevel("G6", stagepilogic.levels["G6NotEmpty"] - 1)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG6EmptyState,
            self.s)
    
    def testTransitionToG4VeryNearlyFilled(self):
        """
        Tests whether StagePiG4FilledState will transition into
        StagePiG4VeryNearlyFilledState under the expected conditions.
        """
        # Should transition if G4 becomes less than full
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4VeryNearlyFull"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4VeryNearlyFilledState,
            self.s)
        
        # Should transition if G4 becomes much less than full
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G4", 0)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4VeryNearlyFilledState,
            self.s)
        
        # If G6 is empty, should transition there instead
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G6", 0)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG6EmptyState,
            self.s)
    
    def testTransitionToG4Overfilled(self):
        """
        Tests whether StagePiG4FilledState will transition into
        StagePiG6OverfilledState under the expected conditions.
        """
        # Should transition if G4 becomes overfull
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4Overfull"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4OverfilledState,
            self.s)
        
        # Should still transition there even if G6 is empty
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G6", 0)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4OverfilledState,
            self.s)

class TestStagePiG4VeryNearlyFilledState(unittest.TestCase):
    """
    Full tests of class StagePiG4VeryNearlyFilledState
    """
    def setUp(self):
        # Start with G4 modelled as being very nearly filled, as this
        # will be needed for most of the tests. Arbitrary level for G6.
        singleStateTestSetUp(self,
                             stagepilogic.StagePiG4VeryNearlyFilledState,
                             500,
                             stagepilogic.levels["G4VeryNearlyFull"])
    
    def tearDown(self):
        singleStateTestTearDown(self)
    
    def testGetStateName(self):
        """
        Tests whether getStateName returns the correct state name
        """
        self.assertEqual(self.s.getStateName(),
                         "StagePiG4VeryNearlyFilledState")
    
    def testGetPreferredReadingInterval(self):
        """
        Tests whether the state has the correct preferred reading interval
        """
        self.assertEqual(self.s.getPreferredReadingInterval(), 15)
    
    def testSetupState(self):
        """
        Tests whether StagePiG4VeryNearlyFilledState has the correct
        control outputs when first set up.
        """
        # Check that only V12 was controlled
        self.s.setupState()
        self.assertEqual(self.wm.controlled_devices, ["VALVE12:V12"])
        
        # Check that V12 was opened 25%
        self.assertEqual(self.wm.getDeviceState("VALVE12", "V12"), "25%")
        
        #TODO: this test will need to change if the matrix pump is to be used
    
    def testNoTransition(self):
        """
        Tests that StagePiG4VeryNearlyFilledState does not transition
        into another state under the initial test conditions.
        
        The initial conditions should be chosen so that they do not
        justify a transition. This permits the other tests to assume
        that no transition would have occurred if they did not alter
        the conditions.
        """
        self.s.doLogic(30)
        self.csm.setStateBy.assert_not_called()
    
    def testTransitionToG6Empty(self):
        """
        Tests whether StagePiG4VeryNearlyFilledState will transition into
        StagePiG6EmptyState under the expected conditions.
        """
        # Should transition if G6 becomes empty
        self.wm.setVesselLevel("G6", stagepilogic.levels["G6NotEmpty"] - 1)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG6EmptyState,
            self.s)
    
    def testTransitionToG4NearlyFilled(self):
        """
        Tests whether StagePiG4VeryNearlyFilledState will transition into
        StagePiG4NearlyFilledState under the expected conditions.
        """
        # Should transition if G4 becomes less than very nearly full
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4NearlyFull"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4NearlyFilledState,
            self.s)
        
        # Should transition if G4 becomes much less than very nearly full
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G4", 0)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4NearlyFilledState,
            self.s)
        
        # If G6 is empty, should transition to G6Empty instead
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G6", 0)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG6EmptyState,
            self.s)
    
    def testTransitionToG4Filled(self):
        """
        Tests whether StagePiG4VeryNearlyFilledState will transition into
        StagePiG6FilledState under the expected conditions.
        """
        # Should transition if G4 becomes full
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4Full"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4FilledState,
            self.s)
        
        # If G6 is empty, should transition to G6Empty instead
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G6", 0)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG6EmptyState,
            self.s)

class TestStagePiG4NearlyFilledState(unittest.TestCase):
    """
    Full tests of class StagePiG4NearlyFilledState
    """
    def setUp(self):
        # Start with G4 modelled as being nearly filled, as this will
        # be needed for most of the tests. Arbitrary level for G6.
        singleStateTestSetUp(self,
                             stagepilogic.StagePiG4NearlyFilledState,
                             500,
                             stagepilogic.levels["G4NearlyFull"])
    
    def tearDown(self):
        singleStateTestTearDown(self)
    
    def testGetStateName(self):
        """
        Tests whether getStateName returns the correct state name
        """
        self.assertEqual(self.s.getStateName(),
                         "StagePiG4NearlyFilledState")
    
    def testGetPreferredReadingInterval(self):
        """
        Tests whether the state has the correct preferred reading interval
        """
        self.assertEqual(self.s.getPreferredReadingInterval(), 30)
    
    def testSetupState(self):
        """
        Tests whether StagePiG4NearlyFilledState has the correct
        control outputs when first set up.
        """
        # Check that only V12 was controlled
        self.s.setupState()
        self.assertEqual(self.wm.controlled_devices, ["VALVE12:V12"])
        
        # Check that V12 was opened 50%
        self.assertEqual(self.wm.getDeviceState("VALVE12", "V12"), "50%")
        
        #TODO: this test will need to change if the matrix pump is to be used
    
    def testNoTransition(self):
        """
        Tests that StagePiG4NearlyFilledState does not transition into
        another state under the initial test conditions.
        
        The initial conditions should be chosen so that they do not
        justify a transition. This permits the other tests to assume
        that no transition would have occurred if they did not alter
        the conditions.
        """
        self.s.doLogic(30)
        self.csm.setStateBy.assert_not_called()
    
    def testTransitionToG6Empty(self):
        """
        Tests whether StagePiG4NearlyFilledState will transition into
        StagePiG6EmptyState under the expected conditions.
        """
        # Should transition if G6 becomes empty
        self.wm.setVesselLevel("G6", stagepilogic.levels["G6NotEmpty"] - 1)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG6EmptyState,
            self.s)
    
    def testTransitionToG4Filling(self):
        """
        Tests whether StagePiG4NearlyFilledState will transition into
        StagePiG4FillingState under the expected conditions.
        """
        # Should transition if G4 becomes less than nearly full
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4NearlyFull"] - 1)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4FillingState,
            self.s)
        
        # Should transition if G4 becomes much less than nearly full
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G4", 0)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4FillingState,
            self.s)
        
        # If G6 is empty, should transition to G6Empty instead
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G6", 0)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG6EmptyState,
            self.s)
    
    def testTransitionToG4VeryNearlyFilled(self):
        """
        Tests whether StagePiG4NearlyFilledState will transition into
        StagePiG6VeryNearlyFilledState under the expected conditions.
        """
        # Should transition if G4 becomes very nearly filled
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4VeryNearlyFull"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4VeryNearlyFilledState,
            self.s)
        
        # If G6 is empty, should transition to G6Empty instead
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G6", 0)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG6EmptyState,
            self.s)

class TestStagePiG4FillingState(unittest.TestCase):
    """
    Full tests of class StagePiG4FillingState
    """
    def setUp(self):
        # Start with G4 modelled as being below nearly full, as this
        # will be needed for most of the tests. Arbitrary level for G6.
        singleStateTestSetUp(self,
                             stagepilogic.StagePiG4FillingState,
                             500,
                             stagepilogic.levels["G4NearlyFull"] - 1)
    
    def tearDown(self):
        singleStateTestTearDown(self)
    
    def testGetStateName(self):
        """
        Tests whether getStateName returns the correct state name
        """
        self.assertEqual(self.s.getStateName(), "StagePiG4FillingState")
    
    def testGetPreferredReadingInterval(self):
        """
        Tests whether the state has the correct preferred reading interval
        """
        self.assertEqual(self.s.getPreferredReadingInterval(), 60)
    
    def testSetupState(self):
        """
        Tests whether StagePiG4FillingState has the correct
        control outputs when first set up.
        """
        # Check that only V12 was controlled
        self.s.setupState()
        self.assertEqual(self.wm.controlled_devices, ["VALVE12:V12"])
        
        # Check that V12 was opened 100%
        self.assertEqual(self.wm.getDeviceState("VALVE12", "V12"), "100%")
        
        #TODO: this test will need to change if the matrix pump is to be used
    
    def testNoTransition(self):
        """
        Tests that StagePiG4FillingState does not transition into
        another state under the initial test conditions.
        
        The initial conditions should be chosen so that they do not
        justify a transition. This permits the other tests to assume
        that no transition would have occurred if they did not alter
        the conditions.
        """
        self.s.doLogic(30)
        self.csm.setStateBy.assert_not_called()
    
    def testTransitionToG6Empty(self):
        """
        Tests whether StagePiG4FillingState will transition into
        StagePiG6EmptyState under the expected conditions.
        """
        # Should transition if G6 becomes empty
        self.wm.setVesselLevel("G6", stagepilogic.levels["G6NotEmpty"] - 1)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG6EmptyState,
            self.s)
    
    def testTransitionToG4NearlyFilled(self):
        """
        Tests whether StagePiG4FillingState will transition into
        StagePiG6NearlyFilledState under the expected conditions.
        """
        # Should transition if G4 becomes nearly filled
        self.wm.setVesselLevel("G4", stagepilogic.levels["G4NearlyFull"])
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG4NearlyFilledState,
            self.s)
        
        # If G6 is empty, should transition to G6Empty instead
        self.csm.setStateBy.reset_mock()
        self.wm.setVesselLevel("G6", 0)
        self.s.doLogic(30)
        self.csm.setStateBy.assert_called_once_with(
            stagepilogic.StagePiG6EmptyState,
            self.s)

class TestStagePiControlLogicFunction(unittest.TestCase):
    @unittest.expectedFailure
    def testsNotImplemented(self):
        # Fail as a reminder to write these tests.
        self.fail("These tests have not yet been written.")