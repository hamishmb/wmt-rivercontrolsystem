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

stagepilogic.py
===============

This module contains control logic for Stage Pi, which is primarily responsible
for keeping butts group G4 full of water whenever possible, using water from
butts group G6.
"""
