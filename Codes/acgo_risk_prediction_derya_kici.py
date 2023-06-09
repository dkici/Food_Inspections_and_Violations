# -*- coding: utf-8 -*-
"""ACGO_Risk_Prediction_Derya_Kici.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1WyhXnr_pTvoKeC6O5YZjWVAuR--CbU8n

# Alcohol and Gaming Commission of Ontario 

Senior Data Scientist Technical Assessment

Derya Kici, June 1, 2023
"""

# !pip install imblearn

"""Develop a predictive model using the given dataset on Chicago restaurant inspections. The aim is to identify establishments at a higher risk of violations"""

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import missingno as msno

from collections import Counter
from multiprocessing import Pool
from random import sample
import time

import sklearn
from sklearn import model_selection, preprocessing, feature_selection, ensemble, linear_model, metrics, decomposition
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.utils import resample

import imblearn
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.under_sampling import NearMiss
from imblearn.over_sampling import SMOTE

from keras.models import Sequential
from keras.layers import Dense
from keras.wrappers.scikit_learn import KerasClassifier
from keras.utils import np_utils

from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestRegressor

from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report

from google.colab import drive
drive.mount("/content/gdrive", force_remount=True)

"""# Load Data"""

# data = pd.read_csv("C:\\Users\\derya\\Desktop\\AGCO Pre-Interview Assessment\\data\\Food Inspections and Violations.csv")
data = pd.read_csv("/content/gdrive/MyDrive/AGCO Pre-Interview Assessment/data/Food Inspections and Violations.csv")
data.head()

data = data.dropna()
len(data[data["Violations"].isna()])

data.isnull().sum()

columns = ["Inspection ID", "Facility Type", "Risk",  "Inspection Type", "Violations"]
df = data[columns].copy()
df.head()

"""# Data Preprocessing

There exists multiple violation codes for some restaurants, then I need to seperate the violan codes from this Violation column. The violations are listed in the same column by using '|".
"""

df2 = df.join(df['Violations'].str.split('|',expand = True).add_prefix('Violations_')) 
df2 = df2.drop(columns = {"Violations"})
df2 = df2.melt(id_vars=["Inspection ID","Facility Type","Risk","Inspection Type"], 
        var_name="viol", 
        value_name="Violation_id")
df2 = df2.drop(columns = {'viol'})
df2 = df2.dropna(subset = 'Violation_id')
df2['Violation_id'] = (df2['Violation_id'].str.rsplit('.')).str[0]
df2["Violation_id"] = df2["Violation_id"].str.strip()
df2.head(2)

df2.isnull().sum()

"""I will also split the date in to components as day, month, and year"""

# df2["Month"] = df2["Inspection Date"].astype(str).str[:2]
# df2["Day"] = df2["Inspection Date"].astype(str).str[3:5]
# df2["Year"] = df2["Inspection Date"].astype(str).str[-4:]
# df2 = df2.drop(columns={"Inspection Date"})
# df2

"""# Balance The Data"""

df2["Violation_id"] = "Violation_" + df2["Violation_id"] 
df2

df_encoded = pd.get_dummies(df2, columns = ['Violation_id'])
df_encoded.columns = df_encoded.columns.str.removeprefix("Violation_id_")

df_encoded = pd.get_dummies(df_encoded, columns = ['Facility Type'])
# df_encoded.columns = df_encoded.columns.str.removeprefix("Facility Type")

df_encoded = pd.get_dummies(df_encoded, columns = ['Inspection Type'])
# df_encoded.columns = df_encoded.columns.str.removeprefix("Inspection Type")

# df_encoded = pd.get_dummies(df_encoded, columns = ['Year'])

# df_encoded = pd.get_dummies(df_encoded, columns = ['Month'])

# df_encoded = pd.get_dummies(df_encoded, columns = ['Day'])
df_encoded.head()

df_encoded.set_index("Inspection ID", inplace = True)
df_encoded

df_encoded.columns

## split data
df_train, df_test = model_selection.train_test_split(df_encoded, 
                      test_size=0.3)

