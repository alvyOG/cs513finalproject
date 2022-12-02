import pandas as pd
import pickle

import time

def test(filename):
    testData = pd.read_csv("testset.csv")
    print("File read in.")

    file = open(filename, 'rb')
    model = pickle.load(file)
    file.close()

    xTest = testData.drop('malicious', axis=1)

    start = time.perf_counter()
    prediction = model.predict(xTest)
    end = time.perf_counter()
    print(prediction)
    print(end-start)

test("XGboostModel.sav")
