#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Socket Tools for the River System Control and Monitoring Software Version 0.10.0
# Copyright (C) 2017-2018 Wimborne Model Town
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

#NOTE: Using this terminology, "Plugs" are client sockets, "Sockets" are server sockets.

"""
This is the part of the software framework that contains the
network communications stuff. This includes a Sockets class
that abstracts some of the complexity of directly using
Python's socket package.

In extending and abstracting socket, Sockets also makes use
of a SocketHandlerThread class, to handle automatic connection
management and creation. With these classes, you push the data
you want to send to the queue, and then SocketsHandlerThread
sends the data down the socket ASAP, but if it couldn't send it,
it will stay in the queue until it is successfully sent.

.. module:: sockettools.py
    :platform: Linux
    :synopsis: The part of the framework that contains the sockets/network communications classes.

.. moduleauthor:: Hamish McIntyre-Bhatty <hamishmb@live.co.uk>

"""

from collections import deque
import socket
import select
import threading
import time
import logging
import pickle
import _pickle

VERSION = "0.10.0"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------- Sockets Class ----------
class Sockets:
    """
    This is the class that provides our high-level abstraction
    away from 'socket'.

    Documentation for constructor of objects of type Socket:

    Args:
        the_type (string):      The type of socket we are constructing.
                                **MUST** be one of "Plug", or "Socket".

    Usage:
        >>> my_socket = Sockets("Plug")

    .. note::
        On instantiation, messages to the commandline are enabled.
    """

    #pylint: disable=too-many-instance-attributes
    #We need all of the instance attributes for status tracking and error handling.

    #pylint: disable=too-many-public-methods
    #We need all of these public methods too.
    #TODO Ideally, we would simplify this, but we need to decide how.

    def __init__(self, _type, name="Unknown"):
        """The constructor, as documented above."""
        #TODO Throw error if _type is invalid.
        #Core variables and socket.
        self.port_number = -1
        self.server_address = ""
        self.type = _type
        self.name = name
        self.underlying_socket = ""
        self.server_socket = ""
        self.handler_thread = ""

        #Variables for tracking status of the handler, and the socket.
        self.verbose = True
        self.ready_to_send = False
        self.reconnected = False
        self.requested_handler_exit = False
        self.internal_request_exit = False
        self.handler_exited = False

        #Message queues (actually lists).
        self.in_queue = deque()
        self.out_queue = deque()

    # ---------- Setup Functions ----------
    def set_portnumber(self, port_number):
        """
        This method sets the port number for the socket.

        Args:
            port_number (int):      The port number for the socket.



        .. warning::
                Be aware that if this number is < than 1024, you need root
                access to bind to it successfully.

        Usage:

            >>> <Sockets-Obj>.set_portnumber(30000)
        """

        logger.debug("Sockets.set_portnumber(): Port number: "+str(port_number)+"...")
        self.port_number = port_number

    def set_server_address(self, server_address):
        """
        This method sets the server address for the socket.

        Note:
            This is only useful when creating a 'Plug' (client socket).
            Otherwise, it will be ignored.

        Args:
            server_address (string):        The server address.

        Usage:

            >>> <Sockets-Obj>.set_server_address("192.168.0.2")"""

        logger.debug("Sockets.set_server_address(): Server address: "+server_address+"...")
        self.server_address = socket.gethostbyname(server_address)

    def set_console_output(self, state):
        """
        This method can enable/disable messages to console (used in server).

        Args:
            state (bool):

                - True - enabled.
                - False - disabled.

        Usage:

            >>> <Sockets-Obj>.set_console_output(False)
        """

        logger.debug("Sockets.set_console_output(): Setting self.verbose to "+str(state)+"...")
        self.verbose = state

    def reset(self):
        """
        This method resets the socket to the default state upon instantiation.

        This is used by the sockets handler, but is also useful because it
        closes the socket, which makes it safe to exit the program.

        .. warning::
            If you're about to exit the program, make sure the handler has
            exited before you run this!

        Usage:

            >>> <Sockets-Obj>.reset()"""

        logger.debug("Sockets.reset(): Resetting socket...")

        #Variables for tracking status of the other thread.
        self.ready_to_send = False
        self.reconnected = False
        self.requested_handler_exit = False
        self.internal_request_exit = False
        self.handler_exited = False

        #Queues.
        self.in_queue = deque()
        self.out_queue = deque()

        #Sockets.
        try:
            self.underlying_socket.close()

        except AttributeError:
            #On server side, this may happen if the client socket was never created. Never mind.
            pass

        self.server_socket = ""

        logger.debug("Sockets.reset(): Done! Socket is now in its default state...")

    # ---------- Info getter functions ----------
    def is_ready(self):
        """
        This method returns True if the socket is ready for transmission, else False.

        Returns:
            bool. Whether the socket is ready to transmit or not.

            - True - Ready to transmit.
            - False - Not ready.

        Usage:

            >>> <Sockets-Obj>.is_ready()
            >>> False
        """

        return self.ready_to_send

    def just_reconnected(self):
        """
        This method returns True if the socket has just reconnected to the server,
        else False.

        Returns:
            bool. Whether the socket has just reconnected itself.

            - True - It has.
            - False - It hasn't.

        Usage:

            >>> <Sockets-Obj>.just_reconnected()
            >>> True
        """

        #Clear and return Reconnected.
        temp = self.reconnected
        self.reconnected = False

        return temp

    def wait_for_handler_to_exit(self):
        """
        This method waits for the handler to exit. Useful when e.g. doing clean-up,
        when you want to shut down the socket gracefully.

        .. warning::
            Make sure you have asked the handler to exit first, or you might end up
            stuck waiting forever!

        Usage:

            >>> <Sockets-Obj>.wait_for_handler_to_exit()
        """

        self.request_handler_exit()
        self.handler_thread.join()

    def handler_has_exited(self):
        """
        This method can be used to check whether the handler has exited. Often useful
        when trying to detect and handle errors; the handler thread may exit if it
        encounters an error it can't recover from. Also useful if you, for some
        reason, don't want to/can't use wait_for_handler_to_exit().

        Usage:

            >>> <Sockets-Obj>.handler_has_exited()
            >>> False
        """

        return self.handler_exited

    # ---------- Controller Functions ----------
    def start_handler(self):
        """
        This method starts the handler thread and then returns. Call this when you've
        finished setup and you're ready to use the socket. Connection and connection
        management will be handled for you.

        Raises:

            - ValueError if the type isn't set correctly.

        Usage:

            >>> <Sockets-Obj>.start_handler()
        """

        #Setup.
        self.ready_to_send = False
        self.reconnected = False
        self.requested_handler_exit = False
        self.internal_request_exit = False
        self.handler_exited = False

        if self.type in ("Plug", "Socket"):
            logger.debug("Sockets.start_handler(): Check passed, starting handler...")
            self.handler_thread = SocketHandlerThread(self)

        else:
            logger.debug("Sockets.start_handler(): Type is wrong, throwing runtime_error...")
            raise ValueError("Type not set correctly")

    def request_handler_exit(self):
        """
        This method is used to ask the handler to exit. Returns immediately, without waiting.

        Usage:

            >>> <Sockets-Obj>.request_handler_exit()
        """

        logger.debug("Sockets.request_handler_exit(): Requesting handler to exit...")
        self.requested_handler_exit = True

    # ---------- Handler Thread & Functions ----------
    def _create_and_connect(self):
        """
        PRIVATE, implementation detail.

        Handles connecting/reconnecting the socket.
        This should only be called by the handler thread.

        Usage:

            >>> <Sockets-Obj>._create_and_connect()
        """

        #Handle any errors while connecting.
        try:
            if self.type == "Plug":
                logger.debug("Sockets._create_and_connect(): Creating and connecting plug...")
                self._create_plug()
                self._connect_plug()

            elif self.type == "Socket":
                logger.debug("Sockets._create_and_connect(): Creating and connecting socket...")
                self._create_socket()
                self._connect_socket()

            #Make it non-blocking.
            self.underlying_socket.setblocking(0)

            #We are now connected.
            logger.debug("Sockets._create_and_connect(): Done!")
            self.ready_to_send = True

        except ConnectionRefusedError as err:
            #Connection refused by peer.
            logger.critical("Sockets._create_and_connect(): Error connecting: "+str(err))
            logger.critical("Sockets._create_and_connect(): Retrying in 10 seconds...")

            if self.verbose:
                print("Connecting Failed ("+self.name+"): "+str(err)
                      + ". Retrying in 10 seconds...")

            #Make the handler exit.
            logger.debug("Sockets._create_and_connect(): Asking handler to exit...")
            self.internal_request_exit = True

        except TimeoutError as err:
            #Connection timed out.
            logger.critical("Sockets._create_and_connect(): Error connecting: "+str(err))
            logger.critical("Sockets._create_and_connect(): Connection timed out! Poor network "
                            + "connectivity or bad socket configuration?")
            logger.critical("Sockets._create_and_connect(): Retrying in 10 seconds...")

            if self.verbose:
                print("Connecting Failed ("+self.name+"): "+str(err)
                      + ". Retrying in 10 seconds...")

            #Make the handler exit.
            logger.debug("Sockets._create_and_connect(): Asking handler to exit...")
            self.internal_request_exit = True

        except OSError as err:
            #Address already in use, probably.
            #FIXME.
            pass

    # ---------- Connection Functions (Plugs) ----------
    def _create_plug(self):
        """
        PRIVATE, implementation detail.

        Sets up the plug for us.
        Should only be called by the handler thread.

        Usage:

            >>> <Sockets-Obj>._create_plug()
        """

        logger.info("Sockets._create_plug(): Creating the plug...")

        self.underlying_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        logger.info("Sockets._create_plug(): Done!")

    def _connect_plug(self):
        """
        PRIVATE, implementation detail.

        Waits until the plug has connected to a socket.
        Should only be called by the handler thread.

        Usage:

            >>> <Sockets-Obj>._connect_plug()
        """

        logger.info("Sockets._connect_plug(): Attempting to connect to the requested socket...")

        self.underlying_socket.connect((self.server_address, self.port_number))

        logger.info("Sockets._connect_plug(): Done!")

    # ---------- Connection Functions (Sockets) ----------
    def _create_socket(self):
        """
        PRIVATE, implementation detail.

        Sets up the socket for us.
        Should only be called by the handler thread.

        Usage:

            >>> <Sockets-Obj>._create_socket()
        """

        logger.info("Sockets._create_socket(): Creating the socket...")

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', self.port_number)) #FIXME Address already in use error.
        self.server_socket.listen(10)

        logger.info("Sockets._create_socket(): Done!")

    def _connect_socket(self): #TODO Add timeout capability somehow.
        """
        PRIVATE, implementation detail.

        Waits until the socket has connected to a plug.
        Should only be called by the handler thread.

        Usage:

            >>> <Sockets-Obj>._connect_socket()
        """

        logger.info("Sockets._connect_socket(): Attempting to connect to the requested socket...")

        self.underlying_socket, addr = self.server_socket.accept()

        logger.info("Sockets._connect_socket(): Done!")

    # --------- Read/Write Functions ----------
    def write(self, data):
        """
        This method pushes a message to the outgoing message queue,
        so it can be written later by the handler thread. This is what
        you should use if you want to send a message through the socket,
        but don't care about knowing if it ever got there. Errors and
        other things are handled for you by the sockets handler if you
        use this.

        Args:
            data (any_format):      The data to add to the queue.

        Usage:

            >>> <Sockets-Obj>.write(<some_data_in_any_format>)
        """

        logger.debug("Sockets.write(): Appending "+str(data)+" to OutgoingQueue...")
        self.out_queue.append(data)

    def has_data(self):
        """
        This method returns True if there's data on the queue to read, else False.

        Returns:
            bool. Whether there's data to read or not.

            - True  - There is data to read.
            - False - There is not.

        Usage:

            >>> <Sockets-Obj>.has_data()
            >>> True
        """

        return bool(len(self.in_queue))

    def read(self):
        """
        This method returns the oldest data in the incoming queue. This is because
        if there are multiple readings sat here, we want to end up with the
        newest one, not the oldest!

        Returns:
            string. The data.

        Usage:

            >>> <Sockets-Obj>.read()
            >>> "Some Data"
        """

        logger.debug("Sockets.read(): Returning front of IncomingQueue...")
        return self.in_queue[0]

    def pop(self):
        """
        This method clears the oldest element on the incoming queue, if it isn't
        empty.

        Usage:

            >>> <Sockets-Obj.pop()
        """

        if len(self.in_queue) > 0:
            logger.debug("Sockets.pop(): Clearing oldest element of IncomingQueue...")
            self.in_queue.popleft()

    # ---------- Other Functions ----------
    def _send_pending_messages(self):
        """
        PRIVATE, implementation detail.

        Sends any messages waiting in the message queue.
        Should only be used by the handler thread.
        Returns True if successful, False if not/queue empty.

        Usage:

            >>> <Sockets-Obj>._send_pending_messages()
            >>> True
        """

        logger.debug("Sockets._send_pending_messages(): Sending any pending messages...")

        try:
            #Write all pending messages.
            while len(self.out_queue) > 0:
                #Write the oldest message first.
                logger.debug("Sockets._send_pending_messages(): Sending data...")

                #Use pickle to serialize everything.
                #We can easily delimit things with ENDMSG.
                data = pickle.dumps(self.out_queue[0])

                self.underlying_socket.sendall(data+b"ENDMSG")

                #Remove the oldest message from message queue.
                logger.debug("Sockets._send_pending_messages(): Clearing front of out_queue...")
                self.out_queue.popleft()

        except BaseException as err:
            #FIXME: Looking for an exception from sendall(), but don't know what it is.
            logger.error("Sockets._send_pending_messages(): Connection closed cleanly...")
            return False #Connection closed cleanly by peer.

        logger.debug("Sockets._send_pending_messages(): Done.")
        return True

    def _read_pending_messages(self):
        """
        PRIVATE, implementation detail.

        Attempts to read some data from the socket.
        Should only be used by the handler thread.
        Returns 0 if success, -1 if error, similar to select().

        Usage:

            >>> <Sockets-Obj>._read_pending_messages()
            >>> 0
        """

        logger.debug("Sockets._read_pending_messages(): Attempting to read from socket...")

        try:
            #This is vaguely derived from the C++ solution I found on Stack Overflow.
            logger.debug("Sockets._read_pending_messages(): Waiting for data...")

            data = b""
            pickled_obj_is_incomplete = True

            #Use a 1-second timeout.
            self.underlying_socket.settimeout(1.0)

            #While the socket is ready for reading, or there is any incomplete data,
            #keep trying to read small packets of data.
            while select.select([self.underlying_socket], [], [], 1)[0] or pickled_obj_is_incomplete:

                try:
                    print("Receiving")
                    new_data = self.underlying_socket.recv(2048)
                    print("Done")

                    if new_data == "":
                        logger.error("Sockets._read_pending_messages(): Connection closed cleanly")
                        return -1 #Connection closed cleanly by peer.

                    data += new_data

                except socket.error:
                    #What error are we looking for here? TODO
                    pass


                if b"ENDMSG" in data:
                    objs = data.split(b"ENDMSG")
                    data = objs[-1]

                    for obj in objs[:-1]:
                        self._process_obj(obj)

                #Keep reading until there's nothing left to read.
                pickled_obj_is_incomplete = (data != b"")

            logger.debug("Sockets._read_pending_messages(): Done.")

            return 0

        except BaseException as err:
            logger.error("Sockets._read_pending_messages(): Caught unhandled exception!")
            logger.error("Socket._read_pending_messages(): Error was "+str(err)+"...")
            print("Error reading messages ("+self.name+"): ", err)
            return -1

    def _process_obj(self, obj):
        #Push the unpickled objects to the message queue.
        #We need to un-serialize the data first.
        logger.debug("Sockets._process_obj(): Pushing message to IncomingQueue...")

        try:
            self.in_queue.append(pickle.loads(obj))

        except (_pickle.UnpicklingError, EOFError):
            print(b"Unpickling error ("+bytes(self.name)+"):"+obj)

