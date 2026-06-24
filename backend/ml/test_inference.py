import pandas as pd
from predict import predict_risk, FEATURE_COLS

# Uses one generated feature row saved by train.py.
feature_matrix = pd.read_csv('models/training_feature_matrix.csv')
row = feature_matrix.iloc[0][FEATURE_COLS].to_dict()
print(predict_risk(row))
