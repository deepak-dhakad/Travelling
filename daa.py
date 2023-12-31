# -*- coding: utf-8 -*-
"""DAA.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1KV4CaHS4DjsAkIhqMpEqn3e3Dg15jaSo
"""

from google.colab import drive

drive.mount('/content/drive')

import pandas as pd
sample_df=pd.read_csv("/content/drive/MyDrive/data/dataset (1).csv")

sample_df.tail()

import pandas as pd
import numpy as np
import xgboost as xgb

import pickle
from geopy.geocoders import Nominatim
from sklearn.model_selection import train_test_split

pd.set_option('display.max_columns', None)

sample_df.shape

#Get latitude and longitude differences
sample_df["latitude_difference"] = sample_df["des_lat"] - sample_df["src_lat"]
sample_df["longitude_difference"] = sample_df["des_long"] - sample_df["src_long"]

sample_df["mean_travel_time"] = sample_df["mean_travel_time"].apply(lambda x: round(x/60))

import numpy as np

# Convert trip distance from longitude and latitude differences to Manhattan distance
sample_df["trip_distance"] = 0.621371 * 6371 * (
    abs(2 * np.arctan2(
        np.sqrt(np.square(np.sin((abs(sample_df["latitude_difference"]) * np.pi / 180) / 2))),
        np.sqrt(1 - np.square(np.sin((abs(sample_df["latitude_difference"]) * np.pi / 180) / 2)))
    )) +
    abs(2 * np.arctan2(
        np.sqrt(np.square(np.sin((abs(sample_df["longitude_difference"]) * np.pi / 180) / 2))),
        np.sqrt(1 - np.square(np.sin((abs(sample_df["longitude_difference"]) * np.pi / 180) / 2)))
    )))

sample_df.tail()

sample_df.describe()

sample_df.info()

sample_df = sample_df[sample_df["trip_distance"] <= 300]

sample_df.head()

sample_df.describe()

sample_df.info()

sample_df.head()

X = sample_df.drop(["mean_travel_time", "sourceid", "dstid", "source", "destination"], axis=1)
y = sample_df["mean_travel_time"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=2018)
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=2019)

#Define evaluation metric
def rmsle(y_true, y_pred):
    assert len(y_true) == len(y_pred)
    return np.square(np.log(y_pred + 1) - np.log(y_true + 1)).mean() ** 0.5

#XGBoost parameters
params = {
    'booster':            'gbtree',
    'objective':          'reg:linear',
    'learning_rate':      0.05,
    'max_depth':          14,
    'subsample':          0.9,
    'colsample_bytree':   0.7,
    'colsample_bylevel':  0.7,
    'silent':             1,
    'feval':              'rmsle'
}

nrounds = 500

#Define train and validation sets
dtrain = xgb.DMatrix(X_train, np.log(y_train+1))
dval = xgb.DMatrix(X_val, np.log(y_val+1))

#this is for tracking the error
watchlist = [(dval, 'eval'), (dtrain, 'train')]

#Train model
gbm = xgb.train(params,
                dtrain,
                num_boost_round = nrounds,
                evals = watchlist,
                verbose_eval = True
                )

#Test predictions
pred = np.exp(gbm.predict(xgb.DMatrix(X_test))) - 1

#Take a look at feature importance
feature_scores = gbm.get_fscore()
feature_scores

#This is not very telling, so let's scale the features
summ = 0
for key in feature_scores:
    summ = summ + feature_scores[key]

for key in feature_scores:
    feature_scores[key] = feature_scores[key] / summ

feature_scores

filename = "/content/drive/MyDrive/data/xgb_model.sav"
pickle.dump(gbm, open(filename, 'wb'))

