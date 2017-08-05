#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Core Tools for the River System Control and Monitoring Software Version 1.0
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

import datetime
import sys
import getopt
import time
import socket
import select
import threading

def HandleCmdlineOptions(UsageFunc):
    """
    Handles commandline options for the standalone monitor programs
    Usage:

        tuple HandleCmdlineOptions(function UsageFunc)
    """

    FileName = "Unknown"

    #Check all cmdline options are valid.
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:n:", ["help", "file=", "num="])

    except getopt.GetoptError as err:
        #Invalid option. Show the help message and then exit.
        #Show the error.
        print(str(err))
        UsageFunc()
        sys.exit(2)

    #Do setup. o=option, a=argument.
    NumberOfReadingsToTake = 0 #Take readings indefinitely by default.

    for o, a in opts:
        if o in ["-n", "--num"]:
            NumberOfReadingsToTake = int(a)

        elif o in ["-f", "--file"]:
            FileName = a

        elif o in ["-h", "--help"]:
            UsageFunc()
            sys.exit()
    
        else:
            assert False, "unhandled option"

    return FileName, NumberOfReadingsToTake

def GreetAndGetFilename(ModuleName, FileName):
    """
    Greets user and gets a file name for readings.
    Usage:

        file-obj GreetAndGetFilename(string ModuleName)
    """

    print("System Time: ", str(datetime.datetime.now()))
    print(ModuleName+" is running standalone.")
    print("Welcome. This program will quit automatically if you specified a number of readings, otherwise quit by pressing CTRL-C twice when you wish.\n")

    #Get filename, if one wasn't specified.
    if FileName == "Unknown":
        print("Please enter a filename to save the readings to.")
        print("The file will be appended to.")
        print("Make sure it's somewhere where there's plenty of disk space. Suggested: readings.txt")

        sys.stdout.write("Enter filename and press ENTER: ")

        FileName = input()

        print("\n\nSelected File: "+FileName)
        print("Press CTRL-C if you are not happy with this choice.\n")

        print("Press ENTER to continue...")

        input() #Wait until user presses enter.

    try:
        print("Opening file...")
        RecordingsFile = open(FileName, "a",)

    except:
        #Bad practice :P
        print("Error opening file. Do you have permission to write there?")
        print("Exiting...")
        sys.exit()

    else:
        RecordingsFile.write("Start Time: "+str(datetime.datetime.now())+"\n\n")
        RecordingsFile.write("Starting to take readings...\n")
        print("Successfully opened file. Continuing..")

    return FileName, RecordingsFile

