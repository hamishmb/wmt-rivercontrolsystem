#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Shared Functions for Standalone Monitoring tools for the River System Control and Monitoring Software Version 0.9.1
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

import getopt
import sys

def usage(program_name):
    """Standard usage function for all monitors."""
    print("\nUsage: "+program_name+" [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:               Show this help message")
    print("       -f, --file:               Specify file to write the recordings to. Default: interactive.")
    print("       -c, --controlleraddress:  Specify the DNS name/IP of the controlling server we want to send our level data to, if any.")
    print("       -n <int>, --num=<int>     Specify number of readings to take before exiting. Without this option, readings will be taken until the program is terminated")
    print(program_name+" is released under the GNU GPL Version 3")
    print("Copyright (C) Wimborne Model Town 2017")

def handle_cmdline_options(program_name):
    """
    Handles commandline options for the standalone monitor programs.
    Usage:

        tuple HandleCmdlineOptions(function UsageFunc)
    """

    FileName = "Unknown"
    ServerAddress = None

    #Check all cmdline options are valid.
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:c:n:", ["help", "file=", "controlleraddress=", "num="])

    except getopt.GetoptError as err:
        #Invalid option. Show the help message and then exit.
        #Show the error.
        print(str(err))
        usage(program_name)
        sys.exit(2)

    #Do setup. o=option, a=argument.
    NumberOfReadingsToTake = 0 #Take readings indefinitely by default.

    for o, a in opts:
        if o in ["-n", "--num"]:
            NumberOfReadingsToTake = int(a)

        elif o in ["-f", "--file"]:
            FileName = a

        elif o in ["-c", "--controlleraddress"]:
            ServerAddress = a

        elif o in ["-h", "--help"]:
            usage(program_name)
            sys.exit()
    
        else:
            assert False, "unhandled option"

    return FileName, ServerAddress, NumberOfReadingsToTake
