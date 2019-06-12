#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Tools Package for the River System Control and Monitoring Software
# This file is part of the River System Control and Monitoring Software.
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

"""
This is the Tools package for the river control system software. It
forms the entirety of the framework for the program. There are four
modules in here:

coretools.py
============

This module contins classes and functions used at both the master pi end,
and the remote pis. More functions will likely be added here soon to
reduce code duplication.

Contains Functions:

- greet_user()
- get_and_handle_new_reading()
- do_control_logic()

Contains Classes:

- Reading - to represent readings from all probes.

monitortools.py
===============

This module contains the monitoring tools used in the rest of the
program. These take the form of classes that have methods executed
as threads. This approach was decided because it stops the main
program thread from blocking when taking readings, and allows us
to take readings from many probes at once without any resulting
delays/complexity. SocketsMonitor allows simple monitoring of probes
over a network.

Contains Classes:

- BaseMonitorClass
- Monitor
- SocketsMonitor

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
- HallEffectProbe2 (new magnetic levels probe)

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

.. module:: main.py
    :platform: Linux
    :synopsis: The main part of the control software.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>

"""

from __future__ import absolute_import

from . import coretools
from . import monitortools
from . import sockettools
from . import deviceobjects
