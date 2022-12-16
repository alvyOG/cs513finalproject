#Native libraries
import time
import multiprocessing as mp
import pickle
import sys
import signal
import os

#External libraries
import pandas as pd
import psutil

#Own libraries
from data_sender import sender

#CONTSANTS
TIME_STEP = 0.5

testingProcess = None

class TestData:
    def __init__(self, name, timeStep, batchSize, cpuLimit):
        self.name = name
        self.timeStep = timeStep
        self.timeStamps = []
        self.cpuUsage = []
        self.ramUsage = []
        self.runTime = 0
        self.currentTime = 0
        self.cpuLimit = cpuLimit
        self.batchSize = batchSize
        self.piPacketsPredicted = 0
        self.serverPacketsPredicted = 0

    def addUsageInfo(self, cpu, ram):
        self.timeStamps.append(self.currentTime)
        self.cpuUsage.append(cpu)
        self.ramUsage.append(ram)
        self.currentTime += self.timeStep
        
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

def runTest2(dataset, runTime, server_ip, server_port, batchSize):
    start = time.perf_counter()
    print(f"Trying to connect to {server_ip} on port {server_port}", flush=True)
    sender(str(server_ip), int(server_port), dataset, batchSize)
    end = time.perf_counter()
    runTime.value = end-start

def runTest3(dataset, model, runTime, server_ip, server_port, batchSize, cpuLimit, piPacketsPredicted, serverPacketsPredicted):
    start = time.perf_counter()
    pid = os.getpid()
    currentProcess = psutil.Process(pid=pid)
    piPackets = 0
    serverPackets = 0

    numberOfPackets = len(dataset)
    currentPacketNumber = 0
    atEndOfFile = False

    #get cpu usgage at start (will be zero)
    currentProcess.cpu_percent()
    while not atEndOfFile:
        lastPacketInBatch = currentPacketNumber + batchSize
        if lastPacketInBatch > numberOfPackets:
            lastPacketInBatch = numberOfPackets - 1
            print("Client at end of file.", flush=True)
            atEndOfFile = True

        #if too much cpu usage is seen, transition to running on remote server
        if(currentProcess.cpu_percent() / psutil.cpu_count() > cpuLimit):
            sender(server_ip, server_port, dataset[currentPacketNumber:lastPacketInBatch], batchSize)
            serverPackets += (lastPacketInBatch-currentPacketNumber)
        
        else:
            model.predict(dataset[currentPacketNumber:lastPacketInBatch])
            piPackets += (lastPacketInBatch-currentPacketNumber)
        currentPacketNumber = lastPacketInBatch

    end = time.perf_counter()
    runTime.value = end-start
    piPacketsPredicted.value = piPackets
    serverPacketsPredicted.value = serverPackets

#Reads in the csv and model
def readInFiles(datasetFilename, modelFilename):
    testData = pd.read_csv(datasetFilename)
    print("File read in.", flush=True)

    file = open(modelFilename, 'rb')
    model = pickle.load(file)
    file.close()

    xTest = testData.drop('malicious', axis=1)

    return xTest, model

#Takes a TestData object and a Pandas Datafrane, returns new dataframe
def addTestDataToDataFrame(testData, dataFrame):
    newDf = pd.DataFrame({
        f"{testData.name}_cpu(%)": testData.cpuUsage,
        f"{testData.name}_ram(MB)": testData.ramUsage,
        "TimeStamps(sec)": testData.timeStamps,
    })

    if len(testData.timeStamps) > len(dataFrame["TimeStamps(sec)"]):
        dataFrame.drop("TimeStamps(sec)", inplace=True, axis=1)
    else:
        newDf.drop("TimeStamps(sec)", inplace=True, axis=1)
        
    return pd.concat([dataFrame, newDf], axis=1)

