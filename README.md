# Examining the Effectiveness of Pre-Trained Machine Learning Models for Botnet Detection in IoT and the Cloud
## Project description
This repository contains the code written to complete the semester long research assignment for CS513 Networks at Worcester Polytechnic Institute in the Fall of 2022.
## How to run
This project contains a few dependences that you will need in able to run:
1. pandas
2. numpy
3. sklearn
4. scipy
5. xgboost
6. scikit-learn

We have provided our train and test datasets in trainset.zip and trainset.zip, respectively. You will need to unzip them and keep them in the project directory.
modelTesting.py contains the code to run all of our defined tests. Since experiments 2 and 3 require the use of a server and ip and port should be provided as such:

>python modelTesting.py [ip] [port]

The server will also need to be started in the same way. That can be done using:

>python data_receiver.py [ip] [port]

The output of running the tests will be 2 csv files. The first is testData.csv which provides all the measured CPU and memory usage during the tests. The second is testInfo.csv which provides information regarding what the setup of each test was like.