df_train['Risk'] = df_train['Risk'].map({'Risk 1 (High)':1, 'Risk 2 (Medium)':2, 'Risk 3 (Low)':3})                  
df_train
df_test['Risk'] = df_test['Risk'].map({'Risk 1 (High)':1, 'Risk 2 (Medium)':2, 'Risk 3 (Low)':3})                   
df_test

df_train.shape, df_test.shape

"""# Feature Selection"""

#borrowed from https://towardsdatascience.com/machine-learning-with-python-classification-complete-tutorial-d2c99dc524ec
X = df_train.iloc[:,1:]
y = df_train.iloc[:,0]
feature_names = df_train.columns[1:].tolist()
## Importance
model = ensemble.RandomForestClassifier(n_estimators=100,
                      criterion="entropy", random_state=0)
model.fit(X,y)
importances = model.feature_importances_
## Put in a pandas dtf
df_importances = pd.DataFrame({"IMPORTANCE":importances, 
            "VARIABLE":feature_names}).sort_values("IMPORTANCE", 
            ascending=False)
df_importances['cumsum'] = df_importances['IMPORTANCE'].cumsum(axis=0)
df_importances = df_importances.set_index("VARIABLE")
    
## Plot
fig, ax = plt.subplots(nrows=1, ncols=2, sharex=False, sharey=False)
fig.suptitle("Features Importance", fontsize=18)
ax[0].title.set_text('variables')
df_importances[["IMPORTANCE"]].sort_values(by="IMPORTANCE").plot(kind="barh", legend=False, ax=ax[0]).grid(axis="x")
ax[0].set(ylabel="")
ax[1].title.set_text('cumulative')
df_importances[["cumsum"]].plot(kind="line", linewidth=4, 
                                 legend=False, ax=ax[1])
ax[1].set(xlabel="", xticks=np.arange(len(df_importances)), 
          xticklabels=df_importances.index)
plt.xticks(rotation=70)
plt.grid(axis='both')
plt.show()

imp_features = df_importances[df_importances["cumsum"]<=0.9]
imp_features

imp_features.shape

imp_features.index

# X_names = ['Risk','Facility Type_Grocery Store', 'Facility Type_Restaurant',
#        'Inspection Type_Canvass', 'Violation_35', 'Violation_38',
#        'Violation_34', 'Violation_33', 'Year_2014', 'Year_2013',
#        'Inspection Type_License', 'Year_2015', 'Violation_32',
#        'Facility Type_Liquor', 'Year_2012', 'Year_2016', 'Year_2011',
#        'Inspection Type_Canvass Re-Inspection', 'Month_08',
#        'Facility Type_Bakery', 'Inspection Type_License Re-Inspection',
#        'Violation_41', 'Month_11', 'Month_07', 'Month_12', 'Month_09',
#        'Month_05', 'Inspection Type_Complaint', 'Month_10', 'Month_06',
#        'Violation_36', 'Month_04', 'Month_03', 'Day_14', 'Day_21', 'Day_17',
#        'Day_16', 'Inspection Type_Short Form Complaint', 'Day_15', 'Day_09',
#        'Month_01', 'Day_19', 'Violation_18', 'Day_05', 'Day_28', 'Day_18',
#        'Facility Type_School', 'Day_10', 'Day_06', 'Day_22', 'Day_23',
#        'Day_08', 'Day_07', 'Day_24', 'Month_02', 'Day_13', 'Day_20', 'Day_27',
#        'Day_03', 'Day_11', 'Day_29', 'Day_26', 'Day_02', 'Violation_40',
#        'Day_04', 'Day_25', 'Day_30', 'Day_12', 'Year_2017', 'Day_01',
#        'Inspection Type_Complaint Re-Inspection',
#        'Facility Type_Daycare (2 - 6 Years)','Violation_21',
#        'Facility Type_Daycare Above and Under 2 Years', 'Violation_30',
#        'Violation_37', 'Facility Type_TAVERN', 'Day_31',
#        'Facility Type_Mobile Food Dispenser', 'Violation_19']
# X_train = df_train[X_names].values
# y_train = df_train["Risk"].values
# X_test = df_test[X_names].values
# y_test = df_test["Risk"].values

X_train = df_train.iloc[:,1:].values
y_train = df_train["Risk"].values
X_test = df_test.iloc[:,1:].values
y_test = df_test["Risk"].values

