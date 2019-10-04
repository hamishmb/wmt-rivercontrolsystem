#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Configuration for the River System Control and Monitoring Software
# Copyright (C) 2017-2019 Wimborne Model Town
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

#TODO The way the lists are done here confuses Sphinx.
#is there a list syntax that can be used instead? - the generated
#docs are not displaying nicely.

"""
This is the configuration for all pis. These dictionaries (key-value
base data) provide the configuration for each site in a centralised,
easy-to-change file.

This takes the form of a dictionary object named "SITE_SETTINGS".
This object has detailed configuration for each site, namely the ID,
sockets to host (if any), (local) probes to monitor, and devices to
control.

In the dictionary, devices are identified according to their location
and type the following key, eg:

Sump Pi                        - SUMP
    Hall Effect (magnetic) Probe -     M0
    Main circulation Pump        -     P1
    Butts Return Pump            -     P0

Wendy Street Pi                - G4
    Hall Effect (magnetic) Probe -     M0
    Float Switch                 -     FS0

Gate Valve                     - V4

Full List of Devices and their ID Data, IP Addresses, Master Pi server Port and
Socket Numbers where applicable:

Sump Pi                                 - SUMP, 192.168.0.2
    Hall Effect (magnetic) Probe          -     SUMP:M0
    Other Probe (TBD)                     -     SUMP:TBD0
    Main circulation Pump                 -     SUMP:P1
    Butts Return Pump                     -     SUMP:P0

Railway Room Butts Pi                   - GR, 192.168.0.3, 30003, SOCK3
    Hall Effect (magnetic) Probe          -     G1:M0
    Other Probe (TBD)                     -     G1:TBD0
    Float Switch                          -     G1:FS0
    Hall Effect (magnetic) Probe          -     G2:M0
    Other Probe (TBD)                     -     G2:TBD0
    Float Switch                          -     G2:FS0
    Hall Effect (magnetic) Probe          -     G3:M0
    Other Probe (TBD)                     -     G3:TBD0
    Float Switch                          -     G3:FS0

Stage Butts Pi                            - G6, 192.168.0.6, 30006, SOCK6
    Hall Effect (magnetic) Probe          -     G4:M0
    Other Probe (TBD)                     -     G4:TBD0
    Float Switch                          -     G4:FS0

Wendy Street Butts Pi                   - G4, 192.168.0.4, 30004, SOCK4
    Hall Effect (magnetic) Probe          -     G4:M0
    Other Probe (TBD)                     -     G4:TBD0
    Float Switch                          -     G4:FS0

Gazebo Butts Pi                         - G5, 192.168.0.5, 30005, SOCK5
    Hall Effect (magnetic) Probe          -     G5:M0
    Other Probe (TBD)                     -     G5:TBD0
    Float Switch                          -     G5:FS0

Railway Room G1 Butts Group Gate Valve  - V1, 192.168.0.11, 30011, SOCK11

Railway Room G2 Butts Group Gate Valve  - V2, 192.168.0.12, 30012, SOCK12

Railway Room G3 Butts Group Gate Valve  - V3, 192.168.0.13, 30013, SOCK13

Wendy Street G4 Butts Group Gate Valve  - V4, 192.168.0.14, 30014, SOCK14

Gazebo G5 Butts Group Gate Valve        - V5, 192.168.0.15, 30015, SOCK15

Matrix Pump V6 Gate Valve               - V6, 192.168.0.16, 30016, SOCK16

Matrix Pump V7 Gate Valve               - V7, 192.168.0.17, 30017, SOCK17

Matrix Pump V8 Gate Valve               - V8, 192.168.0.18, 30018, SOCK18

Matrix Pump V9 Gate Valve               - V9, 192.168.0.19, 30019, SOCK19

TBD Gate Valve                          - V10, 192.168.0.20, 30020, SOCK20

TBD Loctn Gardeners Supply Gate Valve   - V11, 192.168.0.21, 30021, SOCK21

Stage Butts Group G6 Gate Valve         - V12, 192.168.0.22, 30022, SOCK22

Staff & Visitor GUI Pi                  - GUI, 192.168.0.9

Webserver Pi                            - WMT_Webserver, 192.168.0.1

Notes:

1.  Remote probes are monitored using the configuration too - the
master pi (sumppi) just reads the configuration for the other pis
to set this up. No extra configuration is needed.

2.  Any section of the configuration can be omitted if, for example,
there are no devices to control at a particular site (like the G4 site).
This is accepted and will "just work".

3.  The code to actually make decisions and decide what to do with
the devices to control is not here - it's in coretools.py.  At the
moment. only sumppi controls anything, so the method is called
do_control_logic(), but later on there will be methods for each site,
and they will be mapped to each site here in this config file.

4.  The Webserver Pi is not a part of the River System, but shares an
Ethernet network.  It has therefore been allocated an IP Address that
will not conflict with the system.  It is expected that it will serve
the Visitor & Staff GUI.

There are no classes or functions defined in this file.

.. module:: config.py
    :platform: Linux
    :synopsis: The configuration for the control software.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>
.. and Terry Coles <wmt@hadrian-way.co.uk>


"""

