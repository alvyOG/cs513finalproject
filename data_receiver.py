import sys
import socket
import signal
import pandas as pd
import pickle
import os
import time
import psutil
import multiprocessing as mp
from io import BytesIO

RECV_BUFFER_SIZE = 4096
QUEUE_LENGTH = 10
isBreak = False

# Need a kill signal handler to prevent server from going down unless killed
def breakHandler(signum,frame):
    global isBreak
    isBreak = True

def runPrediction(dataset, model, runTime):
    start = time.perf_counter()
    model.predict(dataset)
    end = time.perf_counter()
    runTime.value = end-start

def initModel(filename):
    file = open(filename, 'rb')
    model = pickle.load(file)
    file.close()
    return model

def runTest(model, datajson):
    testData = pd.read_json(datajson)
    runTime = mp.Value('f', 0.0)
    runningPrediction = mp.Process(target=runPrediction, args=(testData, model, runTime))
    runningPrediction.start()
    process = psutil.Process(pid=runningPrediction.pid)

    while runningPrediction.exitcode == None:
        print(f'Parent: {os.getpid()}. Child usage: {process.cpu_percent()}.')
        time.sleep(0.1)

    runningPrediction.join()
    print(f'Process runtime: {runTime.value}')

def server(server_ip, server_port, model):
    # Open socket
    HOST = server_ip
    PORT = server_port
    global isBreak
    signal.signal(signal.SIGINT, breakHandler)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind on port and listen for messages
    s.bind((HOST, PORT))
    s.listen(QUEUE_LENGTH)
    # While not receiving a kill signal do:
    while not isBreak:
        # Accept next connection
        (c, addr) = s.accept()
        # While connected
        while True:
            # Receive data on the socket until no data left or buffer full
            data = c.recv(RECV_BUFFER_SIZE)
            datajson = pd.read_csv(BytesIO(data), names=[
                "ip.src",
                "ip.dst",
                "ip.proto",
                "frame.len",
            ])
            if not data:
                break
            else:
                runTest(model, datajson)
        # Close connection once all the data is read from that connection
        c.close()
    # Close the socket when server receives a kill signal
    s.close()
    
def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: data_receiver.py [Server IP] [Server Port]")
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    model = initModel("XGboostModel.sav")
    mp.set_start_method('spawn')
    server(server_ip, server_port, model)

if __name__ == "__main__":
    main()
