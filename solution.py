from audioop import avg
import errno
from socket import *
import os
from statistics import stdev
import sys
import struct
import time
import select
import binascii
# Should use stdev

ICMP_ECHO_REQUEST = 8


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + (string[len(string) - 1])
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receiveOnePing(mySocket, ID, timeout, destAddr):
    global packageRev, timeRTT
    timeLeft = timeout

    while 1:
       startedSelect = time.time()
    whatReady = select.select([mySocket], [], [], timeLeft)
    howLongInSelect = (time.time() - startedSelect)
    if whatReady[0] == []: # Timeout
        return "0: Request timed out."
    timeReceived = time.time()
    recPacket, addr = mySocket.recvfrom(1024)
   #Fill in start
   #Fetch the ICMP header from the IP packet
    icmph = recPacket[20:28]
    type, code, checksum, pID, sq = struct.unpack("bbHHh", icmph)  
    #print("The header received in the ICMP reply is ",type, code, checksum, pID, sq)
    if pID == ID:
        bytesinDbl = struct.calcsize("d")
        timeData = struct.unpack("d", recPacket[28:28 + bytesinDbl])[0]
        timeRTT.append(timeReceived - timeData)
        packageRev += 1
        return timeReceived - timeData
    else:
        return "ID is different."   
  # Fill in end
    timeLeft = timeLeft - howLongInSelect
    if timeLeft <= 0: 
        return"1: Request timed out."

def sendOnePing(mySocket, destAddr, ID):
    global packageSent
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0
    # Make a dummy header with a 0 checksum
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)
    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
            # Convert 16-bit integers from host to network  byte order
            myChecksum = htons(socket(myChecksum) & 0xffff)
    else:
            myChecksum = htons(myChecksum)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))  
    # AF_INET address must be tuple, not str
    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.

def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")
    errno = 1
    msg = " Not pinging"
    # SOCK_RAW is a powerful socket type. For more details:   http://sockraw.org/papers/sock_raw
    # FIll in start
    # Create Socket here
    try:
        mySocket = socket.setsockopt(socket.AF_INET, socket.SOCK_RAW, icmp)
    except error (errno, msg):    
        if errno == 1:
            raise socket.error(msg)
    #Fill in end
    ID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, ID)
    delay = receiveOnePing(mySocket, ID, timeout, destAddr)
    mySocket.close()
    return delay


def ping(host, timeout=1):
    # timeout=1 means: If one second goes by without a reply from the server,  	# the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    # Calculate vars values and return them
    # Send ping requests to a server separated by approximately one second
    while 1 :
        delay = doOnePing(dest, timeout)
        print("RTT:",delay)
        print("maxRTT:", (max(timeRTT) if len(timeRTT) > 0 else 0), "\timeRTT:", (min(timeRTT) if len(timeRTT) > 0 else 0), "\naverageRTT:", float(sum(timeRTT)/len(timeRTT) if len(timeRTT) > 0 else float("nan")))
        print("Package Lose Rate:" , ((packageSent - packageRev)/packageSent if packageRev > 0 else 0))
        time.sleep(1)  # one second 
    return delay

if __name__ == '__main__':
    ping("google.co.il")