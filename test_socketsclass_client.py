#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Sockets Class (client) test for the River System Control and Monitoring Software Version 0.9.1
# This file is part of the River System Control and Monitoring Software.
# Copyright (C) 2017 Wimborne Model Town
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3 or,
# at your option, any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import datetime
import sys
import os

def RunStandalone():
    #Do required imports.
    import Tools.sockettools as SocketTools

    SocketTools.logger = logger

    print("Testing. Please stand by...")

    #Create the sockets object.
    Socket = SocketTools.Sockets("Plug")

    #Set the object up.
    Socket.SetPortNumber(30000)
    Socket.SetServerAddress("localhost")

    Socket.StartHandler()

    while not Socket.IsReady(): time.sleep(0.5)

    try:
        while True:
            Socket.Write("Hello world!")
            time.sleep(1)

    except KeyboardInterrupt:
        #Clean up.
        Socket.RequestHandlerExit()
        Socket.WaitForHandlerToExit()
        Socket.Reset()

if __name__ == "__main__":
    #Set up basic logging to stdout.
    import logging

    logger = logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p', level=logging.DEBUG)

    RunStandalone() 