class SocketHandlerThread(threading.Thread):
    """
    This is the class that provides our handler thread for
    each Sockets object. You shoudn't create any of these yourself.

    Instead use the Sockets.start_handler() method.

    Documentation for constructor of objects of type SocketHandlerThread:

    Args:
        a_socket (Sockets):      The high-level Sockets object that represents
                               our socket.

    Usage:
        >>> my_socket_handler = SocketHandlerThread(<aSockets-Obj>)

    """

    def __init__(self, a_socket):
        """The constructor, as documented above"""
        self.socket = a_socket

        threading.Thread.__init__(self)
        self.start()

    def run(self): #TODO Refactoring.
        """
        This is the body of the thread.

        It handles setup of sockets, sending/receiving data, and maintenance
        (reconnections).

        .. warning::
            Only call me from within a constructor with start(). Do **NOT** call
            me with run(), and **ABSOLUTELY DO NOT** call me outside a constructor
            for objects of this type.

        .. warning::
            Doing the above could cause any number of strange and unstable
            situations to occcur. Running self.start() is the only way (with the
            threading library) to start a new thread.
        """

        logger.debug("Sockets.Handler(): Starting up...")
        read_result = -1

        #Setup the socket.
        logger.debug("Sockets.Handler(): Calling Ptr->_create_and_connect to set the socket up...")

        while not self.socket.requested_handler_exit:
            self.socket._create_and_connect()

            #If we have connected without error, break out of this loop and enter the main loop.
            if not self.socket.internal_request_exit:
                break

            #Otherwise destroy and recreate the socket until we connect.
            #Reset the socket. Also resets the status trackers.
            logger.debug("Sockets.Handler(): Resetting socket...")
            self.socket.reset()

            #Wait for 10 seconds in between attempts.
            time.sleep(10)

        if not self.socket.requested_handler_exit:
            #We have connected.
            logger.debug("Sockets.Handler(): Done! Entering main loop.")
            print("Connected to peer ("+self.socket.name+").")

        #Keep sending and receiving messages until we're asked to exit.
        while not self.socket.requested_handler_exit:
            #Send any pending messages.
            write_result = self.socket._send_pending_messages()

            #Receive messages if there are any.
            read_result = self.socket._read_pending_messages()

            #Check if the peer left.
            if read_result == -1 or write_result == False:
                logger.debug("Sockets.Handler(): Lost connection. Attempting to reconnect...")

                if self.socket.verbose:
                    print("Lost connection to peer ("+self.socket.name
                          + "). Reconnecting...")

                #Wait for the socket to reconnect, unless the user ends the program
                #(this allows us to exit cleanly if the peer is gone).
                while not self.socket.requested_handler_exit:
                    #Reset the socket. Also resets the status trackers.
                    logger.debug("Sockets.Handler(): Resetting socket...")
                    self.socket.reset()

                    #Wait for 10 seconds in between attempts.
                    time.sleep(10)

                    logger.debug("Sockets.Handler(): Recreating and reconnecting the socket...")
                    self.socket._create_and_connect()

                    #If reconnection was successful, set flag and return to normal operation.
                    if not self.socket.internal_request_exit:
                        logger.debug("Sockets.Handler(): Success! Re-entering main loop...")
                        self.socket.reconnected = True

                        if self.socket.verbose:
                            print("Reconnected to peer ("+self.socket.name+").")

                        break

        #Flag that we've exited.
        logger.debug("Sockets.Handler(): Exiting as per the request...")
        self.socket.handler_exited = True