import os
import sys

#Define global variables.
VERSION = "0.11.0~pre3"
RELEASEDATE = "2/10/2019"

#Used to access the database connection object.
DBCONNECTION = None

#A strange approach, but it works and means we can import the modules for doc generation
#without error. It also doesn't relax the checks on our actual deployments.
if not "TESTING" in globals():
    #If running on a raspberry pi (architecture check), default to False,
    #unless the testing flag is present.
    if os.uname()[4][:3] == "arm" and \
        "-t" not in sys.argv and \
        "--testing" not in sys.argv:

        TESTING = False

    #Otherwise, default to True.
    else:
        TESTING = True

#Used to signal system shutdown to all the threads.
EXITING = False

import Tools
import Tools.deviceobjects

def reconfigure_logging():
    """
    Causes logging to be reconfigured for any modules imported before the logger was set up.
    """

    Tools.devicemanagement.reconfigure_logger()

SITE_SETTINGS = {

    #Settings for the SUMP site (master pi).
    "SUMP":
        {
            "ID": "SUMP",
            "Name": "Sump Pi",
            "Default Interval": 15,
            "IPAddress": "192.168.0.2",
            "HostingSockets": True,
            "ControlLogicFunction": "sumppi_control_logic",
            "DBUser": "test",
            "DBPasswd": "test",
            "DBHost": "192.168.1.114",
            "DBPort": 3306,

            #Local probes.
            "Probes":
                {

                    "SUMP:M0":
                    {
                        "Type":             "Hall Effect Probe",
                        "ID":               "SUMP:M0",
                        "Name":             "Sump Probe",
                        "Class":            Tools.deviceobjects.HallEffectProbe,
                        "HighLimits":       (0.07, 0.17, 0.35, 0.56, 0.73, 0.92, 1.22, 1.54, 2.1, 2.45),
                        "LowLimits":        (0.05, 0.15, 0.33, 0.53, 0.7, 0.88, 1.18, 1.5, 2, 2.4),
                        "Depths100s":       (0, 100, 200, 300, 400, 500, 600, 700, 800, 900),
                        "Depths25s":        (25, 125, 225, 325, 425, 525, 625, 725, 825, 925),
                        "Depths50s":        (50, 150, 250, 350, 450, 550, 650, 750, 850, 950),
                        "Depths75s":        (75, 175, 275, 375, 475, 575, 675, 775, 875, 975),
                    }
                },

            #Devices to control.
            "Devices":
                {

                    "SUMP:P0":
                    {
                        "Type":  "Motor",
                        "ID":    "SUMP:P0",
                        "Name":  "Sump to Butts Pump",
                        "Class": Tools.deviceobjects.Motor,
                        "Pins":  (5)
                    },

                    "SUMP:P1":
                    {
                        "Type": "Motor",
                        "ID":   "SUMP:P1",
                        "Name": "Sump Circulation Pump",
                        "Class": Tools.deviceobjects.Motor,
                        "Pins":  (18)
                    }
                },
        },

    #Settings for the G4 site (client pi at Wendy Street).
    "G4":
        {
            "ID": "G4",
            "Name": "Wendy Butts Pi",
            "Default Interval": 15,
            "IPAddress": "192.168.0.4",
            "HostingSockets": False,
            "DBUser": "test",
            "DBPasswd": "test",

            #Local probes.
            "Probes":
                {

                    "G4:M0":
                    {
                        "Type":             "Hall Effect Probe",
                        "ID":               "G4:M0",
                        "Name":             "Wendy Street Butts Probe",
                        "Class":            Tools.deviceobjects.HallEffectProbe,
                        "HighLimits":       (0.07, 0.17, 0.35, 0.56, 0.73, 0.92, 1.22, 1.54, 2.1, 2.45),
                        "LowLimits":        (0.05, 0.15, 0.33, 0.53, 0.7, 0.88, 1.18, 1.5, 2, 2.4),
                        "Depths100s":       (0, 100, 200, 300, 400, 500, 600, 700, 800, 900),
                        "Depths25s":        (25, 125, 225, 325, 425, 525, 625, 725, 825, 925),
                        "Depths50s":        (50, 150, 250, 350, 450, 550, 650, 750, 850, 950),
                        "Depths75s":        (75, 175, 275, 375, 475, 575, 675, 775, 875, 975),
                    },

                    "G4:FS0":
                    {
                        "Type": "Float Switch",
                        "ID":   "G4:FS0",
                        "Name": "Wendy Butts High Float Switch",
                        "Class": Tools.deviceobjects.FloatSwitch,
                        "Pins":  (8),
                    },

                    "G4:FS1":
                    {
                        "Type": "Float Switch",
                        "ID":   "G4:FS1",
                        "Name": "Wendy Butts Low Float Switch",
                        "Class": Tools.deviceobjects.FloatSwitch,
                        "Pins":  (7),
                    }
                },

            #Devices to control.
            "Devices": {},

            "ServerAddress": "192.168.0.2",
            "ServerPort": 30004,
            "ServerName": "SumpPi",
            "SocketName": "Wendy Street Buttspi Socket",
            "SocketID": "SOCK4"
        },

    #Settings for the G6 site (client pi behind the stage).
    "G6":
        {
            "ID": "G6",
            "Name": "Stage Butts Pi",
            "Default Interval": 15,
            "IPAddress": "192.168.0.6",
            "HostingSockets": False,
            "DBUser": "test",
            "DBPasswd": "test",

            #Local probes.
            "Probes":
                {

                    "G6:M0":
                    {
                        "Type":             "Hall Effect Probe",
                        "ID":               "G6:M0",
                        "Name":             "Stage Butts Probe",
                        "Class":            Tools.deviceobjects.HallEffectProbe,
                        "HighLimits":       (0.07, 0.17, 0.35, 0.56, 0.73, 0.92, 1.22, 1.54, 2.1, 2.45),
                        "LowLimits":        (0.05, 0.15, 0.33, 0.53, 0.7, 0.88, 1.18, 1.5, 2, 2.4),
                        "Depths100s":       (0, 100, 200, 300, 400, 500, 600, 700, 800, 900),
                        "Depths25s":        (25, 125, 225, 325, 425, 525, 625, 725, 825, 925),
                        "Depths50s":        (50, 150, 250, 350, 450, 550, 650, 750, 850, 950),
                        "Depths75s":        (75, 175, 275, 375, 475, 575, 675, 775, 875, 975),
                    },

                    "G6:FS0":
                    {
                        "Type": "Float Switch",
                        "ID":   "G6:FS0",
                        "Name": "Stage Butts High Float Switch",
                        "Class": Tools.deviceobjects.FloatSwitch,
                        "Pins":  (8),
                    },

                    "G6:FS1":
                    {
                        "Type": "Float Switch",
                        "ID":   "G6:FS1",
                        "Name": "Stage Butts Low Float Switch",
                        "Class": Tools.deviceobjects.FloatSwitch,
                        "Pins":  (7),
                    }
                },

            #Devices to control.
            "Devices": {},

            "ServerAddress": "192.168.0.2",
            "ServerPort": 30006,
            "ServerName": "SumpPi",
            "SocketName": "Wendy Street Stagepi Socket",
            "SocketID": "SOCK6"

        },

    #Gate Valves.
    "V4":
        {
            "Type": "Gate Valve",
            "ID":   "V4",
            "Name": "Wendy Butts Gate Valve Pi",
            "HostingSockets": False,
            "IPAddress": "192.168.0.14",
            "Default Interval": 15,
            "DBUser": "test",
            "DBPasswd": "test",

            "Name": "Butts Farm Gate Valve",
            "Class": Tools.deviceobjects.GateValve,

            "Pins":  (17, 27, 19),
            "posTolerance": 1,
            "maxOpen": 90,
            "minOpen": 1,
            "refVoltage": 3.3,

            #Config for server connection.
            "ServerAddress": "192.168.0.2",
            "ServerPort": 30014,
            "ServerName": "SumpPi",
            "SocketName": "Wendy Street Butts Gate Valve V4 Socket",
            "SocketID": "SOCK14",

        },

    "V6":
        {
            "Type": "Gate Valve",
            "ID":   "V6",
            "Name": "Stage Butts Gate Valve Pi",
            "HostingSockets": False,
            "IPAddress": "192.168.0.16",
            "Default Interval": 15,
            "DBUser": "test",
            "DBPasswd": "test",

            "Name": "Matrix Pump Gate Valve",
            "Class": Tools.deviceobjects.GateValve,

            "Pins":  (17, 27, 19),
            "posTolerance": 1,
            "maxOpen": 90,
            "minOpen": 1,
            "refVoltage": 3.3,

            #Config for server connection.
            "ServerAddress": "192.168.0.2",
            "ServerPort": 30016,
            "ServerName": "SumpPi",
            "SocketName": "Matrix Pump Gate Valve V6 Socket",
            "SocketID": "SOCK16",

        },

    "V7":
        {
            "Type": "Gate Valve",
            "ID":   "V7",
            "HostingSockets": False,
            "IPAddress": "192.168.0.17",
            "Default Interval": 15,
            "DBUser": "test",
            "DBPasswd": "test",

            "Name": "Matrix Pump Gate Valve",
            "Class": Tools.deviceobjects.GateValve,

            "Pins":  (17, 27, 19),
            "posTolerance": 1,
            "maxOpen": 90,
            "minOpen": 1,
            "refVoltage": 3.3,

            #Config for server connection.
            "ServerAddress": "192.168.0.2",
            "ServerPort": 30017,
            "ServerName": "SumpPi",
            "SocketName": "Matrix Pump Gate Valve V7 Socket",
            "SocketID": "SOCK17",

        },

    "V8":
        {
            "Type": "Gate Valve",
            "ID":   "V8",
            "HostingSockets": False,
            "IPAddress": "192.168.0.18",
            "Default Interval": 15,
            "DBUser": "test",
            "DBPasswd": "test",

            "Name": "Matrix Pump Gate Valve",
            "Class": Tools.deviceobjects.GateValve,

            "Pins":  (17, 27, 19),
            "posTolerance": 1,
            "maxOpen": 90,
            "minOpen": 1,
            "refVoltage": 3.3,

            #Config for server connection.
            "ServerAddress": "192.168.0.2",
            "ServerPort": 30018,
            "ServerName": "SumpPi",
            "SocketName": "Matrix Pump Gate Valve V4 Socket",
            "SocketID": "SOCK18",

        },

    "V9":
        {
            "Type": "Gate Valve",
            "ID":   "V9",
            "HostingSockets": False,
            "IPAddress": "192.168.0.19",
            "Default Interval": 15,
            "DBUser": "test",
            "DBPasswd": "test",

            "Name": "Matrix Pump Gate Valve",
            "Class": Tools.deviceobjects.GateValve,

            "Pins":  (17, 27, 19),
            "posTolerance": 1,
            "maxOpen": 90,
            "minOpen": 1,
            "refVoltage": 3.3,

            #Config for server connection.
            "ServerAddress": "192.168.0.2",
            "ServerPort": 30019,
            "ServerName": "SumpPi",
            "SocketName": "Matrix Pump Gate Valve V9 Socket",
            "SocketID": "SOCK19",

        },

    "V12":
        {
            "Type": "Gate Valve",
            "ID":   "V12",
            "HostingSockets": False,
            "IPAddress": "192.168.0.22",
            "Default Interval": 15,
            "DBUser": "test",
            "DBPasswd": "test",

            "Name": "Stage Butts Gate Valve",
            "Class": Tools.deviceobjects.GateValve,

            "Pins":  (17, 27, 19),
            "posTolerance": 1,
            "maxOpen": 90,
            "minOpen": 1,
            "refVoltage": 3.3,

            #Config for server connection.
            "ServerAddress": "192.168.0.2",
            "ServerPort": 30022,
            "ServerName": "SumpPi",
            "SocketName": "Stage Butts Gate Valve V12 Socket",
            "SocketID": "SOCK22",

        }
}
