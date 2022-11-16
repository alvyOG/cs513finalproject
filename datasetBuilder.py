import pandas as pd
import numpy as np

def manual_separation(bad_line):
    right_split = bad_line[:-2] + [",".join(bad_line[-2:])]
    return right_split

def labeling():
    trainingData_unlabeled = pd.read_csv("trainset_unlabeled.csv", on_bad_lines= manual_separation, engine="python")
    testingData_unlabeled = pd.read_csv("testset_unlabeled.csv", on_bad_lines= manual_separation, engine="python")

    print("Files read in")

    trainingData_unlabeled = trainingData_unlabeled.dropna()
    testingData_unlabeled = testingData_unlabeled.dropna()

    print("na's dropped")

    maliciousIps = ["192.168.2.112", "198.164.30.2", "192.168.2.113", "192.168.2.112", "147.32.84.180",
    "147.32.84.140", "10.0.2.15", "172.16.253.130", "172.16.253.240", "192.168.3.35", "172.29.0.116",
    "192.168.248.165", "131.202.243.84", "192.168.2.110", "192.168.1.103", "192.168.2.109", "147.32.84.170",
    "147.32.84.130", "192.168.106.141", "172.16.253.131", "74.78.117.238", "192.168.3.25", "172.29.0.109",
    "10.37.130.4", "192.168.5.122", "192.168.4.118", "192.168.4.120", "192.168.2.105", "147.32.84.150",
    "147.32.84.160", "192.168.106.131", "172.16.253.129", "158.65.110.24", "192.168.3.65", "172.16.253.132"]

    #1 for malicious and 0 for benign
    def label(row):
        if row["ip.src"] in maliciousIps or row["ip.dst"] in maliciousIps:
            return 1
        else:
            return 0

    trainingData_unlabeled['malicious'] = trainingData_unlabeled.apply(lambda row: label(row), axis=1)
    testingData_unlabeled['malicious'] = testingData_unlabeled.apply(lambda row: label(row), axis=1)

    print("labels added")

    print(trainingData_unlabeled)
    print(testingData_unlabeled)

    trainingData_unlabeled.to_csv("trainset_labeled.csv", index=False)
    testingData_unlabeled.to_csv("testset_labeled.csv", index=False)

    print("Send out to file")

