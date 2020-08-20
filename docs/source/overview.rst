Overview of River System Software
=================================

The river system software framework is broken into many components in different files,
also known as Python modules. Each of these serves a different task, which is
described in the documentation for each module (linked to from the index).

Current Status
--------------

The river system software has gone through many iterations. The current status is as follows:

The executable, main.py, is run on all pis, and the NAS box, and its functionality varies
based on the configuration set in config.py. All pis connect to the database in the NAS box,
which is used to store readings and to request control of other devices. In future, this
will allow for cooperative use of certain devices, such as the matrix pump, but at the
moment this is just used as a convenient way for basic control, though provision has been
put in place for extending the functionality later.

Each pi with devices to monitor regularly updates the database with new readings, according
to their individual reading intervals, which are decided by the control logic algorithms.
Any pi that has controllable devices (such as a gate valve or SSR), also has a corresponding
table in the database. Each pi also communicates with the NAS box to get "system ticks",
which are a convenient way to compare readings from different devices at different times,
and to analyse readings and/or plot them on graphs.

Current Featureset
------------------

Sump Pi uses the readings from G4 (Wendy Butts Pi) and the level from its own magnetic sensor
to manage the water level in the sump, using the database to collect readings and to control
the gate valve.

Other control logic is in the process of being written, but is not yet available. As such,
the other pis use generic control logic which just updates the pi status in the database with
the CPU and memory load.

It is also possible to shutdown and reboot individual pis (or all pis) and to apply river control
system updates to all pis and the NAS box using simple commands and the database.
