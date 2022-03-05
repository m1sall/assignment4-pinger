from socket import *
import os
from statistics import stdev
import statistics
import sys
import struct
import time
import select
import binascii
import socket
ICMP_ECHO_REQUEST = 8
timeRTT = []
packageSent =0;
packageRev = 0;
def checksum(str):
    csum = 0
    countTo = (len(str) / 2) * 2
    count = 0
    while count < countTo:
        thisVal = (str[count+1]) * 256 + (str[count])
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
    if countTo < len(str):
        csum = csum + ord(str[len(str) - 1])
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer
def receiveOnePing(mySocket, ID, timeout, destAddr):
    global packageRev,timeRTT
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout
            return "Request timed out."
        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)
        #Fill in start
        #Fetch the ICMP header from the IP packet
        icmpHeader = recPacket[20:28]
        requestType, code, revChecksum, revId, revSequence = struct.unpack('bbHHh',icmpHeader)
        if ID == revId:
            bytesInDouble = struct.calcsize('d')
            timeData = struct.unpack('d',recPacket[28:28 + bytesInDouble])[0]
            timeRTT.append(timeReceived - timeData)
            packageRev += 1
            return timeReceived - timeData
        else:
            return "ID is not the same!"
        #Fill in end
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "1: Destination Host Unreachable."
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
        myChecksum = socket.htons(myChecksum) & 0xffff
        #Convert 16-bit integers from host to network byte order.
    else:
        myChecksum = socket.htons(myChecksum)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))
    packageSent += 1
     # AF_INET address must be tuple, not str
    #Both LISTS and TUPLES consist of a number of objects
    #which can be referenced by their position number within the object
def doOnePing(destAddr, timeout):
    icmp = socket.getprotobyname("icmp")
    #SOCK_RAW is a powerful socket type. For more details see:http://sock-raw.org/papers/sock_raw
    #Fill in start
    #Create Socket here
    errno = 1
    msg = "Not pinging"
    try:
        mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    except error (errno, msg):
        if errno == 1:
            raise socket.error(msg)
    #Fill in end
    myID = os.getpid() & 0xFFFF  #Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay
def ping(host, timeout=1):
    global rtt_min, rtt_max, rtt_sum, rtt_cnt
    rtt_min = float('+inf')
    rtt_max = float('-inf')
    rtt_sum = 0
    rtt_cnt = 0
    cnt = 0
    #timeout=1 means: If one second goes by without a reply from the server,
    #the client assumes that either the client's ping or the server's pong is lost
    dest = socket.gethostbyname(host)
    print ("Pinging " + dest + " using Python:")
    #Send ping requests to a server separated by approximately one second
    try:
        while True:
            cnt += 1
            print (doOnePing(dest, timeout))
            time.sleep(1)
    except KeyboardInterrupt:
        if cnt != 0:
            print ('--- {} ping statistics ---').format(host)
            print ('{} packets transmitted, {} packets received, {:.1f}% packet loss').format(cnt, rtt_cnt, 100.0 - rtt_cnt * 100.0 / cnt)
            if rtt_cnt != 0:
                print ('round-trip min/avg/max {:.3f}/{:.3f}/{:.3f} ms').format(rtt_min, rtt_sum / rtt_cnt, rtt_max)

    return vars

if __name__ == '__main__':
    ping("google.co.il")