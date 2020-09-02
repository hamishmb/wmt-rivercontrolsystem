#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Configuration for the River System Control and Monitoring Software
# Copyright (C) 2017-2020 Wimborne Model Town
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

* Sump Pi                        - SUMP

   * Hall Effect (magnetic) Probe -     M0
   * Main circulation Pump        -     P1
   * Butts Return Pump            -     P0

* Wendy Street Pi                - G4

   * Hall Effect (magnetic) Probe -     M0
   * Float Switch                 -     FS0

* Gate Valve                     - VALVE4:V4

Full List of Devices and their ID Data, IP Addresses, (i2C Addresses) Pi server Port and
Socket Numbers where applicable:

* Sump Pi                                 - SUMP, 192.168.0.2

   * Hall Effect (magnetic) Probe          -     SUMP:M0 (0x48)
   * Main circulation Pump                 -     SUMP:P1
   * Butts Return Pump                     -     SUMP:P0

* Lady Hanham Butts Pi                   - G3, 192.168.0.3, 30003, SOCK3

   * Hall Effect (magnetic) Probe          -     G3:M0 (0x48)
   * Float Switch (High)                   -     G3:FS0
   * Float Switch (Low)                    -     G3:FS1

   * Hall Effect (magnetic) Probe          -     G3:M1 (0x49)
   * Float Switch (High)                   -     G3:FS2
   * Float Switch (Low)                    -     G3:FS3

   * Hall Effect (magnetic) Probe          -     G3:M1 (0x4B)
   * Float Switch (High)                   -     G3:FS4
   * Float Switch (Low)                    -     G3:FS5

   * Mains Water Solenoid Valve            -     G1:S0

* Wendy Street Butts Pi                     - G4, 192.168.0.4, 30004, SOCK4

   * Hall Effect (magnetic) Probe          -     G4:M0
   * Float Switch (High)                   -     G4:FS0
   * Float Switch (Low)                    -     G4:FS1

* Gazebo Butts Pi                           - G5, 192.168.0.5, 30005, SOCK5

   * Hall Effect (magnetic) Probe          -     G5:M0
   * Float Switch (High)                   -     G5:FS0
   * Float Switch (Low)                    -     G5:FS1

* Stage Butts Pi                            - G6, 192.168.0.6, 30006, SOCK6
   * Hall Effect (magnetic) Probe          -     G6:M0
   * Float Switch (High)                   -     G6:FS0
   * Float Switch (Low)                    -     G6:FS1

* Railway Room G1 Butts Group Gate Valve  - VALVE1:V1, 192.168.0.11, 30011, SOCK11
* Railway Room G2 Butts Group Gate Valve  - VALVE1:V2, 192.168.0.12, 30012, SOCK12
* Railway Room G3 Butts Group Gate Valve  - VALVE3:V3, 192.168.0.13, 30013, SOCK13

* Wendy Street G4 Butts Group Gate Valve  - VALVE4:V4, 192.168.0.14, 30014, SOCK14

* Gazebo G5 Butts Group Gate Valve        - VALVE5:V5, 192.168.0.15, 30015, SOCK15

* Matrix Pump V6 Gate Valve               - VALVE6:V6, 192.168.0.16, 30016, SOCK16
* Matrix Pump V7 Gate Valve               - VALVE7:V7, 192.168.0.17, 30017, SOCK17
* Matrix Pump V8 Gate Valve               - VALVE8:V8, 192.168.0.18, 30018, SOCK18
* Matrix Pump V9 Gate Valve               - VALVE9:V9, 192.168.0.19, 30019, SOCK19

* TBD Gate Valve                          - VALVE10:V10, 192.168.0.20, 30020, SOCK20
* TBD Loctn Gardeners Supply Gate Valve   - VALVE11:V11, 192.168.0.21, 30021, SOCK21

* Stage Butts Group G6 Gate Valve         - VALVE12:V12, 192.168.0.22, 30022, SOCK22

* Staff & Visitor GUI Pi                  - GUI, 192.168.0.9

