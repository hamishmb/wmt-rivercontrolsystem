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
from collections import deque
import unittest
import sys
import threading

#Import other modules.
sys.path.append('../..') #Need to be able to import the Tools module from here.

import Tools
import Tools.sockettools as socket_tools

#Import test data and functions.
#TODO if needed.

class TestSockets(unittest.TestCase):
    """This test class tests the features of the Sockets class in Tools/sockettools.py"""

    def setUp(self):
        self.socket = socket_tools.Sockets("Plug")

    def tearDown(self):
        del self.socket

    def set_exited_flag(self):
        self.socket.handler_exited = True

    def test_constructor_1(self):
        """Test #1: Test that the constructor works when no name is specified"""
        for _type in ("Plug", "Socket"):
            socket = socket_tools.Sockets(_type)

            self.assertEqual(socket.port_number, -1)
            self.assertEqual(socket.server_address, "")
            self.assertEqual(socket.type, _type)
            self.assertEqual(socket.name, "Unknown")
            self.assertEqual(socket.underlying_socket, None)
            self.assertEqual(socket.server_socket, None)
            self.assertEqual(socket.handler_thread, None)
            self.assertTrue(socket.verbose)
            self.assertFalse(socket.ready_to_send)
            self.assertFalse(socket.reconnected)
            self.assertFalse(socket.internal_request_exit)
            self.assertFalse(socket.handler_exited)
            self.assertEqual(socket.in_queue, deque())
            self.assertEqual(socket.out_queue, deque())

    def test_constructor_2(self):
        """Test #2: Test that the constructor works when a name is specified"""
        for _type in ("Plug", "Socket"):
            socket = socket_tools.Sockets(_type, "Test Socket")

            self.assertEqual(socket.port_number, -1)
            self.assertEqual(socket.server_address, "")
            self.assertEqual(socket.type, _type)
            self.assertEqual(socket.name, "Test Socket")
            self.assertEqual(socket.underlying_socket, None)
            self.assertEqual(socket.server_socket, None)
            self.assertEqual(socket.handler_thread, None)
            self.assertTrue(socket.verbose)
            self.assertFalse(socket.ready_to_send)
            self.assertFalse(socket.reconnected)
            self.assertFalse(socket.internal_request_exit)
            self.assertFalse(socket.handler_exited)
            self.assertEqual(socket.in_queue, deque())
            self.assertEqual(socket.out_queue, deque())

    def test_constructor_3(self):
        """Test #3: Test that the constructor fails when _type is not 'Plug' or 'Socket'"""
        for _type in ("plug", "socket", "test", "notatype", None, 1, True):
            try:
                socket = socket_tools.Sockets(_type, "Test Socket")

            except ValueError:
                #Expected.
                pass

            else:
                #All of these must throw errors!
                self.assertTrue(False, "ValueError expected for data: "+str(_type))

    def test_constructor_4(self):
        """Test #4: Test that the constructor fails when name is not a string"""
        for _name in (None, 1, True, 6.7, (), [], {}):
            try:
                socket = socket_tools.Sockets("Socket", _name)

            except ValueError:
                #Expected.
                pass

            else:
                #All of these must throw errors!
                self.assertTrue(False, "ValueError expected for data: "+str(_name))

    def test_set_portnumber_1(self):
        """Test #1: Test that this works when valid portnumbers are passed."""
        #Highest valid port is 65535.
        for i in range(1, 65536):
            self.socket.set_portnumber(i)
            self.assertEqual(i, self.socket.port_number)

    def test_set_portnumber_2(self):
        """Test #2: Test that this fails with invalid portnumbers."""
        for portnumber in (-100, -50, 0, 6.7, 65536, (), [], False, None, "Test"):
            try:
                self.socket.set_portnumber(portnumber)

            except ValueError:
                #Expected.
                pass

            else:
                #This must fail for all of these values.
                self.assertTrue(False, "ValueError expected for data: "+str(portnumber))

    def test_set_server_address_1(self):
        """Test #1: Test that this works when a valid IPv4 address is given"""
        #Don't test with all of them, because that takes far too long.
        for i in range(1, 255, 10):
            for j in range(1, 255, 10):
                for k in range(1, 255, 5):
                    self.socket.set_server_address("192."+str(i)+"."
                                                   + str(j)+"."+str(k))

                    self.assertEqual(self.socket.server_address,
                                     "192."+str(i)+"."+str(j)+"."
                                     + str(k))

    def test_set_server_address_2(self):
        """Test #2: Test that this fails when given invalid IPv4 addresses"""
        for ip in ("0.0.0.0", "255.255.255.255", "....", "", "192.168.1.255",
                   "test", 0, False, None, (), [], {}, 5.6):

            try:
                self.socket.set_server_address(ip)

            except ValueError:
                #Expected.
                pass

            else:
                #All of these must fail!
                self.assertTrue(False, "ValueError expected for data: "+str(ip))

    def test_set_console_output_1(self):
        """Test #1: Test that this works when given boolean values."""
        for _bool in (True, False):
            self.socket.set_console_output(_bool)
            self.assertEqual(self.socket.verbose, _bool)

    def test_set_console_output_2(self):
        """Test #2: Test that this fails when given invalid values."""
        for value in (None, 5, 4.5, [], (), {}, "True"):
            try:
                self.socket.set_console_output(value)

            except ValueError:
                #Expected.
                pass

            else:
                #All of these must fail!
                self.assertTrue(False, "ValueError expected for data: "+str(value))

    def test_reset_1(self):
        """Test #1: Test that this works as expected."""
        self.socket.reset()

        self.assertFalse(self.socket.ready_to_send)
        self.assertFalse(self.socket.reconnected)
        self.assertFalse(self.socket.internal_request_exit)
        self.assertFalse(self.socket.handler_exited)
        self.assertEqual(self.socket.in_queue, deque())
        self.assertEqual(self.socket.out_queue, deque())
        self.assertEqual(self.socket.underlying_socket, None)
        self.assertEqual(self.socket.server_socket, None)

    def test_is_ready_1(self):
        """Test #1: Test that this works as expected."""
        for value in (True, False):
            self.socket.ready_to_send = value
            self.assertEqual(self.socket.is_ready(), value)

    def test_just_reconnected_1(self):
        """Test #1: Test that this works as expected"""
        for value in (True, False):
            self.socket.reconnected = value
            self.assertEqual(self.socket.just_reconnected(), value)

            #This resets to False after it has been called.
            self.assertFalse(self.socket.just_reconnected())

    def test_wait_for_handler_to_exit_1(self):
        """Test #1: Test this works as expected when handler has just exited"""
        self.socket.handler_exited = True

        self.socket.wait_for_handler_to_exit()

    def test_wait_for_handler_to_exit_2(self):
        """Test #2: Test this works as expected when handler takes 10 seconds to exit."""
        #Schedule the exit flag to be set in 10 seconds.
        threading.Timer(10, self.set_exited_flag).start()
        self.socket.wait_for_handler_to_exit()

    def test_handler_has_exited_1(self):
        """Test #1: Test this works as expected."""
        for value in (True, False):
            self.socket.handler_exited = value
            self.assertEqual(self.socket.handler_has_exited(), value)

    def test_start_handler_1(self):
        """Test #1: Test that this works as expected"""
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
