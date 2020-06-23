Documentation for the sockettools module
****************************************

Protocol
========

The protocol the river control system uses is not yet finalised or officially agreed. However, the following is in place:

If you have a central computer with many sockets connecting to other computers, you can use it as a relay.

If site A is connected to site B, which is connected to site C, A can talk to C by prefixing the message with the site name, eg:

>>> socket.send("*C* Hello, world")

When B receives this message, it will forward it on to C. Note that there is no error returned if forwarding failed or if the message couldn't be delivered.