* Webserver Pi                            - WMT_Webserver, 192.168.0.1

Notes:

1.  Remote probes are monitored using the configuration too - the control logic
for each pi uses the database to query readings for each probe it is interested in.

2.  Any section of the configuration can be empty, for example,
there are no devices to control at a particular site (like the G4 site).
This is accepted and will "just work".

3.  The code to actually make decisions and decide what to do with
the devices to control is not here - it's in coretools.py (and may
soon be moved elsewhere). These are the control logic functions.

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
VERSION = "0.11.0"
RELEASEDATE = "18/8/2020"

#System ID of this Pi.
SYSTEM_ID = None

#CPU LOAD and MEMORY USAGE (MB).
CPU = None
MEM = None

#Used to access the database connection object.
DBCONNECTION = None

#List of sockets objects.
SOCKETSLIST = []

#Current system tick.
TICK = 0

#A strange approach, but it works and means we can import the modules for doc generation
#without error. It also doesn't relax the checks on our actual deployments.
if not "TESTING" in globals():
    #If we are on the NAS box, default to True.
    if "NAS" in sys.argv:
        TESTING = True

    #If running on a raspberry pi (architecture check), default to False,
    #unless the testing flag is present.
    elif os.uname()[4][:3] in ("arm", "aar") and \
        "-t" not in sys.argv and \
        "--testing" not in sys.argv:

        TESTING = False

    #Otherwise, default to True.
    else:
        TESTING = True

#Used to signal software shutdown to all the threads.
EXITING = False

#Signals whether we are in debug mode.
DEBUG = False

#Used to signal pending shutdown, reboot, and update.
SHUTDOWN = False
SHUTDOWNALL = False
REBOOT = False
REBOOTALL = False
UPDATE = False

#NB: These are imported here because the above variables and the testing
#flag must be set up first to prevent issues.
import Tools #pylint: disable=wrong-import-position
import Tools.deviceobjects #pylint: disable=wrong-import-position

def reconfigure_logging():
    """
    Causes logging to be reconfigured for any modules imported before the logger was set up.
    """

    Tools.devicemanagement.reconfigure_logger()