# ---------- Sockets Class ----------
class Sockets:
    def __init__(self, TheType):
        """
        Sets up and initialises the sockets instance
        """
   
        #Core variables and socket pointer.
        self.PortNumber = -1
        self.ServerAddress = ""
        self.Type = TheType

        #Variables for tracking status of the handler, and the socket.
        self.Verbose = True
        self.ReadyForTransmission = False
        self.Reconnected = False
        self.HandlerShouldExit = False
        self.HandlerExited = False

        #Message queues (actually lists).
        self.IncomingQueue = []
        self.OutgoingQueue = []

    # ---------- Setup Functions ----------
    def SetPortNumber(self, PortNo):
        """Sets the port number for the socket"""
        logger.debug("Socket Tools: Sockets::SetPortNumber(): Setting PortNumber to "+str(PortNo)+"...")
        self.PortNumber = PortNo

    #Only useful when creating a plug, rather than a socket.
    def SetServerAddress(self, ServerAdd):
        """Sets the server address for the socket"""
        logger.debug("Socket Tools: Sockets::SetServerAddress(): Setting ServerAddress to "+ServerAdd+"...")
        self.ServerAddress = ServerAdd

    def SetConsoleOutput(self, State):
        """Can tell us not to output any messages to console (used in server)"""
        logger.debug("Socket Tools: Sockets::SetConsoleOutput(): Setting Verbose to "+str(State)+"...")
        Verbose = State

    def StartHandler(self):
        """Starts the handler thread and then returns"""
        #Setup.
        self.ReadyForTransmission = False
        self.Reconnected = False
        self.HandlerShouldExit = False
        self.HandlerExited = False

        if self.Type in ("Plug", "Socket"):
            logger.debug("Socket Tools: Sockets::StartHandler(): Check passed, starting handler...")
            self.HandlerThread = SocketHandlerThread(self)

        else:
            logger.debug("Socket Tools: Sockets::StartHandler(): Type isn't set correctly! Throwing runtime_error...")
            raise ValueError("Type not set correctly")

    # ---------- Info getter functions ----------
    def IsReady(self):
        return self.ReadyForTransmission

    def JustReconnected(self):
        #Clear and return Reconnected.
        Temp = self.Reconnected
        self.Reconnected = False

        return Temp

    def WaitForHandlerToExit(self):
        self.HandlerThread.join()

    def HandlerHasExited(self):
        return self.HandlerExited

    # ---------- Controller Functions ----------
    def RequestHandlerExit(self):
        logger.debug("Socket Tools: Sockets::RequestHandlerExit(): Requesting handler to exit...")
        self.HandlerShouldExit = True

    def Reset(self):
        """Resets the socket to the default state."""
        logger.debug("Socket Tools: Sockets::Reset(): Resetting socket...")

        #Variables for tracking status of the other thread.
        self.ReadyForTransmission = False
        self.Reconnected = False
        self.HandlerShouldExit = False
        self.HandlerExited = False

        #Queues.
        self.IncomingQueue = []
        self.OutgoingQueue = []

        #Sockets.
        self.Socket.close()
        self.ServerSocket = ""

        logger.debug("Socket Tools: Sockets::Reset(): Done! Socket is now in its default state...")

    # ---------- Handler Thread & Functions ----------
    def CreateAndConnect(self):
        """Handles connecting/reconnecting the socket."""
        #Handle any errors while connecting.
        try:
            if self.Type == "Plug":
                logger.debug("Socket Tools: Sockets::CreateAndConnect(): Creating and connecting plug...")
                self.CreatePlug()
                self.ConnectPlug()

            elif self.Type == "Socket":
                logger.debug("Socket Tools: Sockets::CreateAndConnect(): Creating and connecting socket...")
                self.CreateSocket()
                self.ConnectSocket()

            #We are now connected.
            logger.debug("Socket Tools: Sockets::CreateAndConnect(): Done!")
            self.ReadyForTransmission = True

        except BaseException as E: #*** WHAT ERROR WOULD WE NEED TO CATCH? ***
            logger.critical("Socket Tools: Sockets::CreateAndConnect(): Error connecting: "+str(E)+". Exiting...")

            if self.Verbose:
                print("Connecting Failed!") # " << e.what() << std::endl
                print("Press ENTER to exit.")

            #Make the handler exit.
            logger.debug("Socket Tools: Sockets::CreateAndConnect(): Asking handler to exit...")
            self.HandlerShouldExit = True

    # ---------- Connection Functions (Plugs) ----------
    def CreatePlug(self):
        """Sets up the plug for us."""
        logger.info("Socket Tools: Sockets::CreatePlug(): Creating the plug...")

        self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        logger.info("Socket Tools: Sockets::CreatePlug(): Done!")

    def ConnectPlug(self): #*** ERROR HANDLING ***
        """Waits until the plug has connected to a socket."""
        logger.info("Socket Tools: Sockets::ConnectPlug(): Attempting to connect to the requested socket...")

        self.Socket.connect((self.ServerAddress, self.PortNumber))

        logger.info("Socket Tools: Sockets::ConnectPlug(): Done!")

    # ---------- Connection Functions (Sockets) ----------
    def CreateSocket(self):
        """Sets up the socket for us."""
        logger.info("Socket Tools: Sockets::CreateSocket(): Creating the socket...")

        self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ServerSocket.bind((socket.gethostname(), self.PortNumber))
        self.ServerSocket.listen(10)

        logger.info("Socket Tools: Sockets::CreateSocket(): Done!")

    def ConnectSocket(self):
        """Waits until the socket has connected to a plug."""
        logger.info("Socket Tools: Sockets::ConnectSocket(): Attempting to connect to the requested socket...")

        self.Socket = self.ServerSocket.accept()

        logger.info("Socket Tools: Sockets::ConnectSocket(): Done!")

    # --------- Read/Write Functions ----------
    def Write(self, Msg):
        """Pushes a message to the outgoing message queue so it can be written later by the handler thread."""
        logger.debug("Socket Tools: Sockets::Write(): Appending "+Msg+" to OutgoingQueue...")
        self.OutgoingQueue.append(Msg)

    def SendToPeer(self, Msg):
        """Sends the given message to the peer and waits for an acknowledgement). A convenience function.""" #*** TODO If ACK is very slow, try again *** *** Will need to change this later cos if there's a high volume of messages it might fail ***
        logger.debug("Socket Tools: Sockets::SendToPeer(): Sending message "+Msg+" to peer...")

        #Push it to the message queue.
        self.Write(Msg)

        #Wait until an \x06 (ACK) has arrived.
        logger.debug("Socket Tools: Sockets::SendToPeer(): Waiting for acknowledgement...")
        while not self.HasPendingData(): time.sleep(0.1)

        #Remove the ACK from the queue.
        logger.info("Socket Tools: Sockets::SendToPeer(): Done.")
        self.Pop()

    def HasPendingData(self):
        """Returns true if there's data on the queue to read, else false."""
        return bool(len(self.IncomingQueue))

    def Read(self):
        """Returns the item at the front of IncomingQueue."""
        logger.debug("Socket Tools: Sockets::Read(): Returning front of IncomingQueue...") 
        return self.IncomingQueue[0]

    def Pop(self):
        """Clears the front element from IncomingQueue. Prevents crash also if the queue is empty."""
        if len(self.IncomingQueue) > 0:
            logger.debug("Socket Tools: Sockets::Pop(): Clearing front element of IncomingQueue...")
            self.IncomingQueue.pop(0)

    # ---------- Other Functions ----------
    def SendAnyPendingMessages(self):
        """Sends any messages waiting in the message queue."""
        logger.debug("Socket Tools: Sockets::SendAnyPendingMessages(): Sending any pending messages...")

        try:
            #Wait until there's something to send in the queue.
            if len(self.OutgoingQueue) == 0:
                logger.debug("Socket Tools: Sockets::SendAnyPendingMessages(): Nothing to send.")
                return False

            #Write the data.
            logger.debug("Socket Tools: Sockets::SendAnyPendingMessages(): Sending data...")
            ReturnCode = self.Socket.sendall(self.OutgoingQueue[0])

            if ReturnCode == 0:
                logger.error("Socket Tools: Sockets::SendAnyPendingMessages(): Connection was closed cleanly by the peer...")
                return False #Connection closed cleanly by peer. *** HANDLE BETTER ***

            #Remove last thing from message queue.
            logger.debug("Socket Tools: Sockets::SendAnyPendingMessages(): Clearing item at front of OutgoingQueue...")
            self.OutgoingQueue.pop(0)  

        except BaseException as E:
            logger.error("Socket Tools: Sockets::SendAnyPendingMessages(): Caught unhandled exception! Error was "+static_cast<string>(err.what())+"...")
            print("Error: ", E)

        logger.debug("Socket Tools: Sockets::SendAnyPendingMessages(): Done.")
        return True

    def AttemptToReadFromSocket(self):
        """Attempts to read some data from the socket."""
        logger.debug("Socket Tools: Sockets::AttemptToReadFromSocket(): Attempting to read some data from the socket...")

        try:
            #This is a solution I found on Stack Overflow.

            logger.debug("Socket Tools: Sockets::AttemptToReadFromSocket(): Waiting for data...")

            Data = ""

            #While the socket is ready for reading, keep trying to read small packets of data.
            while select.select(self.Socket, [], [], 1)[0]:
                #Use a 1-second timeout.
                self.Socket.settimeout(1.0)

                Data += self.Socket.recv(2048)

            #Push to the message queue.
            logger.debug("Socket Tools: Sockets::AttemptToReadFromSocket(): Pushing message to IncomingQueue...")
            self.IncomingQueue.append(Data)

            logger.debug("Socket Tools: Sockets::AttemptToReadFromSocket(): Done.")

            return 0

        except BaseException as E:
            logger.error("Socket Tools: Sockets::AttemptToReadFromSocket(): Caught unhandled exception! Error was "+static_cast<string>(err.what())+"...")
            print("Error: ", E)
            return -1

