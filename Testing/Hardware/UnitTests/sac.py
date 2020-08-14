#!/usr/bin/env python3
# SAC.py - V05: 
#                Wimborne Model Town
#      River System Sensor and Control Assy Test Functions
#
#  **********************************************************************
# This program carries out the following functions on all SACs by:
#    1.  Checking the Hall Effect Probe functions by:
#      a.  Measuring the voltage obtained from each column in each Hall Effect Probe
#          (one for the standard SAC and three for the Lady Hanham SAC).
#      b.  Carrying out compensation arithmetic on the measured value.
#      c.  Using the result to determine the Depth that the magnet is at; move
#          the magnet up and down the tube to various positions and observer the 
#          reported depth.
#    2.  Checking the Solid State Relay function by switching a 12 V voltage to the 
#        relevant outputs.
#    3.  Checking the Float Switch functions by detecting a short applied to the 
#        relevant inputs.
#    4.  For the Lady Hanham Butts Pi only, by by switching a 12 V high currnt
#        voltage to the relevant output.
#
# Copyright (c) 2020 Wimborne Model Town http://www.wimborne-modeltown.com/
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
#  ***********************************************************************

import RPi.GPIO as GPIO
from time import sleep
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Create the global vars for use by the Float Switch, SSR and Solenoid tests
EmptyFloatSwitchPin = 7                     # Standard SAC
FullFloatSwitchPin = 8                      # Standard SAC

G2_EmptyFloatSwitchPin = 6                  # Lady Hanham SAC only
G2_FullFloatSwitchPin = 20                  # Lady Hanham SAC only

G3_EmptyFloatSwitchPin = 19                 # Lady Hanham SAC only
G3_FullFloatSwitchPin = 26                  # Lady Hanham SAC only

ButtsPin = 5
SumpPin = 18

SolPin = 5

# Initialise GPIO pins
GPIO.setmode(GPIO.BCM)                      # Number GPIOs by Broadcom Numbers

GPIO.setup(ButtsPin, GPIO.OUT)              # Set ButtsPin's mode is output
GPIO.setup(SumpPin, GPIO.OUT)               # Set SumpPin's mode is output)
GPIO.output(ButtsPin, GPIO.HIGH)            # Set both pins high (0 V across a pulled-up
GPIO.output(SumpPin, GPIO.HIGH)             # open-collector output)

GPIO.setup(FullFloatSwitchPin, GPIO.IN)     # Set Butts Group Full Float Switch Pin's mode as input)
GPIO.setup(EmptyFloatSwitchPin, GPIO.IN)    # Set Butts Group Empty Float Switch Pin's mode as input)
GPIO.setup(G2_FullFloatSwitchPin, GPIO.IN)     # Set Butts Group Full Float Switch Pin's mode as input)
GPIO.setup(G2_EmptyFloatSwitchPin, GPIO.IN)    # Set Butts Group Empty Float Switch Pin's mode as input)
GPIO.setup(G3_FullFloatSwitchPin, GPIO.IN)     # Set Butts Group Full Float Switch Pin's mode as input)
GPIO.setup(G3_EmptyFloatSwitchPin, GPIO.IN)    # Set Butts Group Empty Float Switch Pin's mode as input)

GPIO.setup(SolPin, GPIO.OUT)                # Set SolPin's mode is output
GPIO.output(SolPin, GPIO.LOW)               # Set pin low (0 V across MOSFET gate)

# Create global vars for use by Hall Effect measurements
fh = open("results.txt","a")

high_limit = [0.07,0.17,0.35,0.56,0.73,0.92,1.22,1.54,2.1,2.45]
low_limit = [0.05,0.15,0.33,0.53,0.7,0.88,1.18,1.5,2,2.4]

depth = ([0,100,200,300,400,500,600,700,800,900],
         [25,125,225,325,425,525,625,725,825,925],
         [50,150,250,350,450,550,650,750,850,950],
         [75,175,275,375,475,575,675,775,875,975])

length = len(depth[0])

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

def setup_adc(addr):
    # Create the ADC object using the I2C bus
    try:
        ads = ADS.ADS1115(i2c, address=addr)
    except OSError:
        print(" OSError. No ADS Device.")
    except ValueError:
        print(" ValueError. No I2C Device.  Exiting...")
        exit(0)
        
    # Create four single-ended inputs on channels 0 to 3
    chan = [0,0,0,0]
    
    try:
        chan[0] = AnalogIn(ads, ADS.P0)
        chan[1] = AnalogIn(ads, ADS.P1)
        chan[2] = AnalogIn(ads, ADS.P2)
        chan[3] = AnalogIn(ads, ADS.P3)
    except OSError:
        print(" OSError. A/D Channel(s) missing.")
    
    return chan

def measure_probe_voltages(chan):
    # Initialise Lists and variables to hold the working values in each column
    Vmeas = [0.0,0.0,0.0,0.0]                                      # Actual voltages
    Vcomp = [0.0,0.0,0.0,0.0]                                      # Compensated values
    result =[0.0,0]                                                # Measured value and column

    # Measure the voltage in each chain
    try:
        Vmeas[0] = chan[0].voltage
        Vmeas[1] = chan[1].voltage
        Vmeas[2] = chan[2].voltage
        Vmeas[3] = chan[3].voltage
    except OSError:
        print(" OSError. ADS Channel(s) not responding.")

    # Find the minimum value
    Vmin = min(Vmeas)

    # Find the column that the minimum value is in
    min_column = Vmeas.index(min(Vmeas))
        
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

    result = Vcomp,min_column
    
    return result

