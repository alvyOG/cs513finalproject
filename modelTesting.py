import pandas as pd
import pickle
import time
import psutil
import multiprocessing as mp
import sys
import signal

from data_sender import sender

testingProcess = None

def interruptHandler(signal, frame):
    global testingProcess
    testingProcess.terminate()
    print("Closing modelTesting.py...", flush=True)
    
    sys.exit(0)

def runTest1(dataset, model, runTime):
    start = time.perf_counter()
    model.predict(dataset)
    end = time.perf_counter()
    runTime.value = end-start

def runTest2(dataset, model, runTime, server_ip, server_port):
    start = time.perf_counter()
    print(f"Trying to connect to {server_ip} on port {server_port}", flush=True)
    sender(str(server_ip), int(server_port), dataset, 10000)
    end = time.perf_counter()
    runTime.value = end-start

#Reads in the csv and model
def readInFiles(datasetFilename, modelFilename):
    testData = pd.read_csv(datasetFilename)
    print("File read in.", flush=True)

    file = open(modelFilename, 'rb')
    model = pickle.load(file)
    file.close()

    xTest = testData.drop('malicious', axis=1)

    return xTest, model

def main():
    global testingProcess

    if len(sys.argv) != 3:
        sys.exit("Usage: modelTesting.py [Server IP] [Server Port]")
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    mp.set_start_method('spawn')
    xTest, model = readInFiles("testset.csv", "XGboostModel.sav")

    tests=["runTest2"]

    for test in tests:
        runTime = mp.Value('f', 0.0)
        runningTest = None

        if test == "runTest2":
            runningTest = mp.Process(target=runTest2, args=(xTest, model, runTime, server_ip, server_port))

        print(f"Starting test {test}", flush=True)
        print(f"{psutil.cpu_count()} cpu's on current system.")
        runningTest.start()
        testingProcess = psutil.Process(pid=runningTest.pid)

        while runningTest.exitcode == None:
            print(f'Child CPU usage: {testingProcess.cpu_percent()}.', flush=True)
            print(f'Child memory usage: {testingProcess.memory_full_info().uss}.', flush=True)
            time.sleep(0.5)

        runningTest.join()
        print(f'Process runtime: {runTime.value}', flush=True)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, interruptHandler)
    signal.signal(signal.SIGTERM, interruptHandler)
    main()
    