SITE_SETTINGS = {

    #Settings for the NAS site.
    "NAS":
        {
            "ID": "NAS",
            "Name": "NAS Box",
            "Default Interval": 15,
            "IPAddress": "192.168.0.25",
            "HostingSockets": True,
            "ControlLogicFunction": "nas_control_logic",
            "DBUser": "nasbox",
            "DBPasswd": "river20",
            "DBHost": "127.0.0.1",
            "DBPort": 3306,

            #Local probes.
            "Probes":
                {},

            #Devices to control.
            "Devices": {},
        },

    #Settings for the SUMP site.
    "SUMP":
        {
            "Type": "Site",
            "ID": "SUMP",
            "Name": "Sump Pi",
            "Default Interval": 15,
            "IPAddress": "192.168.0.2",
            "HostingSockets": False,
            "ControlLogicFunction": "sumppi_control_logic",
            "DBUser": "sumppi",
            "DBPasswd": "river20",
            "DBHost": "192.168.0.25",
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
                        "ADCAddress":       0x48,
                        "HighLimits":       (0.11, 0.25, 0.44, 0.63, 0.805, 1.05, 1.36, 1.77, 2.25, 3.0),
                        "LowLimits":        (0.05, 0.111, 0.251, 0.441, 0.631, 0.806, 1.051, 1.361, 1.771, 2.251),
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

            "ServerAddress": "192.168.0.25",
            "ServerPort": 30002,
            "ServerName": "NAS",
            "SocketName": "Sumppi Socket",
            "SocketID": "SOCK2"

        },

    #Settings for the G3 site (client pi behind the Lady Hanham Building).
    "G3":
        {
            "Type": "Site",
            "ID": "G3",
            "Name": "Lady Hanham Butts Pi",
            "Default Interval": 15,
            "IPAddress": "192.168.0.3",
            "HostingSockets": False,
            "ControlLogicFunction": "generic_control_logic",
            "DBUser": "hanhampi",
            "DBPasswd": "river20",
            "DBHost": "192.168.0.25",
            "DBPort": 3306,

            #Local probes.
            "Probes":
                {

                    "G3:M0":
                    {
                        "Type":             "Hall Effect Probe",
                        "ID":               "G3:M0",
                        "Name":             "Lady Hanaham Butts Probe (G1 Butts Group)",
                        "Class":            Tools.deviceobjects.HallEffectProbe,
                        "ADCAddress":       0x48,
                        "HighLimits":       (0.11, 0.25, 0.44, 0.63, 0.805, 1.05, 1.36, 1.77, 2.25, 3.0),
                        "LowLimits":        (0.05, 0.111, 0.251, 0.441, 0.631, 0.806, 1.051, 1.361, 1.771, 2.251),
                        "Depths100s":       (0, 100, 200, 300, 400, 500, 600, 700, 800, 900),
                        "Depths25s":        (25, 125, 225, 325, 425, 525, 625, 725, 825, 925),
                        "Depths50s":        (50, 150, 250, 350, 450, 550, 650, 750, 850, 950),
                        "Depths75s":        (75, 175, 275, 375, 475, 575, 675, 775, 875, 975),
                    },

                    "G3:FS0":
                    {
                        "Type": "Float Switch",
                        "ID":   "G3:FS0",
                        "Name": "Lady Hanaham High Float Switch (G1 Butts Group)",
                        "Class": Tools.deviceobjects.FloatSwitch,
                        "Pins":  (8),
                    },

                    "G3:FS1":
                    {
                        "Type": "Float Switch",
                        "ID":   "G3:FS1",
                        "Name": "Lady Hanaham Low Float Switch (G1 Butts Group)",
                        "Class": Tools.deviceobjects.FloatSwitch,
                        "Pins":  (7),
                    },

                    "G3:M1":
                    {
                        "Type":             "Hall Effect Probe",
                        "ID":               "G3:M1",
                        "Name":             "Lady Hanaham Butts Probe (G2 Butts Group)",
                        "Class":            Tools.deviceobjects.HallEffectProbe,
                        "ADCAddress":       0x49,
                        "HighLimits":       (0.11, 0.25, 0.44, 0.63, 0.805, 1.05, 1.36, 1.77, 2.25, 3.0),
                        "LowLimits":        (0.05, 0.111, 0.251, 0.441, 0.631, 0.806, 1.051, 1.361, 1.771, 2.251),
                        "Depths100s":       (0, 100, 200, 300, 400, 500, 600, 700, 800, 900),
                        "Depths25s":        (25, 125, 225, 325, 425, 525, 625, 725, 825, 925),
                        "Depths50s":        (50, 150, 250, 350, 450, 550, 650, 750, 850, 950),
                        "Depths75s":        (75, 175, 275, 375, 475, 575, 675, 775, 875, 975),
                    },

                    "G3:FS2":
                    {
                        "Type": "Float Switch",
                        "ID":   "G3:FS2",
                        "Name": "Lady Hanaham High Float Switch (FS2 Butts Group)",
                        "Class": Tools.deviceobjects.FloatSwitch,
                        "Pins":  (20),
                    },

                    "G3:FS3":
                    {
                        "Type": "Float Switch",
                        "ID":   "G3:FS3",
                        "Name": "Lady Hanaham High Low Switch (FS3 Butts Group)",
                        "Class": Tools.deviceobjects.FloatSwitch,
                        "Pins":  (6),
                    },

                    "G3:M2":
                    {
                        "Type":             "Hall Effect Probe",
                        "ID":               "G3:M2",
                        "Name":             "Lady Hanaham Butts Probe (G3 Butts Group)",
                        "Class":            Tools.deviceobjects.HallEffectProbe,
                        "ADCAddress":       0x4B,
                        "HighLimits":       (0.11, 0.25, 0.44, 0.63, 0.805, 1.05, 1.36, 1.77, 2.25, 3.0),
                        "LowLimits":        (0.05, 0.111, 0.251, 0.441, 0.631, 0.806, 1.051, 1.361, 1.771, 2.251),
                        "Depths100s":       (0, 100, 200, 300, 400, 500, 600, 700, 800, 900),
                        "Depths25s":        (25, 125, 225, 325, 425, 525, 625, 725, 825, 925),
                        "Depths50s":        (50, 150, 250, 350, 450, 550, 650, 750, 850, 950),
                        "Depths75s":        (75, 175, 275, 375, 475, 575, 675, 775, 875, 975),
                    },

                    "G3:FS4":
                    {
                        "Type": "Float Switch",
                        "ID":   "G3:FS4",
                        "Name": "Lady Hanaham High Float Switch (FS4 Butts Group)",
                        "Class": Tools.deviceobjects.FloatSwitch,
                        "Pins":  (26),
                    },

                    "G3:FS5":
                    {
                        "Type": "Float Switch",
                        "ID":   "G3:FS5",
                        "Name": "Lady Hanaham Low Float Switch (FS5 Butts Group)",
                        "Class": Tools.deviceobjects.FloatSwitch,
                        "Pins":  (19),
                    }
                },

            #Devices to control.
            "Devices": {

                "G3:S0":
                {
                    "Type":  "Solenoid Valve",
                    "ID":    "G3:S1",
                    "Name":  "Mains Water Solenoid Valve (G1 Butts Group)",
                    "Class": Tools.deviceobjects.Motor,
                    "Pins":  (5)
                },


            },

            "ServerAddress": "192.168.0.25",
            "ServerPort": 30003,
            "ServerName": "NAS",
            "SocketName": "Lady Hanham Buttspi Socket",
            "SocketID": "SOCK3"
        },

    #Settings for the G4 site (client pi at Wendy Street).
    "G4":
        {
            "Type": "Site",
            "ID": "G4",
            "Name": "Wendy Butts Pi",
            "Default Interval": 15,
            "IPAddress": "192.168.0.4",
            "HostingSockets": False,
            "ControlLogicFunction": "generic_control_logic",
            "DBUser": "wbuttspi",
            "DBPasswd": "river20",
            "DBHost": "192.168.0.25",
            "DBPort": 3306,

            #Local probes.
            "Probes":
                {

                    "G4:M0":
                    {
                        "Type":             "Hall Effect Probe",
                        "ID":               "G4:M0",
                        "Name":             "Wendy Street Butts Probe",
                        "Class":            Tools.deviceobjects.HallEffectProbe,
                        "ADCAddress":       0x48,
                        "HighLimits":       (0.11, 0.25, 0.44, 0.63, 0.805, 1.05, 1.36, 1.77, 2.25, 3.0),
                        "LowLimits":        (0.05, 0.111, 0.251, 0.441, 0.631, 0.806, 1.051, 1.361, 1.771, 2.251),
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

            "ServerAddress": "192.168.0.25",
            "ServerPort": 30004,
            "ServerName": "NAS",
            "SocketName": "Wendy Street Buttspi Socket",
            "SocketID": "SOCK4"
        },

    #Settings for the G6 site (client pi behind the stage).
    "G6":
        {
            "Type": "Site",
            "ID": "G6",
            "Name": "Stage Butts Pi",
            "Default Interval": 15,
            "IPAddress": "192.168.0.6",
            "HostingSockets": False,
            "ControlLogicFunction": "stagepi_control_logic",
            "ControlLogicSetupFunction": "stagepi_control_logic_setup",
            "DBUser": "sbuttspi",
            "DBPasswd": "river20",
            "DBHost": "192.168.0.25",
            "DBPort": 3306,

            #Local probes.
            "Probes":
                {

                    "G6:M0":
                    {
                        "Type":             "Hall Effect Probe",
                        "ID":               "G6:M0",
                        "Name":             "Stage Butts Probe",
                        "Class":            Tools.deviceobjects.HallEffectProbe,
                        "ADCAddress":       0x48,
                        "HighLimits":       (0.11, 0.25, 0.44, 0.63, 0.805, 1.05, 1.36, 1.77, 2.25, 3.0),
                        "LowLimits":        (0.05, 0.111, 0.251, 0.441, 0.631, 0.806, 1.051, 1.361, 1.771, 2.251),
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

            "ServerAddress": "192.168.0.25",
            "ServerPort": 30006,
            "ServerName": "NAS",
            "SocketName": "Wendy Street Stagepi Socket",
            "SocketID": "SOCK6"

        },

    #Gate Valves.
    "VALVE1":
        {
            "ID":   "VALVE1",
            "Name": "Gate Valve V1 Pi",
            "Default Interval": 15,
            "IPAddress": "192.168.0.11",
            "HostingSockets": False,
            "ControlLogicFunction": "valve_control_logic",
            "DBUser": "valve1",
            "DBPasswd": "river20",
            "DBHost": "192.168.0.25",
            "DBPort": 3306,

            #Here for compatibility reasons.
            "Probes": {},

            #Devices to control.
            "Devices":
                {
                    "VALVE1:V1":
                        {
                            "Type": "Gate Valve",
                            "ID": "VALVE1:V1",
                            "Name": "Gate Valve V1",
                            "Class": Tools.deviceobjects.GateValve,
                            "ADCAddress": 0x48,

                            "Pins":  (17, 27, 19),
                            "posTolerance": 1,
                            "maxOpen": 90,
                            "minOpen": 1,
                            "refVoltage": 3.3,
                        },
                },

            #Config for server connection.
            "ServerAddress": "192.168.0.25",
            "ServerPort": 30011,
            "ServerName": "NAS",
            "SocketName": "Gate Valve V1 Socket",
            "SocketID": "SOCK11",

        },

    "VALVE2":
        {
            "ID":   "VALVE2",
            "Name": "Gate Valve V2 Pi",
            "Default Interval": 15,
            "IPAddress": "192.168.0.12",
            "HostingSockets": False,
            "ControlLogicFunction": "valve_control_logic",
            "DBUser": "valve2",
            "DBPasswd": "river20",
            "DBHost": "192.168.0.25",
            "DBPort": 3306,

            #Here for compatibility reasons.
            "Probes": {},

            #Devices to control.
            "Devices":
                {
                    "VALVE2:V2":
                        {
                            "Type": "Gate Valve",
                            "ID": "VALVE2:V2",
                            "Name": "Gate Valve V2",
                            "Class": Tools.deviceobjects.GateValve,
                            "ADCAddress": 0x48,

                            "Pins":  (17, 27, 19),
                            "posTolerance": 1,
                            "maxOpen": 90,
                            "minOpen": 1,
                            "refVoltage": 3.3,
                        },
                },

            #Config for server connection.
            "ServerAddress": "192.168.0.25",
            "ServerPort": 30012,
            "ServerName": "NAS",
            "SocketName": "Gate Valve V2 Socket",
            "SocketID": "SOCK12",

        },

    "VALVE3":
        {
            "ID":   "VALVE3",
            "Name": "Gate Valve V3 Pi",
            "Default Interval": 15,
            "IPAddress": "192.168.0.13",
            "HostingSockets": False,
            "ControlLogicFunction": "valve_control_logic",
            "DBUser": "valve3",
            "DBPasswd": "river20",
            "DBHost": "192.168.0.25",
            "DBPort": 3306,

            #Here for compatibility reasons.
            "Probes": {},

            #Devices to control.
            "Devices":
                {
                    "VALVE3:V3":
                        {
                            "Type": "Gate Valve",
                            "ID": "VALVE3:V3",
                            "Name": "Gate Valve V3",
                            "Class": Tools.deviceobjects.GateValve,
                            "ADCAddress": 0x48,

                            "Pins":  (17, 27, 19),
                            "posTolerance": 1,
                            "maxOpen": 90,
                            "minOpen": 1,
                            "refVoltage": 3.3,
                        },
                },

            #Config for server connection.
            "ServerAddress": "192.168.0.25",
            "ServerPort": 30013,
            "ServerName": "NAS",
            "SocketName": "Gate Valve V3 Socket",
            "SocketID": "SOCK13",

        },

    "VALVE4":
        {
            "ID":   "VALVE4",
            "Name": "Gate Valve V4 Pi",
            "Default Interval": 15,
            "IPAddress": "192.168.0.14",
            "HostingSockets": False,
            "ControlLogicFunction": "valve_control_logic",
            "DBUser": "valve4",
            "DBPasswd": "river20",
            "DBHost": "192.168.0.25",
            "DBPort": 3306,

            #Here for compatibility reasons.
            "Probes": {},

            #Devices to control.
            "Devices":
                {
                    "VALVE4:V4":
                        {
                            "Type": "Gate Valve",
                            "ID": "VALVE4:V4",
                            "Name": "Gate Valve V4",
                            "Class": Tools.deviceobjects.GateValve,
                            "ADCAddress": 0x48,

                            "Pins":  (17, 27, 19),
                            "posTolerance": 1,
                            "maxOpen": 90,
                            "minOpen": 1,
                            "refVoltage": 3.3,
                        },
                },

            #Config for server connection.
            "ServerAddress": "192.168.0.25",
            "ServerPort": 30014,
            "ServerName": "NAS",
            "SocketName": "Wendy Street Butts Gate Valve V4 Socket",
            "SocketID": "SOCK14",

        },

#    "VALVE6":
#        {
#            "ID":   "VALVE6",
#            "Name": "Gate Valve V6 Pi",
#            "Default Interval": 15,
#            "IPAddress": "192.168.0.16",
#            "HostingSockets": False,
#            "ControlLogicFunction": "valve_control_logic",
#            "DBUser": "valve6",
#            "DBPasswd": "river20",
#            "DBHost": "192.168.0.25",
#            "DBPort": 3306,
#
#            #Here for compatibility reasons.
#            "Probes": {},
#
#            #Devices to control.
#            "Devices":
#                {
#                    "VALVE6:V6":
#                        {
#                            "Type": "Gate Valve",
#                            "ID": "VALVE6:V6",
#                            "Name": "Gate Valve V6",
#                            "Class": Tools.deviceobjects.GateValve,
#                            "ADCAddress": 0x48,
#
#                            "Pins":  (17, 27, 19),
#                            "posTolerance": 1,
#                            "maxOpen": 90,
#                            "minOpen": 1,
#                            "refVoltage": 3.3,
#                        },
#                },
#
#            #Config for server connection.
#            "ServerAddress": "192.168.0.25",
#            "ServerPort": 30016,
#            "ServerName": "NAS",
#            "SocketName": "Matrix Pump Gate Valve V6 Socket",
#            "SocketID": "SOCK16",
#
#        },

#    "VALVE7":
#        {
#            "ID":   "VALVE7",
#            "Name": "Gate Valve V7 Pi",
#            "Default Interval": 15,
#            "IPAddress": "192.168.0.17",
#            "HostingSockets": False,
#            "ControlLogicFunction": "valve_control_logic",
#            "DBUser": "valve7",
#            "DBPasswd": "river20",
#            "DBHost": "192.168.0.25",
#            "DBPort": 3306,
#
#            #Here for compatibility reasons.
#            "Probes": {},
#
#            #Devices to control.
#            "Devices":
#                {
#                    "VALVE7:V7":
#                        {
#                            "Type": "Gate Valve",
#                            "ID": "VALVE7:V7",
#                            "Name": "Gate Valve V7",
#                            "Class": Tools.deviceobjects.GateValve,
#                            "ADCAddress": 0x48,
#
#                            "Pins":  (17, 27, 19),
#                            "posTolerance": 1,
#                            "maxOpen": 90,
#                            "minOpen": 1,
#                            "refVoltage": 3.3,
#                        },
#                },
#
#            #Config for server connection.
#            "ServerAddress": "192.168.0.25",
#            "ServerPort": 30017,
#            "ServerName": "NAS",
#            "SocketName": "Matrix Pump Gate Valve V7 Socket",
#            "SocketID": "SOCK17",
#
#        },

#    "VALVE8":
#        {
#            "ID":   "VALVE8",
#            "Name": "Gate Valve V8 Pi",
#            "Default Interval": 15,
#            "IPAddress": "192.168.0.18",
#            "HostingSockets": False,
#            "ControlLogicFunction": "valve_control_logic",
#            "DBUser": "valve8",
#            "DBPasswd": "river20",
#            "DBHost": "192.168.0.25",
#            "DBPort": 3306,
#
#            #Here for compatibility reasons.
#            "Probes": {},
#
#            #Devices to control.
#            "Devices":
#                {
#                    "VALVE8:V8":
#                        {
#                            "Type": "Gate Valve",
#                            "ID": "VALVE8:V8",
#                            "Name": "Gate Valve V8",
#                            "Class": Tools.deviceobjects.GateValve,
#                            "ADCAddress": 0x48,
#
#                            "Pins":  (17, 27, 19),
#                            "posTolerance": 1,
#                            "maxOpen": 90,
#                            "minOpen": 1,
#                            "refVoltage": 3.3,
#                        },
#                },
#
#            #Config for server connection.
#            "ServerAddress": "192.168.0.25",
#            "ServerPort": 30018,
#            "ServerName": "NAS",
#            "SocketName": "Matrix Pump Gate Valve V8 Socket",
#            "SocketID": "SOCK18",
#
#        },

#    "VALVE9":
#        {
#            "ID":   "VALVE9",
#            "Name": "Gate Valve V9 Pi",
#            "Default Interval": 15,
#            "IPAddress": "192.168.0.19",
#            "HostingSockets": False,
#            "ControlLogicFunction": "valve_control_logic",
#            "DBUser": "valve9",
#            "DBPasswd": "river20",
#            "DBHost": "192.168.0.25",
#            "DBPort": 3306,
#
#            #Here for compatibility reasons.
#            "Probes": {},
#
#            #Devices to control.
#            "Devices":
#                {
#                    "VALVE9:V9":
#                        {
#                            "Type": "Gate Valve",
#                            "ID": "VALVE9:V9",
#                            "Name": "Gate Valve V9",
#                            "Class": Tools.deviceobjects.GateValve,
#                            "ADCAddress": 0x48,
#
#                            "Pins":  (17, 27, 19),
#                            "posTolerance": 1,
#                            "maxOpen": 90,
#                            "minOpen": 1,
#                            "refVoltage": 3.3,
#                        },
#                },
#
#            #Config for server connection.
#            "ServerAddress": "192.168.0.25",
#            "ServerPort": 30019,
#            "ServerName": "NAS",
#            "SocketName": "Matrix Pump Gate Valve V9 Socket",
#            "SocketID": "SOCK19",
#
#        },

#    "VALVE12":
#        {
#            "ID":   "VALVE8",
#            "Name": "Gate Valve V12 Pi",
#            "Default Interval": 15,
#            "IPAddress": "192.168.0.22",
#            "HostingSockets": False,
#            "ControlLogicFunction": "valve_control_logic",
#            "DBUser": "valve12",
#            "DBPasswd": "river20",
#            "DBHost": "192.168.0.25",
#            "DBPort": 3306,
#
#            #Here for compatibility reasons.
#            "Probes": {},
#
#            #Devices to control.
#            "Devices":
#                {
#                    "VALVE12:V12":
#                        {
#                            "Type": "Gate Valve",
#                            "ID": "VALVE12:V12",
#                            "Name": "Gate Valve V12",
#                            "Class": Tools.deviceobjects.GateValve,
#                            "ADCAddress": 0x48,
#
#                            "Pins":  (17, 27, 19),
#                            "posTolerance": 1,
#                            "maxOpen": 90,
#                            "minOpen": 1,
#                            "refVoltage": 3.3,
#                        },
#                },
#
#            #Config for server connection.
#            "ServerAddress": "192.168.0.25",
#            "ServerPort": 30022,
#            "ServerName": "NAS",
#            "SocketName": "Stage Butts Gate Valve V12 Socket",
#            "SocketID": "SOCK22",
#
#        },

}
