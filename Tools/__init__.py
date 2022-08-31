#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Tools Package for the River System Control and Monitoring Software
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

"""
This is the Tools package for the river control system software. It
forms the entirety of the framework for the program. There are four
modules in here:

coretools.py
============

This module contains classes and functions used in various parts of the rest of the
framework.

Contains Classes:

- Reading - to represent readings from all probes/devices.

dbtools.py
==========

This module contains database-related functionality.

Contains Classes:

- DatabaseConnection - to communicate with the database on the NAS box.

loggingtools.py
===============

This module contains a custom handler for Python 3's logging module. The custom
handler rotates log files every night at midnight and re-creates log files if they
are moved or deleted.

logiccoretools.py
=================

This module contains code to interface between the control logic and the DatabaseConnection
class in coretools. This is to provide a stable API in case the DatabaseConnection class
needs to be modified at a later date. Currently, all the functions in here do is call
the corresponding method in the DatabaseConnection class with the same name.

monitortools.py
===============

This module contains the monitoring tools used in the rest of the
program. These take the form of classes that have methods executed
as threads. This approach was decided because it stops the main
program thread from blocking when taking readings, and allows us
to take readings from many probes at once without any noticeable resulting
delays/complexity. SocketsMonitor allows simple monitoring of probes
over a network.

Contains Classes:

- BaseMonitorClass
- Monitor
- SocketsMonitor (not currently in use by framework)

deviceobjects.py
================

This module contains all of the classes that are used to represent controls, 
probes and other devices in the rest of the program. These classes
all inherit from a common base device class that has useful methods
and attributes. Each individual class implements its own reading
mechanism, and has several other public methods if needed.

They also each have some private methods. As these are part of
the implementation, and are subject to change or disappear, they
are not documented here.

Contains Classes:

- BaseDeviceClass
- Motor
- FloatSwitch
- CapacitiveProbe
- ResistanceProbe
- HallEffectDevice (for water-wheels)
- HallEffectProbe (magnetic levels probe)

sockettools.py
==============

This module contains all of the classes and functionality needed for
network communications (using sockets). This consists of a Sockets class,
which is a high-level abstraction of the Python 3.x socket module,
designed to make network communications easy, fast, simple and reliable.

There's also a SocketHandlerThread class, and one of these is started as
a thread each time a socket is created. This class handles connection,
disconnection, input/output, and communication faults/errors for its
assigned Socket object. This keeps everything simple for the user of
the Sockets class.

Contains Classes:

- Sockets
- SocketHandlerThread

testingtools.py
===============

This module defines some testing classes and functions that simulate hardware, in order for the
control software to be run more easily in test deployments without real hardware, such as
in virtual machines.

statetools.py
=============

This module contains Abstract Base Classes for writing control logic based
on The State Pattern.

ControlStateMachineABC defines the basis for a state machine object which
has a number of different control states. The machine should initialise
itself by loading in a set of state objects that it will use. It remembers
the current state and gives the current state responsibility for handling
the 'doLogic' method.

ControlStateABC defines the basis of a control state object for use in a
control state machine. States have the responsibility for handling doLogic
while they are the current state, and for transitioning the machine into
a different state under some set of defined conditions.

Contains Classes:

- ControlStateABC
- ControlStateMachineABC
"""
