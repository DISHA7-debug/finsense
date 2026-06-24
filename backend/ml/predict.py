import json
import pickle
from pathlib import Path

import pandas as pd

MODEL_DIR = Path(__file__).resolve().parent / 'models'

with open(MODEL_DIR / 'xgb_model.pkl', 'rb') as f:
    _model = pickle.load(f)
with open(MODEL_DIR / 'scaler.pkl', 'rb') as f:
    _scaler = pickle.load(f)
with open(MODEL_DIR / 'explainer.pkl', 'rb') as f:
    _explainer = pickle.load(f)
with open(MODEL_DIR / 'feature_cols.json', encoding='utf-8') as f:
    FEATURE_COLS = json.load(f)

FEATURE_HUMAN_LABELS = {
    'emi_missed_last_3': 'EMI missed (last 3 months)',
    'balance_trend_slope': 'Account balance trend',
    'bounce_count_3m': 'Cheque bounces (last 3 months)',
    'income_coverage_ratio': 'Balance vs EMI coverage',
    'credit_debit_ratio': 'Money in vs money out',
    'utilisation_rate': 'Loan utilisation',
    'months_to_completion': 'Months remaining on loan',
    'late_payment_rate': 'Rate of late payments',
    'utility_miss_rate': 'Utility bill non-payment rate',
    'min_balance_ratio': 'Minimum balance buffer',
    'loan_to_income_ratio': 'Loan vs annual income',
    'employment_risk': 'Employment type risk',
}


def score_to_tier(score: float) -> str:
    if score < 30:
        return 'green'
    if score < 55:
        return 'amber'
    if score < 75:
        return 'orange'
    return 'red'


def predict_risk(feature_dict: dict) -> dict:
    missing = [col for col in FEATURE_COLS if col not in feature_dict]
    if missing:
        raise ValueError(f'Missing required feature(s): {missing}')

    X = pd.DataFrame([feature_dict])[FEATURE_COLS]
    X_scaled = _scaler.transform(X)
    prob = float(_model.predict_proba(X_scaled)[0, 1])
    score = round(prob * 100, 2)
    tier = score_to_tier(score)

    shap_vals = _explainer.shap_values(X_scaled)[0]
    shap_dict = {feat: round(float(sv), 4) for feat, sv in zip(FEATURE_COLS, shap_vals)}
    sorted_shap = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
    top_factors = [
        {
            'feature': feat,
            'impact': round(abs(val), 4),
            'direction': 'increasing_risk' if val > 0 else 'decreasing_risk',
            'human_label': FEATURE_HUMAN_LABELS.get(feat, feat),
        }
        for feat, val in sorted_shap[:5]
    ]
    return {
        'score': score,
        'tier': tier,
        'probability': prob,
        'shap_values': shap_dict,
        'top_risk_factors': top_factors,
    }
