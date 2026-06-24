import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from features import build_feature_matrix, FEATURE_COLS

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / 'data'
MODEL_DIR = Path(__file__).resolve().parent / 'models'


def train_model():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print('Loading synthetic data...')
    transactions = pd.read_csv(DATA_DIR / 'synthetic_transactions.csv')
    loans = pd.read_csv(DATA_DIR / 'synthetic_loans.csv')
    borrowers = pd.read_csv(DATA_DIR / 'synthetic_borrowers.csv')

    print('Building feature matrix...')
    df = build_feature_matrix(transactions, loans, borrowers).dropna(subset=['label'])
    if df.empty:
        raise RuntimeError('Feature matrix is empty. Check generated transaction months and loan IDs.')

    X = df[FEATURE_COLS]
    y = df['label'].astype(int)
    print(f'Dataset: {len(df):,} samples | Stressed: {y.sum():,} ({y.mean()*100:.1f}%)')

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    neg = int((y_train == 0).sum())
    pos = int((y_train == 1).sum())
    scale_pos_weight = neg / max(pos, 1)

    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric='logloss',
        random_state=42,
        n_jobs=-1,
    )

    print('Training XGBoost...')
    model.fit(X_train_scaled, y_train, eval_set=[(X_test_scaled, y_test)], verbose=50)

    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    print('\n--- Model Performance ---')
    print(classification_report(y_test, y_pred, target_names=['Healthy', 'Stressed']))
    print(f'ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}')
    print('Confusion matrix:')
    print(confusion_matrix(y_test, y_pred))

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test_scaled[:100])
    mean_shap = pd.Series(np.abs(shap_values).mean(axis=0), index=FEATURE_COLS).sort_values(ascending=False)
    print('\nTop 5 features by mean |SHAP|:')
    print(mean_shap.head())

    with open(MODEL_DIR / 'xgb_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open(MODEL_DIR / 'scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    with open(MODEL_DIR / 'explainer.pkl', 'wb') as f:
        pickle.dump(explainer, f)
    with open(MODEL_DIR / 'feature_cols.json', 'w', encoding='utf-8') as f:
        json.dump(FEATURE_COLS, f, indent=2)
    df.to_csv(MODEL_DIR / 'training_feature_matrix.csv', index=False)

    print(f'\nSaved model artifacts to: {MODEL_DIR}')
    return model, scaler, explainer


if __name__ == '__main__':
    train_model()
