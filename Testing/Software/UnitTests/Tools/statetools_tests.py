#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# State Tools Unit Tests for the River System Control and Monitoring Software
# Copyright (C) 2017-2019 Wimborne Model Town
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3 or,
# at your option, any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=too-few-public-methods
#
# Reason (too-few-public-methods): Test classes don't need many public members.

# NOTE: Class ControlStateABC does not require testing, because it is an
# abstract class. It should be tested through the testing of its
# concrete subclasses.

# NOTE: Class ControlStateMachineABC does not require testing, because
# it is an abstract class. It should be tested through the testing of
# its concrete subclasses.

# Rationale for not testing these Abstract Base Classes:
# 1. They are only for internal use within the River Control System, AND
# 2. They should always be used via a concrete subclass, AND
# 3. The concrete subclasses should always be fully tested
#
# Abstract classes are just implementation details of their subclasses.
#
# If there was an intention for the ABCs to be provided as a library/API for
# use outside of the River Control System project, then testing the ABCs
# would be necessary in order to avoid potentially delivering a broken
# interface to other projects.