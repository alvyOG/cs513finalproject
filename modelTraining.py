import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

def manual_separation(bad_line):
    right_split = bad_line[:-2] + [",".join(bad_line[-2:])]
    return right_split
def training():
    trainData = pd.read_csv("trainset.csv", on_bad_lines= manual_separation, engine="python")
    testData = pd.read_csv("testset.csv", on_bad_lines= manual_separation, engine="python")

    print("Files read in.")

    sampledTrainData = trainData
    yTrain = sampledTrainData['malicious'].values
    xTrain = sampledTrainData.drop('malicious', axis=1)

    sampledTestData = testData.sample(n=10000)
    yTest = sampledTestData['malicious'].values
    xTest = sampledTestData.drop('malicious', axis=1)

    rf = RandomForestClassifier(max_depth=2, random_state=0)
    rf.fit(xTrain, yTrain)
    prediction = rf.predict(xTest)
    print(f"Random Forest Classifier Test accuracy: {accuracy_score(yTest, prediction)}")

    reg = LogisticRegression(penalty='l2')
    reg.fit(xTrain, yTrain)
    prediction = reg.predict(xTest)
    print(f"Logistic Regression Test accuracy: {accuracy_score(yTest, prediction)}")