class SocketHandlerThread(threading.Thread):
    def __init__(self, Socket):
        """Initialize and start the thread."""
        self.Socket = Socket

        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """Handles setup, send/receive, and maintenance of socket (reconnections)."""
        logger.debug("Socket Tools: Sockets::Handler(): Starting up...")
        Sent = -1
        ReadResult = -1

        #Setup the socket.
        logger.debug("Socket Tools: Sockets::Handler(): Calling Ptr->CreateAndConnect to set the socket up...")
        self.Socket.CreateAndConnect()

        logger.debug("Socket Tools: Sockets::Handler(): Done! Entering main loop.")

        #Keep sending and receiving messages until we're asked to exit.
        while not self.Socket.HandlerShouldExit:
            #Send any pending messages.
            Sent = self.Socket.SendAnyPendingMessages()

            #Receive messages if there are any.
            ReadResult = self.Socket.AttemptToReadFromSocket()

            #Check if the peer left.
            if ReadResult == -1:
                logger.debug("Socket Tools: Sockets::Handler(): Lost connection to peer. Attempting to reconnect...")

                if self.Socket.Verbose:
                    print("\n\nLost connection to peer. Reconnecting...")

                #Reset the socket. Also sets the tracker.
                logger.debug("Socket Tools: Sockets::Handler(): Resetting socket...")
                self.Socket.Reset()

                #Wait for the socket to reconnect or we're requested to exit.
                #Wait for 2 seconds first.
                time.sleep(2)

                logger.debug("Socket Tools: Sockets::Handler(): Recreating and attempting to reconnect the socket...")
                self.Socket.CreateAndConnect()

                #If reconnection was successful, set flag and tell user.
                if not self.Socket.HandlerShouldExit:
                    logger.debug("Socket Tools: Sockets::Handler(): Success! Telling user and re-entering main loop...")
                    self.Socket.Reconnected = True

                    if self.Socket.Verbose:
                        print("Reconnected to peer.\nPress ENTER to continue.")

        #Flag that we've exited.
        logger.debug("Socket Tools: Sockets::Handler(): Exiting as per the request...")
        self.Socket.HandlerExited = True

