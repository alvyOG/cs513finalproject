import socket
import pickle
import sys
import signal
import struct

BUFFER_SIZE = 2048

openSocket = None

def interruptHandler(signal, frame):
    global openSocket

    print("Closing data_sender.py...", flush=True)
    if openSocket:
        openSocket.close()

    sys.exit(0)

def sendMessage(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def sender(server_ip, server_port, dataset, batch_size):
    global openSocket

    #set signal handlers
    signal.signal(signal.SIGINT, interruptHandler)
    signal.signal(signal.SIGTERM, interruptHandler)

    #Open socket
    HOST = server_ip
    PORT = server_port
    openSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Check for connection, keep client up and continue checking if not
    connected = False
    while not connected:
        try:
            openSocket.connect((HOST, PORT))
            connected = True
            print("Client made connection!", flush=True)
        except Exception as e:
            pass

    # When connected, open data set and send batches
    atEndOfFile = False
    numberOfPackets = len(dataset)
    print(f"Number of packets to send: {numberOfPackets}", flush=True)
    currentPacketNumber = 0

    while not atEndOfFile:
        lastPacketInBatch = currentPacketNumber + batch_size
        if lastPacketInBatch > numberOfPackets:
            lastPacketInBatch = numberOfPackets - 1
            print("Client at end of file.", flush=True)
            atEndOfFile = True

        dataToSend = dataset[currentPacketNumber:lastPacketInBatch]
        binary = pickle.dumps(dataToSend)
        #send out message
        #print("Client sending packet batch.", flush=True)
        sendMessage(openSocket, binary)

        #wait for a response back
        #print("Client waiting for response back.", flush=True)

        try:
            openSocket.recv(BUFFER_SIZE)
        except Exception as e:
            interruptHandler(None, None)

        #print("Client got response back.", flush=True)
        currentPacketNumber = lastPacketInBatch

    # close the socket when done sending
    print("Client closing connection.", flush=True)
    openSocket.close()