def runTests(server_ip, server_port, xTest, model, testResultsDataFrame, testInfoDataFrame):
    global testingProcess
    runTime = mp.Value('f', 0.0, lock=False)
    piPacketsPredicted = mp.Value('i', 0, lock=False)
    serverPacketsPredicted = mp.Value('i', 0, lock=False)

    #[testname]_[batchSize]_[cpuLimit]
    tests=[
        {
            "name": "test1",
            "target": runTest1,
            "args": [xTest, model, runTime],
            "testDataObj": TestData("test1", TIME_STEP, None, None),
        
        },
        {
            "name": "test2_1000",
            "target": runTest2,
            "args": [xTest, runTime, server_ip, server_port, 1000],
            "testDataObj": TestData("test2_1000", TIME_STEP, 1000, None),
        
        },
        {
            "name": "test2_10000",
            "target": runTest2,
            "args": [xTest, runTime, server_ip, server_port, 10000],
            "testDataObj": TestData("test2_10000", TIME_STEP, 10000, None),
        
        },
        {
            "name": "test2_100000",
            "target": runTest2,
            "args": [xTest, runTime, server_ip, server_port, 100000],
            "testDataObj": TestData("test2_100000", TIME_STEP, 100000, None),
        
        },
        {
            "name": "test2_1000000",
            "target": runTest2,
            "args": [xTest, runTime, server_ip, server_port, 1000000],
            "testDataObj": TestData("test2_1000000", TIME_STEP, 1000000, None),
        
        },
        {
            "name": "test2_4637496",
            "target": runTest2,
            "args": [xTest, runTime, server_ip, server_port, 4637496],
            "testDataObj": TestData("test2_4637496", TIME_STEP, 4637496, None),
        
        },
                {
            "name": "test3_1000_40",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 1000, 40, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_1000_40", TIME_STEP, 1000, 40),
        
        },
        {
            "name": "test3_10000_40",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 10000, 40, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_10000_40", TIME_STEP, 10000, 40),
        
        },
        {
            "name": "test3_100000_40",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 100000, 40, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_100000_40", TIME_STEP, 100000, 40),
        
        },
        {
            "name": "test3_1000000_40",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 1000000, 40, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_1000000_40", TIME_STEP, 1000000, 40),
        
        },
        {
            "name": "test3_4637496_40",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 4637496, 40, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_4637496_40", TIME_STEP, 4637496, 40),
        },
        {
            "name": "test3_1000_50",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 1000, 50, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_1000_50", TIME_STEP, 1000, 50),
        
        },
        {
            "name": "test3_10000_50",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 10000, 50, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_10000_50", TIME_STEP, 10000, 50),
        
        },
        {
            "name": "test3_100000_50",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 100000, 50, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_100000_50", TIME_STEP, 100000, 50),
        
        },
        {
            "name": "test3_1000000_50",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 1000000, 50, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_1000000_50", TIME_STEP, 1000000, 50),
        
        },
        {
            "name": "test3_4637496_50",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 4637496, 50, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_4637496_50", TIME_STEP, 4637496, 50),
        },
                {
            "name": "test3_1000_60",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 1000, 60, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_1000_60", TIME_STEP, 1000, 60),
        
        },
        {
            "name": "test3_10000_60",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 10000, 60, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_10000_60", TIME_STEP, 10000, 60),
        
        },
        {
            "name": "test3_100000_60",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 100000, 60, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_100000_60", TIME_STEP, 100000, 60),
        
        },
        {
            "name": "test3_1000000_60",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 1000000, 60, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_1000000_60", TIME_STEP, 1000000, 60),
        
        },
        {
            "name": "test3_4637496_60",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 4637496, 60, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_4637496_60", TIME_STEP, 4637496, 60),
        },
                {
            "name": "test3_1000_70",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 1000, 70, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_1000_70", TIME_STEP, 1000, 70),
        
        },
        {
            "name": "test3_10000_70",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 10000, 70, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_10000_70", TIME_STEP, 10000, 70),
        
        },
        {
            "name": "test3_100000_70",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 100000, 70, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_100000_70", TIME_STEP, 100000, 70),
        
        },
        {
            "name": "test3_1000000_70",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 1000000, 70, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_1000000_70", TIME_STEP, 1000000, 70),
        
        },
        {
            "name": "test3_4637496_70",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 4637496, 70, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_4637496_70", TIME_STEP, 4637496, 70),
        },
                {
            "name": "test3_1000_80",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 1000, 80, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_1000_80", TIME_STEP, 1000, 80),
        
        },
        {
            "name": "test3_10000_80",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 10000, 80, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_10000_80", TIME_STEP, 10000, 80),
        
        },
        {
            "name": "test3_100000_80",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 100000, 80, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_100000_80", TIME_STEP, 100000, 80),
        
        },
        {
            "name": "test3_1000000_80",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 1000000, 80, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_1000000_80", TIME_STEP, 1000000, 80),
        
        },
        {
            "name": "test3_4637496_80",
            "target": runTest3,
            "args": [xTest, model, runTime, server_ip, server_port, 4637496, 80, piPacketsPredicted, serverPacketsPredicted],
            "testDataObj": TestData("test3_4637496_80", TIME_STEP, 4637496, 80),
        },
    ]

    for test in tests:
        runningTest = mp.Process(target=test["target"], args=test["args"])
        piPacketsPredicted.value = 0
        serverPacketsPredicted.value = 0

        name = test["name"]
        print(f"Starting test {name}", flush=True)
        numberOfCPUs = psutil.cpu_count()
        print(f"{numberOfCPUs} cpu's on current system.", flush=True)
        runningTest.start()
        testingProcess = psutil.Process(pid=runningTest.pid)

        #Get initial values for process usage (will be zero)
        #Also we divide by the number of CPUs becuase cpu_percent() gives the total amount over all the cpus in the system so we want to normalize it to have numbers <= 100
        test["testDataObj"].addUsageInfo(float(testingProcess.cpu_percent()/numberOfCPUs), float(testingProcess.memory_full_info().uss/1000000))
        time.sleep(TIME_STEP)

        while runningTest.exitcode == None:
            try:
                test["testDataObj"].addUsageInfo(float(testingProcess.cpu_percent()/numberOfCPUs), float(testingProcess.memory_full_info().uss/1000000))
                time.sleep(TIME_STEP)
            except Exception as e:
                continue

        runningTest.join()

        test["testDataObj"].runTime = runTime.value
        test["testDataObj"].piPacketsPredicted = piPacketsPredicted.value
        test["testDataObj"].serverPacketsPredicted = serverPacketsPredicted.value
        testResultsDataFrame = addTestDataToDataFrame(test["testDataObj"], testResultsDataFrame)
        testInfoDataFrame.loc[len(testInfoDataFrame.index)] = [test["testDataObj"].name,
            test["testDataObj"].runTime,
            test["testDataObj"].batchSize,
            test["testDataObj"].cpuLimit,
            test["testDataObj"].piPacketsPredicted,
            test["testDataObj"].serverPacketsPredicted]

    return testResultsDataFrame, testInfoDataFrame

def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: modelTesting.py [Server IP] [Server Port]")
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    mp.set_start_method('spawn')
    xTest, model = readInFiles("testset.csv", "XGboostModel.sav")

    testData = pd.DataFrame(columns=["TimeStamps(sec)"])
    testInfo = pd.DataFrame(columns=["test", "run_time", "batch_size", "cpu_limit", "pi_packets_predicted", "server_packets_predicted"])
    testData, testInfo = runTests(server_ip, server_port, xTest, model, testData, testInfo)

    #reorder columns so that the timestamps are first
    columns = list(testData.columns.values)
    columns.remove("TimeStamps(sec)")
    columns.insert(0, "TimeStamps(sec)")
    testData = testData.reindex(columns=columns)

    print("Outputting to file...")
    testData.to_csv("testData.csv", index=False)
    testInfo.to_csv("testInfo.csv", index=False)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, interruptHandler)
    signal.signal(signal.SIGTERM, interruptHandler)
    main()
    
