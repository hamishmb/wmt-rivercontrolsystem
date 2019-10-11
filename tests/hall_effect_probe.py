#!/usr/bin/env python3
# hall_effect_probe2.py - V04: 
#                Wimborne Model Town
#      River System New Type Magnetic Probe Test Functions
#
#  **********************************************************************
# This program carries out the following functions by:
#      a.  Measuring the voltage obtained from the slider on the Actuator Valve.
#      b.  Carrying out compensation arithmetic on the measured value.
#      c.  Using the result to determine the Depth that the magnet is at; move
#          the magnet up and down the tube to various positions and observer the 
#          reported depth.
#
# Copyright (c) 2019 Wimborne Model Town http://www.wimborne-modeltown.com/
#
#    This code is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Scheduler.py is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    with this software.  If not, see <http://www.gnu.org/licenses/>.
#
#  ***********************************************************************import time

import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
try:
    ads = ADS.ADS1115(i2c)
except OSError:
    print(" OSError. No ADS Device.")
except ValueError:
    print(" ValueError. No I2C Device.  Exiting...")
    exit(0)

# Create four single-ended inputs on channels 0 to 3
try:
    chan0 = AnalogIn(ads, ADS.P0)
    chan1 = AnalogIn(ads, ADS.P1)
    chan2 = AnalogIn(ads, ADS.P2)
    chan3 = AnalogIn(ads, ADS.P3)
except OSError:
    print(" OSError. A/D Channel(s) missing.")

high_limit = [0.07,0.17,0.35,0.56,0.73,0.92,1.22,1.54,2.1,2.45]
low_limit = [0.05,0.15,0.33,0.53,0.7,0.88,1.18,1.5,2,2.4]

depth = ([0,100,200,300,400,500,600,700,800,900],
         [25,125,225,325,425,525,625,725,825,925],
         [50,150,250,350,450,550,650,750,850,950],
         [75,175,275,375,475,575,675,775,875,975])

length = len(depth[0])

fh = open("results.txt","a")

def measure_probe_voltages():
    # Initialise Lists and variables to hold the working values in each column
    Vmeas = [0.0,0.0,0.0,0.0]                                      # Actual voltages
    Vcomp = [0.0,0.0,0.0,0.0]                                      # Compensated values
    result =[0.0,0]                                                # Measured value and column

    # Measure the voltage in each chain
    try:
        Vmeas[0] = chan0.voltage
        Vmeas[1] = chan1.voltage
        Vmeas[2] = chan2.voltage
        Vmeas[3] = chan3.voltage
    except OSError:
        print(" OSError. ADS Channel(s) not responding.")

    # Find the minimum value
    Vmin = min(Vmeas)

    # Find the column that the minimum value is in
    min_column = Vmeas.index(min(Vmeas))
    print("Column containing the minimum value = " + str(min_column))
        
    # Work out the average of the three highest measurements (thus ignoring the 'dipped' channel.
    Vtot = Vmeas[0] + Vmeas[1] + Vmeas[2] + Vmeas[3]
    Vav = (Vtot - Vmin)/3

    # Calculate the compensated value for each channel. 
    if Vmin >= 3.0:                                          # Take a shortcut when the magnet is between sensors
        Vcomp[0] = Vcomp[1] = Vcomp[2] = Vcomp[3] = Vav - Vmin
    else:
        if min_column == 0:
            Vcomp[min_column] = Vav - Vmin
        elif min_column == 1:
            Vcomp[min_column] = Vav - Vmin
        elif min_column == 2:
            Vcomp[min_column] = Vav - Vmin
        elif min_column == 3:
            Vcomp[min_column] = Vav - Vmin
        else:
            Vcomp[min_column] = Vav

    print("Dip Value = " + str(Vcomp[min_column]))

    result = Vcomp,min_column

    return result

def test_levels():
    count = 0
    level = 1000                                              # Value to return

    while count < length:
        print("")
        print("Count Number = " + str(count))

        Vcomp, min_column = measure_probe_voltages()

        # Now test the channel with the dip to see if any of the sensors are triggered
        if ((Vcomp[min_column] <= high_limit[count]) and (Vcomp[min_column] >= low_limit[count])):
            level = depth[min_column][count]
            print ("Depth = " + str(level))
        elif level == 1000:
            print("Between Sensors at this Depth")

        count += 1
        time.sleep(2)

    return level

def loop():
    while True:
        depth = test_levels()
        if depth == 1000:
            print("No Sensors Triggered")
        else:
            print("Depth = " + str(depth))
  
try:
    loop()

except KeyboardInterrupt:
    fh.close()
