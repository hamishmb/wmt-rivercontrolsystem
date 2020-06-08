#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Socket Tools for the River System Control and Monitoring Software
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
import traceback
import subprocess
import time
import logging
import pickle
import _pickle

import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLogger('River System Control Software').getEffectiveLevel())

for handler in logging.getLogger('River System Control Software').handlers:
    logger.addHandler(handler)

# ---------- Sockets Class ----------
class Sockets:
    """
    This is the class that provides our high-level abstraction
    away from 'socket'.

    Documentation for constructor of objects of type Socket:

    Args:
        _type (string):         The type of socket we are constructing.
                                **MUST** be one of "Plug", or "Socket".

        system_id (str):        The system ID.

    Kwargs:
        name (string):          The human-readable name of the socket.
                                Optional.

    Usage:
        >>> my_socket = Sockets("Plug", "G4")

        OR

        >>> my_socket = Sockets("Plug", "G4", "G4 Socket")

    .. note::
        On instantiation, messages to the commandline are enabled.
    """

    #pylint: disable=too-many-instance-attributes
    #We need all of the instance attributes for status tracking and error handling.

    #pylint: disable=too-many-public-methods
    #We need all of these public methods too.

    def __init__(self, _type, system_id, name="Unknown"):
        """The constructor, as documented above."""
        #Throw ValueError if _type is invalid.
        if _type not in ("Plug", "Socket"):
            raise ValueError("_type must be either 'Plug' or 'Socket'")

        #Throw ValueError if system_id is invalid.
        if system_id not in config.SITE_SETTINGS:
            raise ValueError("Invalid system ID")

        #Throw ValueError if name is invalid.
        if not isinstance(name, str):
            raise ValueError("_name must be of type str")

        #Core variables and socket.
        self.port_number = -1
        self.server_address = ""
        self.type = _type
        self.name = name
        self.system_id = system_id
        self.underlying_socket = None
        self.server_socket = None
        self.handler_thread = None

        #Variables for tracking status of the handler, and the socket.
        self.verbose = True
        self.ready_to_send = False
        self.reconnected = False
        self.internal_request_exit = False
        self.handler_exited = False

        #Message queues (actually lists).
        self.in_queue = deque()
        self.out_queue = deque()
        self.forward_queue = deque()

        #Add this sockets object to the list.
        config.SOCKETSLIST.append(self)

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

        #Check the port number is valid.
        if (not isinstance(port_number, int)) or \
            isinstance(port_number, bool) or \
            port_number <= 0 or \
            port_number > 65535:

            raise ValueError("Invalid port number: "+str(port_number))

        logger.debug("Sockets.set_portnumber(): Port number ("+self.name+"): "+str(port_number)+"...")
        self.port_number = port_number

    def set_server_address(self, server_address):
        """
        This method sets the server address for the socket.

        Note:
            Now needed for both sockets, so we can ping the peer.

        Args:
            server_address (string):        The server address.

        Usage:

            >>> <Sockets-Obj>.set_server_address("192.168.0.2")"""

        #Check the IP address is valid (basic check).
        if not isinstance(server_address, str) or \
            len(server_address.split(".")) != 4 or \
            server_address == "0.0.0.0":

            raise ValueError("Invalid IPv4 address: "+str(server_address))

        #Advanced checks.
        #Check that each octet is a integer and between 0 and 255 (exclusive).
        for octet in server_address.split("."):
            if not octet.isdigit() or \
                int(octet) > 254 or \
                int(octet) < 0:

                raise ValueError("Invalid IPv4 address: "+str(server_address))

        logger.debug("Sockets.set_server_address(): Server address ("+self.name+"): "+server_address+"...")
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

        if not isinstance(state, bool):
            raise ValueError("state must be of type bool")

        logger.debug("Sockets.set_console_output(): ("+self.name+"): Setting self.verbose to "+str(state)+"...")
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

        logger.info("Sockets.reset(): ("+self.name+"): Resetting socket...")

        #Variables for tracking status of the other thread.
        self.ready_to_send = False
        self.reconnected = False
        self.internal_request_exit = False
        self.handler_exited = False

        #Don't reset queues, as this will drop pending data!

        #Sockets.
        try:
            self.underlying_socket.shutdown(socket.SHUT_RDWR)
            self.underlying_socket.close()

        except (AttributeError, OSError):
            #This may happen if the underlying socket was not created/connected
            #yet. Never mind.
            pass

        self.underlying_socket = None

        if self.server_socket is not None:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
                self.server_socket.close()

            except (AttributeError, OSError):
                #This may happen if the underlying socket was not created/connected
                #yet. Never mind.
                pass

        self.server_socket = None

        logger.info("Sockets.reset(): ("+self.name+"): Done! Socket is now in its default state...")

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


        while not self.handler_exited:
            time.sleep(0.5)

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
        self.internal_request_exit = False
        self.handler_exited = False

        if self.type in ("Plug", "Socket"):
            logger.debug("Sockets.start_handler(): ("+self.name+"): Check passed, starting handler...")
            self.handler_thread = SocketHandlerThread(self)

        else:
            logger.error("Sockets.start_handler(): ("+self.name+"): Type is wrong, throwing ValueError...")
            raise ValueError("Type must be 'Plug' or 'Socket'")

    # ---------- Handler Thread & Functions ----------
    def peer_alive(self):
        """
        Used to ping peer once at other end of the connection to check if it is still up.

        Used on first connection, and periodically so we know if a host goes down.

        Returns:
            boolean.        True = peer is online
                            False = peer is offline

        Usage:
            >>> <Sockets-Obj>.peer_alive()
            >>> True
        """
        try:
            #Ping the peer one time.
            subprocess.run(["ping", "-c", "1", "-W", "2", self.server_address],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)

            #If there was no error, this was fine.
            logger.debug("Sockets.peer_alive(): ("+self.name+"): Peer is up...")
            return True

        except subprocess.CalledProcessError:
            #Non-zero exit status.
            logger.warning("Sockets.peer_alive(): ("+self.name+"): Peer is down!")

            if self.verbose:
                print("Connection Failed, peer down ("+self.name+"). "
                      + "Retrying in 10 seconds...")

            return False

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
                logger.info("Sockets._create_and_connect(): ("+self.name+"): Creating and connecting plug...")
                self._create_plug()
                self._connect_plug()

            elif self.type == "Socket":
                logger.info("Sockets._create_and_connect(): ("+self.name+"): Creating and connecting socket...")
                self._create_socket()
                self._connect_socket()

            #Make it non-blocking.
            self.underlying_socket.setblocking(False)

            #We are now connected.
            logger.info("Sockets._create_and_connect(): ("+self.name+"): Done!")
            self.internal_request_exit = False
            self.ready_to_send = True

        except ConnectionRefusedError as err:
            #Connection refused by server.
            logger.error("Sockets._create_and_connect(): ("+self.name+"): Error connecting:\n\n"
                         + str(traceback.format_exc()) + "\n\n")

            logger.error("Sockets._create_and_connect(): ("+self.name+"): Retrying in 10 seconds...")

            if self.verbose:
                print("Connection Refused ("+self.name+"): "+str(err)
                      + ". Retrying in 10 seconds...")

            #Make the handler exit.
            logger.debug("Sockets._create_and_connect(): ("+self.name+"): Asking handler to exit...")
            self.internal_request_exit = True

        except (socket.timeout, TimeoutError, BlockingIOError) as err:
            #Connection timed out (waiting for client to connect).
            logger.error("Sockets._create_and_connect(): ("+self.name+"): Error connecting:\n\n"
                         + str(traceback.format_exc()) + "\n\n")

            logger.error("Sockets._create_and_connect(): ("+self.name+"): Connection timed out! Poor network "
                         + "connectivity or bad socket configuration?")

            logger.error("Sockets._create_and_connect(): ("+self.name+"): Retrying in 10 seconds...")

            if self.verbose:
                print("Connection Timed Out ("+self.name+"): "+str(err)
                      + ". Retrying in 10 seconds...")

            #Make the handler exit.
            logger.debug("Sockets._create_and_connect(): ("+self.name+"): Asking handler to exit...")
            self.internal_request_exit = True

        except OSError as err:
            #Address already in use, probably.
            #This shouldn't occur any more, but it may still happen from time to time.
            logger.error("Sockets._create_and_connect(): ("+self.name+"): Error connecting:\n\n"
                         + str(traceback.format_exc()) + "\n\n")

            logger.error("Sockets._create_and_connect(): ("+self.name+"): Unknown error, possibly "
                         + "address already in use?")

            logger.error("Sockets._create_and_connect(): ("+self.name+"): Retrying in 10 seconds...")

            if self.verbose:
                print("Connection Timed Out ("+self.name+"): "+str(err)
                      + ". Retrying in 10 seconds...")

            #Make the handler exit.
            logger.debug("Sockets._create_and_connect(): ("+self.name+"): Asking handler to exit...")
            self.internal_request_exit = True

    # ---------- Connection Functions (Plugs) ----------
    def _create_plug(self):
        """
        PRIVATE, implementation detail.

        Sets up the plug for us.
        Should only be called by the handler thread.

        Usage:

            >>> <Sockets-Obj>._create_plug()
        """

        logger.info("Sockets._create_plug(): ("+self.name+"): Creating the plug...")

        self.underlying_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.underlying_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        logger.info("Sockets._create_plug(): ("+self.name+"): Done!")

    def _connect_plug(self):
        """
        PRIVATE, implementation detail.

        Attempts to connect the plug to a socket. Does not block.
        Should only be called by the handler thread.

        Usage:

            >>> <Sockets-Obj>._connect_plug()
        """

        logger.info("Sockets._connect_plug(): ("+self.name+"): Attempting to connect to the requested socket...")

        self.underlying_socket.connect((self.server_address, self.port_number))

        logger.info("Sockets._connect_plug(): ("+self.name+"): Done!")

    # ---------- Connection Functions (Sockets) ----------
    def _create_socket(self):
        """
        PRIVATE, implementation detail.

        Sets up the socket for us.
        Should only be called by the handler thread.

        Usage:

            >>> <Sockets-Obj>._create_socket()
        """

        logger.info("Sockets._create_socket(): ("+self.name+"): Creating the socket...")

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', self.port_number))
        self.server_socket.listen(10)

        #Make it non-blocking.
        self.server_socket.settimeout(15)

        logger.info("Sockets._create_socket(): ("+self.name+"): Done!")

    def _connect_socket(self):
        """
        PRIVATE, implementation detail.

        Attempts to connect the socket to a plug. Does not block.
        Should only be called by the handler thread.

        Usage:

            >>> <Sockets-Obj>._connect_socket()
        """

        logger.info("Sockets._connect_socket(): ("+self.name+"): Attempting to connect to the requested socket...")

        self.underlying_socket = self.server_socket.accept()[0]

        logger.info("Sockets._connect_socket(): ("+self.name+"): Done!")

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

        logger.debug("Sockets.write(): ("+self.name+"): Appending "+str(data)+" to OutgoingQueue...")
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

        Throws:
            IndexError, if there is no data on the queue to read.

        Returns:
            string. The data.

        Usage:

            >>> <Sockets-Obj>.read()
            >>> "Some Data"
        """

        logger.debug("Sockets.read(): ("+self.name+"): Returning front of IncomingQueue...")
        return self.in_queue[0]

    def pop(self):
        """
        This method clears the oldest element on the incoming queue, if it isn't
        empty.

        Usage:

            >>> <Sockets-Obj.pop()
        """

        #Clear the oldest element of the queue if there's anything in it.
        if self.in_queue:
            logger.debug("Sockets.pop(): ("+self.name+"): Clearing oldest element of IncomingQueue...")
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

        logger.debug("Sockets._send_pending_messages(): ("+self.name+"): Sending any pending messages...")

        try:
            #Write all pending messages, if there are any.
            while self.out_queue:
                #Write the oldest message first.
                logger.info("Sockets._send_pending_messages(): ("+self.name+"): Sending data...")

                #Use pickle to serialize everything.
                #We can easily delimit things with ENDMSG.
                data = pickle.dumps(self.out_queue[0])

                self.underlying_socket.sendall(data+b"ENDMSG")

                #Remove the oldest message from message queue.
                logger.debug("Sockets._send_pending_messages(): ("+self.name+"): Clearing front of out_queue...")
                self.out_queue.popleft()

        except _pickle.PicklingError:
            #Unable to pickle the object!
            logger.error("Sockets._send_pending_messages(): ("+self.name+"): Unable to pickle data to send to peer! "
                         + "Error was:\n\n"+str(traceback.format_exc())
                         + "\n\nContinuing...")

            self.out_queue.popleft()

        except OSError:
            #Assume that network is down or client gone. Recreate the socket.
            logger.error("Sockets._send_pending_messages(): ("+self.name+"): Connection closed or client gone. "
                         + "Error was:\n\n"+str(traceback.format_exc())
                         + "\n\nAttempting to reconnect...")

            return False #Connection closed cleanly by peer.

        logger.debug("Sockets._send_pending_messages(): ("+self.name+"): Done.")
        return True

    def _forward_messages(self):
        """
        PRIVATE, implementation detail.

        Puts any messages that we need to forward on the correct socket's queue.
        Should only be used by the handler thread.
        Returns True if successful, False if not/queue empty.

        Usage:

            >>> <Sockets-Obj>._forward_messages()
            >>> True
        """

        logger.debug("Sockets._forward_messages(): ("+self.name+"): Forwarding any pending messages...")

        #Forward all pending messages, if there are any.
        while self.forward_queue:
            #Write the oldest message first.
            logger.info("Sockets._forward_messages(): ("+self.name+"): Forwarding data...")

            msg = self.forward_queue[0]

            #Find the correct socket to send the message to.
            dest_sysid = msg.split(" ")[0].replace("*", "")
            dest_ipaddr = config.SITE_SETTINGS[dest_sysid]["IPAddress"]

            dest_socket = None

            for _socket in config.SOCKETSLIST:
                if _socket.server_address == dest_ipaddr:
                    dest_socket = _socket

            if dest_socket is None:
                #Couldn't find the socket to forward this message to!
                logger.error("Sockets._forward_messages(): ("+self.name+"): Cannot forward message for "+dest_sysid+"! Dropping message.")

            else:
                dest_socket.write(msg)

            #Remove the oldest message from message queue.
            logger.debug("Sockets._forward_messages(): ("+self.name+"): Clearing front of forward_queue...")
            self.forward_queue.popleft()

        logger.debug("Sockets._forward_messages(): ("+self.name+"): Done.")
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

        logger.debug("Sockets._read_pending_messages(): ("+self.name+"): Attempting to read from socket...")

        try:
            #This is vaguely derived from the C++ solution I found on Stack Overflow.
            logger.debug("Sockets._read_pending_messages(): ("+self.name+"): Waiting for data...")

            data = b""

            #Don't hang forever if there's no data.
            pickled_obj_is_incomplete = False

            #While the socket is ready for reading, or there is any incomplete data,
            #keep trying to read small packets of data.
            while select.select([self.underlying_socket], [], [], 1)[0] \
                or pickled_obj_is_incomplete:

                try:
                    new_data = self.underlying_socket.recv(2048)

                    if new_data == b"":
                        logger.error("Sockets._read_pending_messages(): ("+self.name+"): Connection closed cleanly")
                        return -1 #Connection closed cleanly by peer.

                    #Set this now, seeing as we have received at least part of an object.
                    pickled_obj_is_incomplete = True

                    data += new_data

                except OSError:
                    #Ignore this, it means the whole pickled object hasn't arrived just yet.
                    pass

                if b"ENDMSG" in data:
                    objs = data.split(b"ENDMSG")
                    data = objs[-1]

                    for obj in objs[:-1]:
                        logger.info("Sockets._read_pending_messages(): ("+self.name+"): Received data.")
                        self._process_obj(obj)

                #Keep reading until there's nothing left to read.
                pickled_obj_is_incomplete = (data != b"")

            logger.debug("Sockets._read_pending_messages(): ("+self.name+"): Done.")

            return 0

        except Exception:
            logger.error("Sockets._read_pending_messages(): ("+self.name+"): Caught unhandled exception!")
            logger.error("Socket._read_pending_messages(): ("+self.name+"): Error was\n\n"
                         + str(traceback.format_exc())+"...")

            print("Error reading messages ("+self.name+"): ", traceback.format_exc())
            return -1

    def _process_obj(self, obj):
        #Push the unpickled objects to the message queue.
        #We need to un-serialize the data first.
        try:
            msg = pickle.loads(obj)

        except (_pickle.UnpicklingError, TypeError, EOFError):
            logger.error("Sockets._process_obj(): ("+self.name+"): Error unpickling data from socket: "+str(obj))
            print("Unpickling error ("+self.name+"): "+str(obj))
            return

        if isinstance(msg, str):
            potential_sysid = msg.split(" ")[0].replace("*", "")

        else:
            potential_sysid = None

        #Append to the appropriate queue.
        if potential_sysid != self.system_id and potential_sysid in config.SITE_SETTINGS:
            #Needs to be sent to another device.
            logger.debug("Sockets._process_obj(): ("+self.name+"): Pushing message to forward queue...")
            self.forward_queue.append(msg)

        else:
            #This message is intended for us.
            logger.debug("Sockets._process_obj(): ("+self.name+"): Pushing message to incoming queue...")

            if isinstance(msg, str) and "*" in msg:
                self.in_queue.append(' '.join(msg.split(" ")[1:]))

            else:
                self.in_queue.append(msg)

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

        logger.debug("Sockets.Handler(): ("+self.socket.name+"): Starting up...")
        read_result = -1

        #-------------------- Setup the socket --------------------
        #Setup the socket.
        logger.debug("Sockets.Handler(): ("+self.socket.name+"): Calling self.socket._create_and_connect to set the socket up...")

        while not config.EXITING:
            self.socket.internal_request_exit = True

            if self.socket.peer_alive():
                self.socket._create_and_connect()

            #If we have connected without error, break out of this loop and enter the main loop.
            if not self.socket.internal_request_exit:
                break

            #Otherwise destroy and recreate the socket until we connect.
            #Reset the socket. Also resets the status trackers.
            logger.debug("Sockets.Handler(): ("+self.socket.name+"): Resetting socket...")
            self.socket.reset()

            #Wait for 10 seconds in between attempts.
            time.sleep(10)

        if not config.EXITING:
            #We have connected.
            logger.debug("Sockets.Handler(): ("+self.socket.name+"): Done! Entering main loop.")
            print("Connected to peer ("+self.socket.name+").")

        #-------------------- Manage the connection, sending and receiving data --------------------
        #Keep sending and receiving messages until we're asked to exit.
        iters_count = 0
        last_ping_good = True

        while not config.EXITING:
            #Send any pending messages.
            write_result = self.socket._send_pending_messages()

            #Queue any messages to forward on the correct socket.
            self.socket._forward_messages()

            #Receive messages if there are any.
            read_result = self.socket._read_pending_messages()

            #Do a ping, if it's time (we don't want to do one every time and flood the network).
            #This should be roughly every 30 seconds.
            if iters_count < 30:
                iters_count += 1

            else:
                iters_count = 0
                last_ping_good = self.socket.peer_alive()

            if read_result == -1 or write_result is False or not last_ping_good:
                logger.error("Sockets.Handler(): ("+self.socket.name+"): Lost connection. Attempting to reconnect...")

                if self.socket.verbose:
                    print("Lost connection to peer ("+self.socket.name
                          + "). Reconnecting...")

                #Wait for the socket to reconnect, unless the user ends the program
                #(this allows us to exit cleanly if the peer is gone).
                while not config.EXITING: #FIXME code duplication
                    #Reset the socket. Also resets the status trackers.
                    logger.error("Sockets.Handler(): ("+self.socket.name+"): Resetting socket...")
                    self.socket.reset()

                    #Wait for 10 seconds in between attempts.
                    time.sleep(10)

                    self.socket.internal_request_exit = True

                    logger.debug("Sockets.Handler(): ("+self.socket.name+"): Recreating and reconnecting the socket...")
                    if self.socket.peer_alive():
                        self.socket._create_and_connect()

                    #If reconnection was successful, set flag and return to normal operation.
                    if not self.socket.internal_request_exit:
                        logger.debug("Sockets.Handler(): ("+self.socket.name+"): Success! Re-entering main loop...")
                        self.socket.reconnected = True
                        last_ping_good = True

                        if self.socket.verbose:
                            print("Reconnected to peer ("+self.socket.name+").")

                        break

        #Flag that we've exited.
        logger.info("Sockets.Handler(): ("+self.socket.name+"): Exiting as per the request...")
        self.socket.handler_exited = True
