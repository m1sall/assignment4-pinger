from audioop import avg
from email import header
from socket import *
import os
from statistics import stdev
import statistics
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
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout
            return "Request timed out."
        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)
        #Fetch the ICMP header from the IP packet
        header = recPacket[20:28]
        type, code, checksum, packID, seqNo = struct.unpack("bbHHh", header)
        if type == 0 and packID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent =struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            ttls = struct.unpack("c", recPacket[8:9])[0]
            rtt = timeReceived - timeSent
            return(rtt, ttls)

        timeLeft = timeLeft -howLongInSelect
        if timeLeft <= 0:
            return "Oops, Request timed out."

def sendOnePing(mySocket, destAddr, ID):
    global packageSent
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0
    # Make a dummy header with a 0 checksum.
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)
    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':    
    #Convert 16-bit integers from host to network byte order.
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))
    packageSent = 1
     # AF_INET address must be tuple, not str
    #Both LISTS and TUPLES consist of a number of objects
    #which can be referenced by their position number within the object
def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")

    # SOCK_RAW is a powerful socket type. For more details:   http://sockraw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)
    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay

def ping(host, timeout=1):
    #timeout=1 means: If one second goes by without a reply from the server,
    dest = gethostbyname(host)
    # print ("Pinging:" + dest + " using Python:")
    # print ("")
    # Calculate vars values and return them
    count = 0
    val = []
    #Send ping requests to a server separated by approximately one second
    for i in range(0,4):
        delay = doOnePing(dest, timeout)
        val.append(delay[0])
       # Print delay
        time.sleep(1)# one second
    print(val)
    if len(val) > 0:
        packet_min = min(val) * 1000
        packet_avg = sum(val) / len(val) * 1000
        packet_max = max(val) * 1000
        stdev_var = list(val) * 1000
        vars = [str(round(packet_min, 2)), str(round(packet_avg, 2)), str(round(packet_max, 2)), str(round(statistics.stdev(stdev_var),2))]
    else:
        vars = ['0', '0.0', '0', '0.0']
    
    return vars

if __name__ == '__main__':
    ping("google.co.il")