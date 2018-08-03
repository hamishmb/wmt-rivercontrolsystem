#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Universal Standalone Monitor Config for the River System Control
# and Monitoring Software Version 0.9.2
# Copyright (C) 2017-2018 Wimborne Model Town
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
This is the configuration for all pis. These dictionaries
(key-value base data) provide all the configuration for each
site in a centralised, easy-to-change file.

This takes the form of a dictionary object
named "SITE_SETTINGS". This object has detailed configuration
for each site, namely the ID, sockets to host (if any), (local)
probes to monitor, and devices to control.

NB: Remote probes are monitored using the configuraation too -
the master pi (sumppi) just reads the configuraation for the
other pis to set this up. No extra configuration is needed.

NB 2: Any section of the configuration can be omitted if, for
example, there are no devices to control at a particular site
(like the G4 site). This is accepted and will "just work".

NB 3: The code to actually make decisions and decide what to do
with the devices to control is not here - it's in coretools.py.
At the moment. only sumppi controls anything, so the method is called
do_control_logic(), but later on there will be methods for each site,
and they will be mapped to each site here in this config file.

There are no classes or functions defined in this file.

.. module:: config.py
    :platform: Linux
    :synopsis: The configuration for the control software.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>

"""

import Tools

SITE_SETTINGS = {

    #Settings for the SUMP site (master pi).
    "SUMP":
        {
            "ID": "SUMP",

            #Sockets to host.
            "Sockets":
                {

                    #For connection to butts pi.
                    "Buttspi Socket":
                        {
                            "ID":           "SOCK0",
                            "Name":         "Buttspi Socket",
                            "PortNumber":   30000
                        }
                },

            #Local probes.
            "Probes":
                {

                    "SUMP:M0":
                    {
                        "Type":             "Hall Effect Probe",
                        "ID":               "SUMP:M0",
                        "Name":             "Sump Probe",
                        "Class":            Tools.sensorobjects.HallEffectProbe,
                        "Pins":             (15, 17, 27, 22, 23, 24, 10, 9, 25, 11),
                        "Default Interval": 10
                    }
                },

            #Devices to control.
            "Devices":
                {

                    "SUMP:P0":
                    {
                        "Type":  "Motor",
                        "ID":    "SUMP:P0",
                        "Name":  "Butts Pump",
                        "Class": Tools.sensorobjects.Motor,
                        "Pins":  (5)
                    },

                    "SUMP:P1":
                    {
                        "Type": "Motor",
                        "ID":   "SUMP:P1",
                        "Name": "Circulation Pump",
                        "Class": Tools.sensorobjects.Motor,
                        "Pins":  (18)
                    }
                },
        },

    #Settings for the G4 site (client pi at Wendy Street).
    "G4":
        {
            "ID": "G4",

            #Local probes.
            "Probes":
                {

                    "G4:M0":
                    {
                        "Type": "Hall Effect Probe",
                        "ID":   "G4:M0",
                        "Name": "Butts Probe",
                        "Class": Tools.sensorobjects.HallEffectProbe,
                        "Pins":  (15, 17, 27, 22, 23, 24, 10, 9, 25, 11),
                        "Default Interval": 10
                    },

                    "G4:FS0":
                    {
                        "Type": "Float Switch",
                        "ID":   "G4:FS0",
                        "Name": "Butts Switch",
                        "Class": Tools.sensorobjects.FloatSwitch,
                        "Pins":  (8),
                        "Default Interval": 30
                    }
                },

            "ServerAddress": "192.168.0.2",
            "ServerPort": 30000
        }

}
