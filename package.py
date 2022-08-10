#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# River System Control and Monitoring Software Packaging script
# Copyright (C) 2020-2022 Wimborne Model Town
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
This is a script to package the river control system framework in a tarball that is
suitable for use with the site-wide auto-updater. This will obtain the latest version
from the git repository, and requires the git, tar, and gzip commands to be available.

Full instructions for use are
available in the Installation Specification and/or User Guide.

.. module:: package.py
    :platform: Linux
    :synopsis: Packaging script for site-wide updater.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>

"""

import subprocess
import sys
import os
import shutil

#Fetch the code from the online repository.
cmd = subprocess.run(["git", "clone", "https://gitlab.com/wmtprojectsteam/rivercontrolsystem.git",
                      "master"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

stdout = cmd.stdout.decode("UTF-8", errors="ignore")

if cmd.returncode != 0:
    print("Error! Unable to download river system software. "
          + "Error was:\n"+stdout+"\n")
    sys.exit()

#Rename directory to "rivercontrolsystem".
cmd = subprocess.run(["mv", "-v", "master", "rivercontrolsystem"], stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, check=False)

stdout = cmd.stdout.decode("UTF-8", errors="ignore")

if cmd.returncode != 0:
    print("Error! Unable to prepare river control system software. "
          + "Error was:\n"+stdout+"\n")
    sys.exit()

#Save git revision into a special file inside.
os.chdir("./rivercontrolsystem")
cmd = subprocess.run("git log -1 > REVISION.txt", stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     shell=True, check=False)

os.chdir("../")

stdout = cmd.stdout.decode("UTF-8", errors="ignore")

if cmd.returncode != 0:
    print("Error! Unable to save revision number. "
          + "Error was:\n"+stdout+"\n")
    sys.exit()

#Create a tarball of the downloaded software.
cmd = subprocess.run(["tar", "-cvz", "rivercontrolsystem", "-f", "rivercontrolsystem.tar.gz"],
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

stdout = cmd.stdout.decode("UTF-8", errors="ignore")

if cmd.returncode != 0:
    print("Error! Unable to compress river control system software. "
          + "Error was:\n"+stdout+"\n")
    sys.exit()

#Clean up.
shutil.rmtree("./rivercontrolsystem")

print("Your compressed tarball is ready and available at: ./rivercontrolsystem.tar.gz")
