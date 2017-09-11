#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Socket Tools for the River System Control and Monitoring Software Version 0.9.1
# Copyright (C) 2017 Wimborne Model Town
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

#TODO All of this is a hastily-done port of some C++ code from Stroodlr,
#(my (Hamish's) newest incomplete project).
#As such, it needs a lot of cleanup and testing.
#It's all very hacky and messy, but it works, mostly.

#NOTE: Using this terminology, "Plugs" are client sockets, "Sockets" are server sockets.

import socket
import select
import threading
import time
from collections import deque

# ---------- Sockets Class ----------
class Sockets:
    #pylint: disable=too-many-instance-attributes
    #We need all of the instance attributes for status tracking and error handling.

    #pylint: disable=too-many-public-methods
    #We need all of these public methods too.
    #TODO Ideally, we would simplify this, but we need to decide how.

    def __init__(self, TheType):
        """Sets up and initialises the sockets instance."""

        #Core variables and socket.
        self.port_number = -1
        self.server_address = ""
        self.type = TheType
        self.underlying_socket = ""
        self.server_socket = ""
        self.handler_thread = ""

        #Variables for tracking status of the handler, and the socket.
        self.verbose = True
        self.ready_to_send = False
        self.reconnected = False
        self.requested_handler_exit = False
        self.handler_exited = False

        #Message queues (actually lists).
        self.in_queue = deque()
        self.out_queue = deque()

    # ---------- Setup Functions ----------
    def set_portnumber(self, port_number):
        """
        Sets the port number for the socket.
        Usage:

            <Sockets-Instance>.set_portnumber(int port_number)"""

        logger.debug("Sockets.set_portnumber(): Port number: "+str(port_number)+"...")
        self.port_number = port_number

    #Only useful when creating a plug, rather than a socket.
    def set_server_address(self, server_address):
        """
        Sets the server address for the socket.
        This is only useful when creating a 'Plug' (client socket).
        Usage:

            <Sockets-Instance>.set_server_address(string server_address)"""

        logger.debug("Sockets.set_server_address(): Server address: "+server_address+"...")
        self.server_address = socket.gethostbyname(server_address)

    def set_console_output(self, state):
        """
        Can tell us not to output any messages to console (used in server).
        Usage:

            <Sockets-Instance>.set_console_output(bool State)"""

        logger.debug("Sockets.set_console_output(): Setting self.verbose to "+str(state)+"...")
        self.verbose = state

    def reset(self):
        """
        Resets the socket to the default state.
        Also closes the socket to make it safe to exit the program.
        Usage:

            <Sockets-Instance>.reset()"""

        logger.debug("Sockets.reset(): Resetting socket...")

        #Variables for tracking status of the other thread.
        self.ready_to_send = False
        self.reconnected = False
        self.requested_handler_exit = False
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
        Returns True if Socket is ready for transmission, else False.
        Usage:

            bool <Sockets-Instance>.is_ready()"""

        return self.ready_to_send

    def just_reconnected(self):
        """
        Returns True if socket just reconnected to the server, else False.
        Usage:

            bool <Socket-Instance>.just_reconnected()"""

        #Clear and return Reconnected.
        temp = self.reconnected
        self.reconnected = False

        return temp

    def wait_for_handler_to_exit(self):
        """
        Useful when e.g. doing clean-up, when you want to shut down the socket gracefully.
        Waits until the handler thread has exited.
        Usage:

            <Sockets-Instance>.wait_for_handler_to_exit()"""

        self.handler_thread.join()

    def handler_has_exited(self):
        """
        Used to check whether the handler has exited.
        Often useful when trying to detect and handle errors;
        the handler thread may exit if it encounters an error it can't recover from.
        Usage:

            <Sockets-Instance>.handler_has_exited()"""

        return self.handler_exited

    # ---------- Controller Functions ----------
    def start_handler(self):
        """
        Starts the handler thread and then returns.
        Usage:

            <Sockets-Instance>.start_handler()"""

        #Setup.
        self.ready_to_send = False
        self.reconnected = False
        self.requested_handler_exit = False
        self.handler_exited = False

        if self.type in ("Plug", "Socket"):
            logger.debug("Sockets.start_handler(): Check passed, starting handler...")
            self.handler_thread = SocketHandlerThread(self)

        else:
            logger.debug("Sockets.start_handler(): Type is wrong, throwing runtime_error...")
            raise ValueError("Type not set correctly")

    def request_handler_exit(self):
        """
        Used to ask the handler to exit. Returns immediately.
        Usage:

            <Sockets-Instance>.request_handler_exit()"""

        logger.debug("Sockets.request_handler_exit(): Requesting handler to exit...")
        self.requested_handler_exit = True

    # ---------- Handler Thread & Functions ----------
    def create_and_connect(self):
        """
        Handles connecting/reconnecting the socket.
        This should only be called by the handler thread.
        Usage:

            <Sockets-Instance>.create_and_connect()"""

        #Handle any errors while connecting.
        try:
            if self.type == "Plug":
                logger.debug("Sockets.create_and_connect(): Creating and connecting plug...")
                self.create_plug()
                self.connect_plug()

            elif self.type == "Socket":
                logger.debug("Sockets.create_and_connect(): Creating and connecting socket...")
                self.create_socket()
                self.connect_socket()

            #We are now connected.
            logger.debug("Sockets.create_and_connect(): Done!")
            self.ready_to_send = True

        except BaseException as err: #FIXME WHAT ERROR WOULD WE NEED TO CATCH?
            logger.critical("Sockets.create_and_connect(): Error connecting: "+str(err))
            logger.critical("Socket.create_and_connect(): .Retrying in 10 seconds...")

            if self.verbose:
                print("Connecting Failed: "+str(err)+". Retrying in 10 seconds...")

            #Make the handler exit.
            logger.debug("Sockets.create_and_connect(): Asking handler to exit...")
            self.requested_handler_exit = True

    # ---------- Connection Functions (Plugs) ---------- FIXME: Add error handling.
    def create_plug(self):
        """
        Sets up the plug for us.
        Should only be called by the handler thread.
        Usage:

            <Sockets-Instance>.create_plug()"""

        logger.info("Sockets.create_plug(): Creating the plug...")

        self.underlying_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        logger.info("Sockets.create_plug(): Done!")

    def connect_plug(self):
        """
        Waits until the plug has connected to a socket.
        Should only be called by the handler thread.
        Usage:

            <Sockets-Instance>.connect_plug()"""

        logger.info("Sockets.connect_plug(): Attempting to connect to the requested socket...")

        self.underlying_socket.connect((self.server_address, self.port_number))

        logger.info("Sockets.connect_plug(): Done!")

    # ---------- Connection Functions (Sockets) ---------- FIXME: Add error handling.
    def create_socket(self):
        """
        Sets up the socket for us.
        Should only be called by the handler thread.
        Usage:

            <Sockets-Instance>.create_socket()"""

        logger.info("Sockets.create_socket(): Creating the socket...")

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', self.port_number))
        self.server_socket.listen(10)

        logger.info("Sockets.create_socket(): Done!")

    def connect_socket(self):
        """
        Waits until the socket has connected to a plug.
        Should only be called by the handler thread.
        Usage:

            <Sockets-Instance>.connect_socket()"""

        logger.info("Sockets.connect_socket(): Attempting to connect to the requested socket...")

        self.underlying_socket, addr = self.server_socket.accept()

        logger.info("Sockets.connect_socket(): Done!")

    # --------- Read/Write Functions ----------
    def write(self, data):
        """
        Pushes a message to the outgoing message queue,
        so it can be written later by the handler thread.
        This is wat you should use if you want to send a message through the socket,
        but don't care about knowing if it ever got there.
        Errors and other things are handled for you if you use this.
        Usage:

            <Sockets-Instance>.write(string data)"""

        logger.debug("Sockets.write(): Appending "+data+" to OutgoingQueue...")
        self.out_queue.append(data)

    def send_to_peer(self, data): #FIXME: If ACK is very slow, try again.
        #FIXME: Will need to change this later cos if there's a
        #high volume of messages it might fail.
        """
        Sends the given message to the peer & waits for an acknowledgement. A convenience function.
        Useful when you want to know if the peer got your message, but slower.
        Usage:

            <Sockets-Instance>.send_to_peer(string data)"""

        logger.debug("Sockets.send_to_peer(): Sending message "+data+" to peer...")

        #Push it to the message queue.
        self.write(data)

        #Wait until a \x06 (ASCII ACK code) has arrived.
        logger.debug("Sockets.send_to_peer(): Waiting for acknowledgement...")
        while not self.has_data():
            time.sleep(0.1)

        #Remove the ACK from the queue.
        logger.info("Sockets.send_to_peer(): Done.")
        self.pop()

    def has_data(self):
        """
        Returns true if there's data on the queue to read, else false.
        Usage:

            bool <Sockets-Instance>.has_data()"""

        return bool(len(self.in_queue))

    def read(self):
        """
        Returns the item at the front of IncomingQueue.
        Usage:

            string <Sockets-Instance>.read()"""

        logger.debug("Sockets.read(): Returning front of IncomingQueue...")
        return self.in_queue[0]

    def pop(self):
        """
        Clears the oldest element from IncomingQueue, if any.
        Usage:

            <Sockets-Instance.pop()"""

        if len(self.in_queue) > 0:
            logger.debug("Sockets.pop(): Clearing oldest element of IncomingQueue...")
            self.in_queue.popleft()

    # ---------- Other Functions ----------
    def send_pending_messages(self):
        """
        Sends any messages waiting in the message queue.
        Should only be used by the handler thread.
        Returns True if successful, False if not/queue empty.
        Usage:

            bool <Sockets-Instance>.send_pending_messages()"""

        logger.debug("Sockets.send_pending_messages(): Sending any pending messages...")

        try:
            #Write all pending messages.
            while len(self.out_queue) > 0:
                #Write the oldest message first.
                logger.debug("Sockets.send_pending_messages(): Sending data...")
                self.underlying_socket.sendall(bytes(self.out_queue[0], "utf-8"))

                #Remove the oldest message from message queue.
                logger.debug("Sockets.send_pending_messages(): Clearing front of out_queue...")
                self.out_queue.popleft()

        except BaseException as err:
            #FIXME: Looking for an exception from sendall(), but don't know what it is.
            logger.error("Sockets.send_pending_messages(): Connection closed cleanly...")
            return False #Connection closed cleanly by peer.

        logger.debug("Sockets.send_pending_messages(): Done.")
        return True

    def read_pending_messages(self):
        """
        Attempts to read some data from the socket.
        Should only be used by the handler thread.
        Returns 0 if success, -1 if error, similar to select().
        Usage:

            int <Sockets-Instance>.read_pending_messages()"""

        logger.debug("Sockets.read_pending_messages(): Attempting to read from socket...")

        try:
            #This is vaguely derived from the C++ solution I found on Stack Overflow.
            logger.debug("Sockets.read_pending_messages(): Waiting for data...")

            data = ""

            #While the socket is ready for reading, keep trying to read small packets of data.
            while select.select([self.underlying_socket], [], [], 1)[0]:
                #Use a 1-second timeout.
                self.underlying_socket.settimeout(1.0)

                new_data = self.underlying_socket.recv(2048).decode("utf-8")

                if new_data == "":
                    logger.error("Sockets.send_pending_messages(): Connection closed cleanly...")
                    return -1 #Connection closed cleanly by peer.

                data += new_data

            #Push to the message queue, if there is a message.
            if data != "":
                logger.debug("Sockets.read_pending_messages(): Pushing message to IncomingQueue...")
                self.in_queue.append(data)

                logger.debug("Sockets.read_pending_messages(): Done.")

            return 0

        except BaseException as err:
            logger.error("Sockets.read_pending_messages(): Caught unhandled exception!")
            logger.error("Socket.read_pending_messages(): Error was "+str(err)+"...")
            print("Error: ", err)
            return -1

class SocketHandlerThread(threading.Thread):
    """
    This is the socket handler thread, used in conjunction with the Sockets class.
    Creation of an instance of this thread is handled by the Sockets Class.
    Usage:

        [var =] SocketHandlerThread(self)"""

    def __init__(self, Socket):
        """Initialize and start the thread."""
        self.underlying_socket = Socket

        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """Handles setup, send/receive, and maintenance of socket (reconnections)."""
        logger.debug("Sockets.Handler(): Starting up...")
        read_result = -1

        #Setup the socket.
        logger.debug("Sockets.Handler(): Calling Ptr->create_and_connect to set the socket up...")

        while True:
            self.underlying_socket.create_and_connect()

            if not self.underlying_socket.requested_handler_exit:
                break

            #Otherwise destroy and recreate the socket until we connect.
            #Reset the socket. Also resets the status trackers.
            logger.debug("Sockets.Handler(): Resetting socket...")
            self.underlying_socket.reset()

            #Wait for 10 seconds in between attempts.
            time.sleep(10)

        #We have connected.
        logger.debug("Sockets.Handler(): Done! Entering main loop.")
        print("Connected to peer.")

        #Keep sending and receiving messages until we're asked to exit.
        while not self.underlying_socket.requested_handler_exit:
            #Send any pending messages.
            sent = self.underlying_socket.send_pending_messages()

            #Receive messages if there are any.
            read_result = self.underlying_socket.read_pending_messages()

            #Check if the peer left.
            if read_result == -1:
                logger.debug("Sockets.Handler(): Lost connection. Attempting to reconnect...")

                if self.underlying_socket.Verbose:
                    print("Lost connection to peer. Reconnecting...")

                #Wait indefinitely for the socket to reconnect.
                while True:
                    #Reset the socket. Also resets the status trackers.
                    logger.debug("Sockets.Handler(): Resetting socket...")
                    self.underlying_socket.reset()

                    #Wait for 10 seconds in between attempts.
                    time.sleep(10)

                    logger.debug("Sockets.Handler(): Recreating and reconnecting the socket...")
                    self.underlying_socket.create_and_connect()

                    #If reconnection was successful, set flag and return to normal operation.
                    if not self.underlying_socket.requested_handler_exit:
                        logger.debug("Sockets.Handler(): Success! Re-entering main loop...")
                        self.underlying_socket.Reconnected = True

                        if self.underlying_socket.Verbose:
                            print("Reconnected to peer.")

                        break

        #Flag that we've exited.
        logger.debug("Sockets.Handler(): Exiting as per the request...")
        self.underlying_socket.HandlerExited = True
