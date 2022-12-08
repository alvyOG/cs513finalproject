import pandas as pd
import pickle
import time
import psutil
import multiprocessing as mp
import sys
import signal

from data_sender import sender

#CONTSANTS
TIME_STEP = 0.5

testingProcess = None

class TestData:
    def __init__(self, name, timeStep):
        self.name = name
        self.timeStep = timeStep
        self.timeStamps = []
        self.cpuUsage = []
        self.ramUsage = []
        self.runTime = 0
        self.currentTime = 0

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

def runTests(server_ip, server_port, xTest, model, dataFrame):
    global testingProcess
    runTime = mp.Value('f', 0.0)

    #[testname]_[batchSize]
    tests=[
        {
            "name": "test1",
            "target": runTest1,
            "args": [xTest, model, runTime],
            "testDataObj": TestData("test1", TIME_STEP),
        
        },
        {
            "name": "test2_1000",
            "target": runTest2,
            "args": [xTest, runTime, server_ip, server_port, 1000],
            "testDataObj": TestData("test2_1000", TIME_STEP),
        
        },
        {
            "name": "test2_10000",
            "target": runTest2,
            "args": [xTest, runTime, server_ip, server_port, 10000],
            "testDataObj": TestData("test2_10000", TIME_STEP),
        
        },
        {
            "name": "test2_100000",
            "target": runTest2,
            "args": [xTest, runTime, server_ip, server_port, 100000],
            "testDataObj": TestData("test2_100000", TIME_STEP),
        
        },
        {
            "name": "test2_1000000",
            "target": runTest2,
            "args": [xTest, runTime, server_ip, server_port, 1000000],
            "testDataObj": TestData("test2_1000000", TIME_STEP),
        
        },
        {
            "name": "test2_4637496",
            "target": runTest2,
            "args": [xTest, runTime, server_ip, server_port, 4637496],
            "testDataObj": TestData("test2_4637496", TIME_STEP),
        
        },
    ]

    for test in tests:
        runningTest = mp.Process(target=test["target"], args=test["args"])

        name = test["name"]
        print(f"Starting test {name}", flush=True)
        numberOfCPUs = psutil.cpu_count()
        print(f"{numberOfCPUs} cpu's on current system.")
        runningTest.start()
        testingProcess = psutil.Process(pid=runningTest.pid)

        #Get initial values for process usage (will be zero)
        #Also we divide by the number of CPUs becuase cpu_percent() gives the total amount over all the cpus in the system so we want to normalize it to have numbers <= 100
        test["testDataObj"].addUsageInfo(float(testingProcess.cpu_percent()/numberOfCPUs), float(testingProcess.memory_full_info().uss/1000000))
        time.sleep(TIME_STEP)

        while runningTest.exitcode == None:
            test["testDataObj"].addUsageInfo(float(testingProcess.cpu_percent()/numberOfCPUs), float(testingProcess.memory_full_info().uss/1000000))
            time.sleep(TIME_STEP)

        runningTest.join()
        test["testDataObj"].runTime = runTime.value
        dataFrame = addTestDataToDataFrame(test["testDataObj"], dataFrame)

        #I am not sure where to add the run time to the data frame so I will print it here.
        print(f"{name} run time: {runTime.value}")

    return dataFrame

def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: modelTesting.py [Server IP] [Server Port]")
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    mp.set_start_method('spawn')
    xTest, model = readInFiles("testset.csv", "XGboostModel.sav")

    testData = pd.DataFrame(columns=["TimeStamps(sec)"])
    testData = runTests(server_ip, server_port, xTest, model, testData)

    #reorder columns so that the timestamps are first
    columns = list(testData.columns.values)
    columns.remove("TimeStamps(sec)")
    columns.insert(0, "TimeStamps(sec)")
    testData = testData.reindex(columns=columns)

    testData.to_csv("testData.csv", index=False)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, interruptHandler)
    signal.signal(signal.SIGTERM, interruptHandler)
    main()
    