X_train.shape, X_test.shape

"""# Random Under Sampler"""

print("Before oversampling: ",Counter(y_train))
under_sampler = RandomUnderSampler(random_state=42)
X_train_RUS, y_train_RUS = under_sampler.fit_resample(X_train, y_train)

print("After oversampling: ",Counter(y_train_RUS))

"""# Near Miss Under Sampler"""

print("Before oversampling: ",Counter(y_train))
under_sampler = NearMiss()
X_train_NM, y_train_NM = under_sampler.fit_resample(X_train, y_train)

print("After oversampling: ",Counter(y_train_NM))

"""# Random Over Sampler"""

from imblearn.over_sampling import RandomOverSampler

print("Before oversampling: ",Counter(y_train))
over_sampler = RandomOverSampler(random_state=42)
X_train_ROS, y_train_ROS = over_sampler.fit_resample(X_train, y_train)

print("After oversampling: ",Counter(y_train_ROS))

"""#SMOTE Over Sampler"""

print("Before oversampling: ",Counter(y_train))
SMOTE = SMOTE()

X_train_SMOTE, y_train_SMOTE = SMOTE.fit_resample(X_train, y_train)

print("After oversampling: ",Counter(y_train_SMOTE))

"""# Gaussian Naive Bayes - Base Model"""

X_train.shape, y_train.shape, X_test.shape, y_test.shape

clf_gnb = GaussianNB()
clf_gnb.fit(X_train, y_train)
print('Accuracy of GNB classifier on training set: {:.2f}'
     .format(clf_gnb.score(X_train, y_train)))
print('Accuracy of GNB classifier on test set: {:.2f}'
     .format(clf_gnb.score(X_test, y_test)))

# make a prediction
y_pred = clf_gnb.predict(X_test)

print(accuracy_score(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))
prediction_df_clf_gnb = pd.DataFrame(y_pred)

clf_gnb = GaussianNB()
clf_gnb.fit(X_train_RUS, y_train_RUS )
print('Accuracy of GNB classifier on training set: {:.2f}'
     .format(clf_gnb.score(X_train_RUS, y_train_RUS )))
print('Accuracy of GNB classifier on test set: {:.2f}'
     .format(clf_gnb.score(X_test, y_test)))

# make a prediction
y_pred = clf_gnb.predict(X_test)

print(accuracy_score(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))
prediction_df_clf_gnb_RUS = pd.DataFrame(y_pred)

clf_gnb = GaussianNB()
clf_gnb.fit(X_train_NM, y_train_NM)
print('Accuracy of GNB classifier on training set: {:.2f}'
     .format(clf_gnb.score(X_train_NM, y_train_NM)))
print('Accuracy of GNB classifier on test set: {:.2f}'
     .format(clf_gnb.score(X_test, y_test)))

# make a prediction
y_pred = clf_gnb.predict(X_test)

print(accuracy_score(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))
prediction_df_clf_gnb_NW = pd.DataFrame(y_pred)

clf_gnb = GaussianNB()
clf_gnb.fit(X_train_ROS, y_train_ROS )
print('Accuracy of GNB classifier on training set: {:.2f}'
     .format(clf_gnb.score(X_train_ROS, y_train_ROS )))
print('Accuracy of GNB classifier on test set: {:.2f}'
     .format(clf_gnb.score(X_test, y_test)))

# make a prediction
y_pred = clf_gnb.predict(X_test)

print(accuracy_score(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))
prediction_df_clf_gnb_ROS = pd.DataFrame(y_pred)

clf_gnb = GaussianNB()
clf_gnb.fit(X_train_SMOTE, y_train_SMOTE)
print('Accuracy of GNB classifier on training set: {:.2f}'
     .format(clf_gnb.score(X_train_SMOTE, y_train_SMOTE)))
print('Accuracy of GNB classifier on test set: {:.2f}'
     .format(clf_gnb.score(X_test, y_test)))

# make a prediction
y_pred = clf_gnb.predict(X_test)

print(accuracy_score(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))
prediction_df_clf_gnb_SMOTE = pd.DataFrame(y_pred)

"""https://towardsdatascience.com/solving-a-simple-classification-problem-with-python-fruits-lovers-edition-d20ab6b071d2

# Decision Tree
"""

