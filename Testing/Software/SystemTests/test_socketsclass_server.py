#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Sockets Class (server) test for the River System Control and Monitoring Software
# This file is part of the River System Control and Monitoring Software.
# Copyright (C) 2017-2022 Wimborne Model Town
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
import getopt

sys.path.insert(0, os.path.abspath('../../../../'))
sys.path.insert(0, os.path.abspath('../../../'))

TEST_SITES = {
    #--------------- DUMMY SITE IDs for TESTING ---------------
    "ST0":
        {
            "Type": "Site",
            "ID": "ST0",
            "Name": "Sockets Test Site",
            "Default Interval": 15,
            "IPAddress": "127.0.0.1",
            "HostingSockets": False,
            "DBUser": "none",
            "DBPasswd": "none",

            #Local probes.
            "Probes": {},

            #Devices to control.
            "Devices": {},

            "ServerAddress": "127.0.0.1",
            "ServerPort": 30000,
            "ServerName": "test",
            "SocketName": "Test Socket",
            "SocketID": "SOCK0"
        },

    "ST1":
        {
            "Type": "Site",
            "ID": "ST1",
            "Name": "Sockets Test Site",
            "Default Interval": 15,
            "IPAddress": "127.0.0.1",
            "HostingSockets": False,
            "DBUser": "none",
            "DBPasswd": "none",

            #Local probes.
            "Probes": {},

            #Devices to control.
            "Devices": {},

            "ServerAddress": "127.0.0.1",
            "ServerPort": 30000,
            "ServerName": "test",
            "SocketName": "Test Socket",
            "SocketID": "SOCK0"
        },
}

def usage():
    """
    This function is used to output help information to the standard output
    if the user passes invalid/incorrect commandline arguments.

    Usage:

    >>> usage()
    """

    print("\nUsage: test_socketsclass_server.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:                   Show this help message")
    print("       -a, --address:                The IP address of the client")
    print("       -p, --portnumber:             The port number to use")
    print("test_socketsclass_server.py is released under the GNU GPL Version 3")
    print("Copyright (C) Wimborne Model Town 2017-2020")

def run_standalone():
    ip_address = None
    port = None

    #Check all cmdline options are valid.
    try:
        opts = getopt.getopt(sys.argv[1:], "ha:p:",
                             ["help", "address=", "portnumber="])[0]

    except getopt.GetoptError as err:
        #Invalid option. Show the help message and then exit.
        #Show the error.
        print(str(err))
        usage()
        sys.exit(2)

    #Do setup. o=option, a=argument.
    for opt, arg in opts:
        if opt in ("-a", "--address"):
            ip_address = arg

        elif opt in ("-p", "--portnumber"):
            #Enable testing mode.
            port = int(arg)

        elif opt in ("-h", "--help"):
            usage()
            sys.exit()

        else:
            assert False, "unhandled option"

    #Check ip and port were specified.
    assert ip_address is not None, "You must specify the IP address to connect to"
    assert port is not None, "You must specify the port number to connect to"

    #Do required imports.
    import config
    from Tools import sockettools

    config.SITE_SETTINGS.update(TEST_SITES)

    sockettools.logger = logger

    print("Testing. Please stand by...")

    #Create the sockets object.
    socket = sockettools.Sockets("Socket", "ST1")

    #Set the object up.
    socket.set_portnumber(port)
    socket.set_server_address(ip_address)

    socket.start_handler()

    while not socket.is_ready():
        time.sleep(0.5)

    try:
        while True:
            while socket.has_data():
                print(socket.read())
                socket.pop()

            time.sleep(1)

    except KeyboardInterrupt:
        #Clean up.
        config.EXITING = True
        socket.wait_for_handler_to_exit()

if __name__ == "__main__":
    #Set up basic logging to stdout.
    logger = logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p', level=logging.DEBUG)

    run_standalone()