def test_levels(chan):
    # Check the level
    count = 0
    level = -1                                              # Value to return.  Defaults to -1 if no sensors are detected

    while count < length:
        Vcomp, min_column = measure_probe_voltages(chan)

        # Now test the channel with the dip to see if any of the sensors are triggered
        if ((Vcomp[min_column] <= high_limit[count]) and (Vcomp[min_column] >= low_limit[count])):
            level = depth[min_column][count]
            print ("level = " + str(level))

        count += 1

    return level

def loop(chan):
    print('The following cycle will repeat for approximately 30 s before returning to the menu')
    print('')

    i = 60
    while i > 0:
        level = test_levels(chan)
        if level == -1:
            print("No Sensors Triggered")
        else:
            print("level = " + str(level))
        
        i -= 1

def solenoid_test():
    print('The following cycle will repeat 5 times before returning to the menu')
    print('')

    i = 5
    while i > 0:
        print('...MOSFET on')
        GPIO.output(SolPin, GPIO.HIGH)     # Solenoid activated
        print('')
        sleep(5)
        print('...MOSFET off')
        GPIO.output(SolPin, GPIO.LOW)    # Solenoid inactive
        print('')
        print('')
        sleep(5)
        
        i -= 1

def fs_test(type):
    print('The following cycle will repeat 5 times before returning to the menu')
    print('')
    
    i = 5
    
    if type == 1:
        while i > 0:
            if GPIO.input(FullFloatSwitchPin):
                print("Butts Group Full Float Switch High")
            else:
                print("Butts Group Full Float Switch Low")
            if GPIO.input(EmptyFloatSwitchPin):
                print("Butts Group Empty Float Switch High")
            else:
                print("Butts Group Empty Float Switch Low")
            print('')
                
            sleep(5)

            i -= 1
        
    elif type == 2:
        while i > 0:
            if GPIO.input(FullFloatSwitchPin):
                print("Standard Butts Group Full Float Switch High")
            else:
                print("Standard Butts Group Full Float Switch Low")
            if GPIO.input(EmptyFloatSwitchPin):
                print("Standard Butts Group Empty Float Switch High")
            else:
                print("Standard Butts Group Empty Float Switch Low")
            print('')
                
            if GPIO.input(G2_FullFloatSwitchPin):
                print("G2 Butts Group Full Float Switch High")
            else:
                print("G2 Butts Group Full Float Switch Low")
            if GPIO.input(G2_EmptyFloatSwitchPin):
                print("G2 Butts Group Empty Float Switch High")
            else:
                print("G2 Butts Group Empty Float Switch Low")
            print('')

            if GPIO.input(G3_FullFloatSwitchPin):
                print("G3 Butts Group Full Float Switch High")
            else:
                print("G3 Butts Group Full Float Switch Low")
            if GPIO.input(G3_EmptyFloatSwitchPin):
                print("G3 Butts Group Empty Float Switch High")
            else:
                print("G3 Butts Group Empty Float Switch Low")
            print('')
            print('')

            sleep(5)
        
            i -= 1

def ssr_test():
    print('The following cycle will repeat 5 times before returning to the menu')
    print('')
    
    i = 5
    
    while i > 0:
        print('...Butts SSR off')
        GPIO.output(ButtsPin, GPIO.HIGH)     # Butts SSR Off
        sleep(5)
        print('...Sump SSR on')
        GPIO.output(SumpPin, GPIO.LOW)     # Sump SSR On
        print('')
        print('')
        print('...Butts SSR on')
        GPIO.output(ButtsPin, GPIO.LOW)     # Butts SSR Off
        sleep(5)
        print('...Sump SSR off')
        GPIO.output(SumpPin, GPIO.HIGH)     # Sump SSR On

        sleep(5)
        
        i -= 1
        
    GPIO.output(SumpPin, GPIO.LOW)     # Clean up

def destroy():
    GPIO.output(ButtsPin, GPIO.HIGH)    # Butts SSR off 
    GPIO.output(SumpPin, GPIO.HIGH)     # Sump SSR off
    GPIO.output(SolPin, GPIO.LOW)       # Set pin low (0 V across MOSFET gate)
    GPIO.cleanup()                      # Release resource


try:
    while True:
        print ("Select from the following Menu")
        print ("    Press '1' to fully test a Hall Effect Probe at address 0x48 (all Assys)")
        print ("    Press '2' to fully test a Hall Effect Probe at address 0x49 (Lady Hanham Assy only)")    
        print ("    Press '3' to fully test a Hall Effect Probe at address 0x4B (Lady Hanham Assy only)")    
        print ("    Press 's' to check SSR driver outputs")
        print ("    Press 'f' to check Float Switch inputs")
        print ("    Press 'F' to check Lady Hanham Float Switch inputs")
        print ("    Press 'v' to check the Solenoid Valve output")
        print ("    Press 'e' to exit this menu or Ctrl-C to exit the program at any time")

        char = input("Enter choice followed by <RET> ")

        if (char == "e"):
            print ("Exiting...")
            exit(0)

        elif (char == "1"):
            channels = setup_adc(0x48)
            loop(channels)

        elif (char == "2"):
            channels = setup_adc(0x49)
            loop(channels)

        elif (char == "3"):
            channels = setup_adc(0x4B)
            loop(channels)

        elif (char == "s"):
            ssr_test()

        elif (char == "f"):
            fs_test(1)

        elif (char == "F"):
            fs_test(2)

        elif (char == "v"):
            solenoid_test()
            
    fh.close()               # Results file closed.
    destroy()                # All GPIO outputs low.
        

   
except KeyboardInterrupt:    # When 'Ctrl+C' is pressed:
    fh.close()               # Results file closed.
    destroy()                # All GPIO outputs low.
