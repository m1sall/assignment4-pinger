from socket import *
import os
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
        csum = csum + (str[len(str) - 1])
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def receiveOnePing(mySocket, ID, timeout, destAddr):
    global rtt_min, rtt_max, rtt_sum, rtt_cnt
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        rtt = timeReceived - send_time
        if whatReady[0] == []: # Timeout duration
            return "0: Request timed out, oops!,"
        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)
        #Fill in start
        #Fectch the ICMP header from the IP packet
        type, code, checksum, id, sequence = struct.unpack('bbHHh',recPacket[20:28])
        if type != 0:
            return'expected type=0, but got {}'.format(type)
        if code != 0:
            return 'expected type=0, but got {}'.format(code)
        if ID != id:
            return 'expected type=0, but got {}'.format(ID, id)
        send_time, = struct.unpack('d', recPacket[28:])

        rtt = (timeReceived - send_time) * 1000
        rtt_cnt += 1
        rtt_sum += rtt
        rtt_min = min(rtt_min, rtt)
        rtt_max = max(rtt_max, rtt)

        ip_header =struct.unpack('!BBHHHBBH4s4s' , recPacket[:20])
        ttl = ip_header[5]
        saddr = socket.inet_ntoa(ip_header[8])
        length = len(recPacket) - 20
        return '{} bytes from {}: icmp_sequence={} ttl={} time+{:.3f} ms'.format(length, saddr, sequence, ttl, rtt)
        
        #Fill in end
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out, oops!."

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
        #Convert 16-bit integers from host to network byte order.

    if sys.platform == 'darwin':
        myChecksum = htons(myChecksum) & 0xffff
    else:
       myChecksum = socket.htons(myChecksum)
    
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))
    # AF_INET address must be tuple, not str
    #Both LISTS and TUPLES consist of a number of objects
    #which can be referenced by their position number within the object
def doOnePing(destAddr, timeout):
    ICMP = socket.getprotobyname("icmp")
    #SOCK_RAW is a powerful socket type. For more details see:http://sock-raw.org/papers/sock_raw
    #Fill in start
    #Create Socket here
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, ICMP)
    #Fill in end
    myID = os.getpid() & 0xFFFF  #Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    
    mySocket.close()
    return delay

def ping(host, timeout=1):
    # timeout=1 means: If one second goes by without a reply from the server,  	# the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    # Calculate vars values  and returm them
        
    # Send ping requests to a server separated by approximately one second
    list = []*1000
    for i in range(0,4):

        delay = doOnePing(dest, timeout)
        print(delay)
        list.append(0)
        time.sleep(1)  # Time to sleep equals one second
        
    packet_min = min(list)*1000
    packet_max = max(list)*1000
    packet_avg = statistics.mean(list)*1000
    stdev_var = (list)*1000
    vars = ([str(round(packet_min, 2)), str(round(packet_avg, 2)), str(round(packet_max, 2)),str(round(statistics.stdev(stdev_var), 2))])
      
    return vars

if __name__ == '__main__':
    ping("google.co.il")