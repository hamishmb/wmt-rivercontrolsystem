#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Logging Tools for the River System Control and Monitoring Software
# Copyright (C) 2017-2022 Wimborne Model Town
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

#pylint: disable=logging-not-lazy
#
#Reason (logging-not-lazy): Harder to understand the logging statements that way.

"""
This is the loggingtools module, which contains tools used by the logger.
Currently, this a just a custom handler for the logger that will rotate
the log file every day, and re-create it if it disappears.

.. module:: loggingtools.py
    :platform: Linux
    :synopsis: Contains logging tools used by all parts of the software.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>
"""

import os
import logging
import logging.handlers

class CustomLoggingHandler(logging.handlers.TimedRotatingFileHandler):
    """
    This is a custom version of logging.handlers.TimedRotatingFileHandler that
    also creates new log files when the log file is moved/deleted.

    No constructor is defined here, because the superclass constructor works just
    fine for us.
    """

    def shouldRollover(self, record):
        """
        Determine if we should rotate the log file.

        The record argument is just here to keep the method signatures the same,
        which maintains compatibility.

        Returns:
            int.    0 - No need to roll over.
                    1 - We should roll over.
        """

        #Use the superclass to check whether midnight has passed since we created
        #the logfile.
        midnight_passed = logging.handlers.TimedRotatingFileHandler.shouldRollover(self,
                                                                                   record=None)

        #Stores whether we think we should roll over.
        file_unusable = 0

        #self.baseFilename holds the absolute path to the filename we specified
        #(defined in logging.FileHandler).
        if not os.path.isfile(self.baseFilename):
            file_unusable = 1

        #If either says to rotate, we will rotate.
        if midnight_passed == 1 or file_unusable == 1:
            return 1

        #Otherwise we won't.
        return 0
