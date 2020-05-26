#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Sockets Tools Unit Test Data for the River System Control and Monitoring Software
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

import datetime
import sys
import os
import pickle
import _pickle

#Import other modules.
sys.path.insert(0, os.path.abspath('../../../')) #Need to be able to import the Tools module from here.

#Global variables for testing.
unpickled_data = []

#Fake socket class to test the setup functions.
class fake_socket:
    #Method used to create a socket, but this version returns an objects of this class.
    @classmethod
    def socket(cls, junk1, junk2):
        return fake_socket()

    def connect(self, ip, portno):
        return False

    @classmethod
    def sendall(cls, data):
        return

#Fake socket class to test the setup functions.
class fake_socket_error_pickling:
    #Method used to create a socket, but this version returns an objects of this class.
    @classmethod
    def socket(cls, junk1, junk2):
        return fake_socket()

    def connect(self, ip, portno):
        return False

    @classmethod
    def sendall(cls, data):
        raise _pickle.PicklingError("Test")

#Fake socket class to test the setup functions.
class fake_socket_oserror:
    #Method used to create a socket, but this version returns an objects of this class.
    @classmethod
    def socket(cls, junk1, junk2):
        return fake_socket()

    def connect(self, ip, portno):
        return False

    @classmethod
    def sendall(cls, data):
        raise OSError("test")

    @classmethod
    def shutdown(cls, flag):
        raise OSError("test")

    @classmethod
    def close(cls):
        raise OSError("test")

#Fake socket class to test the setup functions.
class fake_socket_unpickle_data:
    #Method used to create a socket, but this version returns an objects of this class.
    @classmethod
    def socket(cls, junk1, junk2):
        return fake_socket()

    def connect(self, ip, portno):
        return False

    @classmethod
    def sendall(cls, data):
        global unpickled_data

        datalist = data.split(b"ENDMSG")[:-1]

        for data in datalist:
            unpickled_data.append(pickle.loads(data))

#Fake socket class to test the setup functions.
class fake_socket_peer_gone:
    #Method used to create a socket, but this version returns an objects of this class.
    @classmethod
    def socket(cls, junk1, junk2):
        return fake_socket()

    def connect(self, ip, portno):
        return False

    @classmethod
    def sendall(cls, data):
        return

    @classmethod
    def recv(cls, size):
        return b""

#Fake socket class to test the setup functions.
class fake_socket_with_data:
    #Method used to create a socket, but this version returns an objects of this class.
    @classmethod
    def socket(cls, junk1, junk2):
        return fake_socket()

    def connect(self, ip, portno):
        return False

    @classmethod
    def sendall(cls, data):
        return

    @classmethod
    def recv(cls, size):
        #NOTE: This is pickled data.
        return b"\x80\x03K\x00.ENDMSG\x80\x03G@\x1a\xcc\xcc\xcc\xcc\xcc\xcd.ENDMSG" \
               b"\x80\x03N.ENDMSG\x80\x03\x88.ENDMSG\x80\x03\x89.ENDMSG\x80\x03)." \
               b"ENDMSG\x80\x03]q\x00.ENDMSG\x80\x03}q\x00.ENDMSG\x80\x03X\x04\x00\x00\x00testq\x00.ENDMSG"

#Fake socket class to test the setup functions.
class fake_socket_unhandled_error:
    #Method used to create a socket, but this version returns an objects of this class.
    @classmethod
    def socket(cls, junk1, junk2):
        return fake_socket()

    def connect(self, ip, portno):
        return False

    @classmethod
    def sendall(cls, data):
        return

    @classmethod
    def recv(cls, size):
        raise RuntimeError("test")

#Fake select class for testing.
class select_ready:
    @classmethod
    def select(cls, junk1, junk2, junk3, junk4):
        return (True, True)

class select_ready_once:
    run = False

    @classmethod
    def select(cls, junk1, junk2, junk3, junk4):
        if not cls.run:
            cls.run = True
            return (True, True)

        else:
            return (False, False)

    @classmethod
    def reset(cls):
        cls.run = False

class select_not_ready:
    @classmethod
    def select(cls, junk1, junk2, junk3, junk4):
        return (False, False)

def fake_create_socket_oserror():
    raise OSError("Test")

def fake_handler_thread(junk):
    return False
