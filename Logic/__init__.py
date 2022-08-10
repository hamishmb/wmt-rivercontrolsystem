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

This module contains control logic functions and set-up functions that can be
referenced in the configuration. The functions in controllogic.py should be
kept as short as possible, importing lengthier code from the other modules.

sumppilogic.py
==============

This module contains control logic for Sump Pi, which is primarily responsible
for maintaining a suitable water level in the river sump, pumping water out of
the sump and into butts group G4 when the sump level is too high and pumping
water out of butts group G4 and into the sump when the sump level is too low.

.. note::
    The sump pi control logic is actually still in contrologic.py as the existing
    code would not suit being split. When it is re-written, it is likely it will
    go in its own file as described here.

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
