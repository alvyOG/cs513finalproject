import signal, sys
import socket
import signal
import pandas as pd
import pickle
import multiprocessing as mp
import struct

RECV_BUFFER_SIZE = 4096
QUEUE_LENGTH = 10

openSocket = None
openConnection = None

# Need a ignal handler to prevent server from going down unless killed
def interruptHandler(signal, frame):
    global openSocket
    global openConnection

    print("Closing data_receiver.py...", flush=True)
    if openSocket:
        openSocket.close()
    if openConnection:
        openConnection.close()

    sys.exit(0)

def runPrediction(dataset, model):
    model.predict(dataset)

def initModel(filename):
    file = open(filename, 'rb')
    model = pickle.load(file)
    file.close()
    return model

def receiveMessage(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen)

def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def server(server_ip, server_port, model):
    global openSocket
    global openConnection

    # Open socket
    HOST = server_ip
    PORT = server_port
    openSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind on port and listen for messages
    openSocket.bind((HOST, PORT))
    openSocket.listen(QUEUE_LENGTH)

    # Accept next connection
    while True:
        packetsClassified = 0
        (openConnection, addr) = openSocket.accept()
        print("Server received connection!", flush=True)
        # While connected
        while True:
            # Receive data on the socket until no data left or buffer full
            data = receiveMessage(openConnection)
            if data == None:
                break
            packets = pickle.loads(data)
            packetsClassified += len(packets)
            #print("Server running prediction.", flush=True)
            runPrediction(packets, model)
            #print("Server sending data back.", flush=True)
            openConnection.sendall(b"done!")

        openConnection.close()
        print(f"{packetsClassified} packets classified", flush=True)
    
def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: data_receiver.py [Server IP] [Server Port]")
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    print(f"Starting up server on {server_ip} on port {server_port}", flush=True)
    model = initModel("XGboostModel.sav")
    server(server_ip, server_port, model)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, interruptHandler)
    signal.signal(signal.SIGTERM, interruptHandler)
    main()
