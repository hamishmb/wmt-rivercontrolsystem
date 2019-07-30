#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Socket Tools Unit Tests for the River System Control and Monitoring Software
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

# pylint: disable=too-few-public-methods
#
# Reason (too-few-public-methods): Test classes don't need many public members.

#Import modules
import unittest
import sys

#Import other modules.
sys.path.append('../..') #Need to be able to import the Tools module from here.

import Tools
import Tools.sockettools as socket_tools

#Import test data and functions.
#TODO if needed.

class TestSockets(unittest.TestCase):
    """This test class tests the features of the Sockets class in Tools/sockettools.py"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass

class TestSocketHandlerThread(unittest.TestCase):
    """
    This test class tests the features of the SocketsHandlerThread class in
    Tools/sockettools.py
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        pass
