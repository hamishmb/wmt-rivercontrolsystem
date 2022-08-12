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
This is the Logic package for the river control system software. It contains
the control logic.

contrologic.py contains control logic functions and set-up functions that can be
referenced in the configuration.

Additional modules have been used to separate code that is intended for a
specific control logic only.

controllogic.py
===============

This module contains control logic integration functions and set-up functions
that can be referenced in the configuration. The functions in controllogic.py
should be kept as short as possible, importing lengthier code from the other
modules.

valvelogic.py
==============

This module contains general control logic for the gate valves. This logic runs
on each individual gate valve, and keeps track of the state of the valve, as well
as the desired position, opening and closing the valve as needed, as well as other
management functions.

naslogic.py
==============

This module contains control logic for the NAS box, which is primarily responsible
for maintaining database consistency, keeping track of the system tick, and
monitoring the status of the NAS box hardware.

sumppilogic.py
==============

This module contains control logic for Sump Pi, which is primarily responsible
for maintaining a suitable water level in the river sump, pumping water out of
the sump and into butts group G4 when the sump level is too high and pumping
water out of butts group G4 and into the sump when the sump level is too low.

stagepilogic.py
===============

This module contains control logic for Stage Pi, which is primarily responsible
for keeping butts group G4 full of water whenever possible, using water from
butts group G6.

temptopuplogic.py
=================

This module contains interim measure "Temporary Top Up" control logic for
Lady Hanham Pi. It provides a daily mains water top up at a fixed time of day,
if the level in G1 is sufficiently low. The purpose of the logic is to alleviate
the burden of manually filling the system, prior to the introduction of the full
control logic for Lady Hanham Pi. It will be made obsolete upon introduction of
the full control logic.
"""
