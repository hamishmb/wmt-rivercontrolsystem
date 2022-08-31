#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Core Tools Unit Test Data for the River System Control and Monitoring Software
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

import datetime
import sys
import os

#Import other modules.
sys.path.insert(0, os.path.abspath('../../../')) #Need to be able to import the Tools module from here.

import Tools

class Dummy:
    """A dummy class that does nothing, just used for testing"""
    def __init__(self): pass

#Sample values for the arguments to the Reading class constructor.
TEST_READING_DATA = [
    [str(datetime.datetime.now()), 0, "G4:M0", "400", "OK"],
    [str(datetime.datetime.now()), 1, "G4:M0", "400", "OK"],
    [str(datetime.datetime.now()), 56, "G4:M8", "450", "Fault Detected"],
    [str(datetime.datetime.now()), 728, "SUMP:M0", "475", "OK"],
    [str(datetime.datetime.now()), 0, "G6:FS0", "True", "OK"],
    [str(datetime.datetime.now()), 3, "G4:M2", "0", "OK"],
    [str(datetime.datetime.now()), 7, "G4:M1", "405", "OK"],
    [str(datetime.datetime.now()), 8885, "G2:M0", "440", "OK"],
    [str(datetime.datetime.now()), 34567, "SUMP:M1", "420", "OK"],
    [str(datetime.datetime.now()), 3856, "G2:M0", "876", "OK"],
    [str(datetime.datetime.now()), 3, "G5:M0", "854", "OK"],
    [str(datetime.datetime.now()), 2, "G9:M0", "925", "OK"]
]

#Bad sample values for the arguments to the Reading class constructor.
TEST_READING_BAD_DATA = [
    #Time is not converted to a string.
    [datetime.datetime.now(), 1, "G4:M0", "400", "OK"],

    #Invalid tick value.
    [str(datetime.datetime.now()), -1, "G4:M0", "400", "OK"],
    [str(datetime.datetime.now()), "1", "G4:M0", "400", "OK"],

    #Invalid ID.
    [str(datetime.datetime.now()), 1, "G4:M0:FS0", "400", "OK"],
    [str(datetime.datetime.now()), 1, "G4", "400", "OK"],
    [str(datetime.datetime.now()), 1, ":", "400", "OK"],
    [str(datetime.datetime.now()), 1, "::", "400", "OK"],

    #Invalid value (not a string).
    [str(datetime.datetime.now()), 1, "G4:M0", 400, "OK"],
    [str(datetime.datetime.now()), 1, "G4:M0", True, "OK"],

    #Invalid status (not a string).
    [str(datetime.datetime.now()), 1, "G4:M0", "400", 0],
    [str(datetime.datetime.now()), 1, "G4:M0", "400", True],
    [str(datetime.datetime.now()), 1, "G4:M0", "400", 7.8],
]
