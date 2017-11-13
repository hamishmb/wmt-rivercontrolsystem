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

import logging
import time
import sys
import os

sys.path.insert(0, os.path.abspath('../../'))
sys.path.insert(0, os.path.abspath('../'))

def run_standalone():
    #Do required imports.
    import Tools.sockettools as socket_tools

    socket_tools.logger = logger

    print("Testing. Please stand by...")

    #Create the sockets object.
    socket = socket_tools.Sockets("Plug")

    #Set the object up.
    socket.set_portnumber(30000)
    socket.set_server_address("localhost")

    socket.start_handler()

    while not socket.is_ready():
        time.sleep(0.5)

    try:
        while True:
            socket.write("Hello world!")
            time.sleep(1)

    except KeyboardInterrupt:
        #Clean up.
        socket.request_handler_exit()
        socket.wait_for_handler_to_exit()
        socket.reset()

if __name__ == "__main__":
    #Set up basic logging to stdout.
    logger = logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p', level=logging.DEBUG)

    run_standalone()
