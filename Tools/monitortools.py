#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Monitoring Tools for the River System Control and Monitoring Software Version 0.9.1
# Copyright (C) 2017 Wimborne Model Town
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

import time
import datetime
import threading

#TODO use deque and popleft.

# ---------- BASE CLASS ----------
class BaseMonitorClass(threading.Thread):
    def __init__(self, probe, num_readings, reading_interval):
        threading.Thread.__init__(self)
        self.probe = probe
        self.num_readings = num_readings
        self.reading_interval = reading_interval
        self.queue = []
        self.running = False
        self.should_exit = False

    def is_running(self):
        """
        Returns True if running, else False.
        Usage:
            bool is_running()
        """

        return self.running

    def has_data(self):
        """
        Returns True if the queue isn't empty, False if it is.
        Usage:
            bool has_data()
        """

        return int(len(self.queue))

    def get_reading(self):
        """
        Returns a reading from the queue, and deletes it from the queue.
        Usage:
            string get_reading()
        """

        return self.queue.pop()

    def set_reading_interval(self, interval):
        """
        Sets the reading interval. Takes immediate effect.
        Usage:
            set_reading_interval(int interval)
        """

        self.reading_interval = interval

    def request_exit(self, wait=False):
        """
        Used to ask the thread to exit. Doesn't wait before returning unless specified.
        Usage:
            request_exit([bool wait])
        """
        self.should_exit = True
        self.reading_interval = 0 #Helps thread to react faster.

        if wait:
            while self.running:
                time.sleep(5)

# ---------- Universal Monitor ----------
class Monitor(BaseMonitorClass):
    def __init__(self, Type, probe, num_readings, reading_interval):
        """Initialise and start the thread"""
        BaseMonitorClass.__init__(self, probe, num_readings, reading_interval)

        self.reading_func = probe.get_reading

        self.start()

    def run(self):
        """Main part of the thread"""
        num_readings_taken = 0
        self.running = True

        try:
            while ((not self.should_exit) and (self.num_readings == 0 or (num_readings_taken < self.num_readings))):
                the_reading, status_text = self.reading_func()

                self.queue.append("Time: "+str(datetime.datetime.now())+" the_reading: "+str(the_reading)+" Status: "+status_text)

                if self.num_readings != 0:
                    num_readings_taken += 1

                #Take readings every however often it is.
                #I know we could use a long time.sleep(),
                #but this MUST be responsive to changes in the reading interval.
                count = 0

                while count < self.reading_interval:
                    #This way, if our reading interval changes,
                    #the code will respond to the change immediately.
                    time.sleep(1)
                    count += 1

        except BaseException as err:
            #Ignore all errors. Generally bad practice :P
            print("\nCaught Exception: ", err)

        self.running = False