clf_DT = DecisionTreeClassifier().fit(X_train, y_train)
print('Accuracy of Decision Tree classifier on training set: {:.2f}'
     .format(clf_DT.score(X_train, y_train)))
print('Accuracy of Decision Tree classifier on test set: {:.2f}'
     .format(clf_DT.score(X_test, y_test)))

# make a prediction
y_pred = clf_DT.predict(X_test)

print(accuracy_score(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))
prediction_df_clf_DT = pd.DataFrame(y_pred)

prediction_df_clf_DT.columns = ["predictions"]
prediction_df_clf_DT["actuals"] = y_test
prediction_df_clf_DT["Inspection ID"] = df_test.index
prediction_df_clf_DT.head()

risk1_inspections = prediction_df_clf_DT[(prediction_df_clf_DT["predictions"] == 1) & (prediction_df_clf_DT["actuals"] == 1)]
risk1_inspections.head()

Risk_1_df = pd.merge(risk3_inspections, data, on = "Inspection ID", how="left")
Risk_1_df.head()

Risk1_establishments = Risk_1_df["DBA Name"].unique()
Risk1_establishments

Risk1_establishments[:10]

data["DBA Name"].nunique()

Risk_1_df["DBA Name"].nunique()

clf_DT = DecisionTreeClassifier().fit(X_train_RUS, y_train_RUS )
print('Accuracy of Decision Tree classifier on training set: {:.2f}'
     .format(clf_DT.score(X_train_RUS, y_train_RUS )))
print('Accuracy of Decision Tree classifier on test set: {:.2f}'
     .format(clf_DT.score(X_test, y_test)))

# make a prediction
y_pred = clf_DT.predict(X_test)

print(accuracy_score(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))
prediction_df_clf_DT_RUS = pd.DataFrame(y_pred)

clf_DT = DecisionTreeClassifier().fit(X_train_NM, y_train_NM)
print('Accuracy of Decision Tree classifier on training set: {:.2f}'
     .format(clf_DT.score(X_train_NM, y_train_NM)))
print('Accuracy of Decision Tree classifier on test set: {:.2f}'
     .format(clf_DT.score(X_test, y_test)))

# make a prediction
y_pred = clf_DT.predict(X_test)

print(accuracy_score(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))
prediction_df_clf_DT_NW = pd.DataFrame(y_pred)

clf_DT = DecisionTreeClassifier().fit(X_train_ROS, y_train_ROS)
print('Accuracy of Decision Tree classifier on training set: {:.2f}'
     .format(clf_DT.score(X_train_ROS, y_train_ROS)))
print('Accuracy of Decision Tree classifier on test set: {:.2f}'
     .format(clf_DT.score(X_test, y_test)))

# make a prediction
y_pred = clf_DT.predict(X_test)

print(accuracy_score(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))
prediction_df_clf_DT_ROS = pd.DataFrame(y_pred)

clf_DT = DecisionTreeClassifier().fit(X_train_SMOTE, y_train_SMOTE)
print('Accuracy of Decision Tree classifier on training set: {:.2f}'
     .format(clf_DT.score(X_train_SMOTE, y_train_SMOTE)))
print('Accuracy of Decision Tree classifier on test set: {:.2f}'
     .format(clf_DT.score(X_test, y_test)))

y_pred = clf_DT.predict(X_test)

print(accuracy_score(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))
prediction_df_clf_DT_SMOTE = pd.DataFrame(y_pred)





"""# Neural Networks model"""

def baseline_model():
    model = Sequential()
    model.add(Dense(8, input_dim=X_train.shape[1], activation='relu'))
    model.add(Dense(3, activation='softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model 

estimator = KerasClassifier(build_fn=baseline_model, epochs=10, batch_size=20, verbose=0)
kfold = KFold(n_splits=5, shuffle=True)
results = cross_val_score(estimator, X_train, y_train, cv=kfold)
print("Baseline: %.2f%% (%.2f%%)" % (results.mean()*100, results.std()*100))

y_pred = model.predict(X_test)

print(accuracy_score(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))
prediction_df_model1 = pd.DataFrame(y_pred)



# --The End--