import pandas as pd
import pickle
import os

import time
import psutil
import multiprocessing as mp

def runTest(dataset, model, runTime):
    start = time.perf_counter()
    model.predict(dataset)
    end = time.perf_counter()
    runTime.value = end-start

def readInFile(filename):
    testData = pd.read_csv("testset.csv")
    print("File read in.")

    file = open(filename, 'rb')
    model = pickle.load(file)
    file.close()

    xTest = testData.drop('malicious', axis=1)

    runTime = mp.Value('f', 0.0)
    runningTest = mp.Process(target=runTest, args=(xTest, model, runTime))
    runningTest.start()
    process = psutil.Process(pid=runningTest.pid)

    while runningTest.exitcode == None:
        print(f'Parent: {os.getpid()}. Child usage: {process.cpu_percent()}.')
        time.sleep(0.1)

    runningTest.join()
    print(f'Process runtime: {runTime.value}')

if __name__ == '__main__':
    mp.set_start_method('spawn')
    readInFile("XGboostModel.sav")
