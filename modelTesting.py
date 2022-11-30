import pandas as pd
import pickle

def test(filename):
    testData = pd.read_csv("testset.csv")
    print("File read in.")

    file = open(filename, 'rb')
    model = pickle.load(file)
    file.close()

    xTest = testData.drop('malicious', axis=1)

    prediction = model.predict(xTest)
    print(prediction)

test("XGBoostModel.sav")
