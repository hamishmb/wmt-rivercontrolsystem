#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Unit Tests for the River System Control and Monitoring Software
# Copyright (C) 2017-2020 Wimborne Model Town
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

"""
This file is used to start the test suites for river control system.
"""

#Import modules.
import unittest
import logging
import getopt
import sys
import os

sys.path.insert(0, os.path.abspath('../../../'))
sys.path.insert(0, os.path.abspath('../../'))

import config

#Set up the logger.
logger = logging.getLogger('River System Control Software')

#Log only critical message by default.
LOGGER_LEVEL = logging.CRITICAL

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
                    datefmt='%d/%m/%Y %I:%M:%S %p', level=LOGGER_LEVEL)

def usage():
    """
    This function is used to output help information to the standard output
    if the user passes invalid/incorrect commandline arguments.

    Usage:

    >>> usage()
    """

    print("\nUsage: unittests.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:                   Show this help message")
    print("       -D, --debug                   Enable debug mode")
    print("       -a, --all:                    Run all the tests. The default.")
    print("       -c, --coretools:              Run only the tests for the")
    print("                                     coretools module.")
    print("       -l, --logic:                  Run only the tests for the")
    print("                                     controllogic (integration)")
    print("                                     module.")
    print("       --stagepilogic:               Run only the tests for the")
    print("                                     stagepilogic module.")
    print("       -d, --deviceobjects:          Run only the tests for the")
    print("                                     deviceobjects module.")
    print("       -e, --devicemanagement:       Run only the tests for the")
    print("                                     devicemanagement module.")
    print("       -m, --monitortools:           Run only the tests for the")
    print("                                     monitortools module.")
    print("       -s, --sockettools:            Run only the tests for the")
    print("                                     sockettools module.")
    print("unittests.py is released under the GNU GPL Version 3")
    print("Version: "+config.VERSION+" ("+config.RELEASEDATE+")")
    print("Copyright (C) Wimborne Model Town 2017-2019")

if __name__ == "__main__":
    #Check all cmdline options are valid.
    try:
        OPTIONS, ARGUMENTS = getopt.getopt(sys.argv[1:], "hDcldemsa",
                                           ["help", "debug", "coretools", "logic", "stagepilogic",
                                            "deviceobjects", "devicemanagement", "monitortools",
                                            "sockettools", "all"])

    except getopt.GetoptError as err:
        #Invalid option. Show the help message and then exit.
        #Show the error.
        print(str(err))
        usage()
        sys.exit(2)

    #We have to handle options twice for this to work - a bit strange, but it works.
    #Handle debugging mode here.
    for o, a in OPTIONS:
        if o in ["-D", "--debug"]:
            LOGGER_LEVEL = logging.DEBUG

    logger.setLevel(LOGGER_LEVEL)

    #Import test modules here so the logging level is right - debug mode will work.
    from UnitTests.Tools import coretools_tests
    from UnitTests.Logic import controllogic_tests
    from UnitTests.Logic import stagepilogic_tests
    from UnitTests.Tools import deviceobjects_tests
    from UnitTests.Tools import devicemanagement_tests
    from UnitTests.Tools import monitortools_tests
    from UnitTests.Tools import sockettools_tests

    #Set up which tests to run based on options given.
    TEST_SUITES = [coretools_tests, controllogic_tests, stagepilogic_tests, deviceobjects_tests,
                   devicemanagement_tests, monitortools_tests, sockettools_tests]

    for o, a in OPTIONS:
        if o in ["-a", "--all"]:
            TEST_SUITES = [coretools_tests, controllogic_tests, stagepilogic_tests,
                           deviceobjects_tests, devicemanagement_tests, monitortools_tests,
                           sockettools_tests]

        elif o in ["-c", "--coretools"]:
            TEST_SUITES = [coretools_tests]

        elif o in ("-l", "--logic"):
            TEST_SUITES = [controllogic_tests]

        elif o in ("--stagepilogic"):
            TEST_SUITES = [stagepilogic_tests]

        elif o in ["-d", "--deviceobjects"]:
            TEST_SUITES = [deviceobjects_tests]

        elif o in ("-e", "--devicemanagement"):
            TEST_SUITES = [devicemanagement_tests]

        elif o in ["-m", "--monitortools"]:
            TEST_SUITES = [monitortools_tests]

        elif o in ["-s", "--sockettools"]:
            TEST_SUITES = [sockettools_tests]

        elif o in ["-h", "--help"]:
            usage()
            sys.exit()

        elif o in ["-D", "--debug"]:
            pass

        else:
            assert False, "unhandled option"

    for module in TEST_SUITES:
        print("\n\n---------------------------- Tests for "
              + str(module)+" ----------------------------\n\n")
        unittest.TextTestRunner(verbosity=2).run(unittest.TestLoader().loadTestsFromModule(module))
