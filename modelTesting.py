import pandas as pd
import pickle

def test(filename):
    testData = pd.read_csv("testset.csv")
    print("File read in.")

    file = open(filename, 'rb')
    model = pickle.load(file)
    file.close()

    yTest = testData['malicious'].values
    xTest = testData.drop('malicious', axis=1)
    prediction = model.score(xTest, yTest)
    print(prediction)

test("XGBoostModel.sav")
