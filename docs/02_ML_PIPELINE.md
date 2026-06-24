# FinSense — ML Pipeline: Training & Inference
## Context File 02 for AI Coding Agents

---

## OVERVIEW

The ML pipeline has two phases:
1. **Training** (offline, run once before demo): Produces `xgb_model.pkl` + `scaler.pkl`
2. **Inference** (live, called by FastAPI): Produces risk score 0–100 + SHAP explanations

Model of choice: **XGBoost classifier** (probability output → risk score)
Why XGBoost: handles tabular data extremely well, fast, supports SHAP natively, interpretable

---

## TRAINING SCRIPT

Save as `backend/ml/train.py`

```python
import pandas as pd
import numpy as np
import pickle
import json
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier
import shap

from features import build_feature_matrix, FEATURE_COLS

def train_model():
    print("Loading synthetic data...")
    transactions = pd.read_csv('../data/synthetic_transactions.csv')
    loans = pd.read_csv('../data/synthetic_loans.csv')
    borrowers = pd.read_csv('../data/synthetic_borrowers.csv')
    
    print("Building feature matrix...")
    df = build_feature_matrix(transactions, loans, borrowers)
    df = df.dropna(subset=['label'])
    
    X = df[FEATURE_COLS]
    y = df['label'].astype(int)
    
    print(f"Dataset: {len(df)} samples | Stressed: {y.sum()} ({y.mean()*100:.1f}%)")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train XGBoost
    # scale_pos_weight handles class imbalance (healthy >> stressed)
    neg = (y_train == 0).sum()
    pos = (y_train == 1).sum()
    spw = neg / pos
    
    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=spw,
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=50
    )
    
    # Evaluate
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    y_pred = (y_prob > 0.5).astype(int)
    
    print("\n--- Model Performance ---")
    print(classification_report(y_test, y_pred, target_names=['Healthy', 'Stressed']))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}")
    
    # SHAP explainer (TreeExplainer is fast for XGBoost)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test_scaled[:100])
    
    print("\nTop 5 features by mean |SHAP|:")
    mean_shap = pd.Series(
        np.abs(shap_values).mean(axis=0),
        index=FEATURE_COLS
    ).sort_values(ascending=False)
    print(mean_shap.head())
    
    # Save artifacts
    with open('models/xgb_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('models/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    with open('models/explainer.pkl', 'wb') as f:
        pickle.dump(explainer, f)
    with open('models/feature_cols.json', 'w') as f:
        json.dump(FEATURE_COLS, f)
    
    print("\n✅ Models saved to models/")
    return model, scaler, explainer

if __name__ == '__main__':
    train_model()
```

---

## INFERENCE MODULE

Save as `backend/ml/predict.py`

```python
import pickle
import json
import numpy as np
import pandas as pd
import shap
from pathlib import Path

MODEL_DIR = Path(__file__).parent / 'models'

# Load once at startup (module-level cache)
with open(MODEL_DIR / 'xgb_model.pkl', 'rb') as f:
    _model = pickle.load(f)
with open(MODEL_DIR / 'scaler.pkl', 'rb') as f:
    _scaler = pickle.load(f)
with open(MODEL_DIR / 'explainer.pkl', 'rb') as f:
    _explainer = pickle.load(f)
with open(MODEL_DIR / 'feature_cols.json') as f:
    FEATURE_COLS = json.load(f)


def score_to_tier(score: float) -> str:
    """Convert 0–100 risk score to tier string."""
    if score < 30:
        return 'green'
    elif score < 55:
        return 'amber'
    elif score < 75:
        return 'orange'
    else:
        return 'red'


def predict_risk(feature_dict: dict) -> dict:
    """
    Main inference function.
    
    Input:
        feature_dict: dict with all 12 feature keys
    
    Returns:
        {
            'score': float (0–100),
            'tier': str,
            'probability': float (0–1),
            'shap_values': {feature_name: shap_value},
            'top_risk_factors': [{'feature': str, 'impact': float, 'direction': str}]
        }
    """
    X = pd.DataFrame([feature_dict])[FEATURE_COLS]
    X_scaled = _scaler.transform(X)
    
    # Get probability of being stressed (class 1)
    prob = float(_model.predict_proba(X_scaled)[0, 1])
    score = round(prob * 100, 2)
    tier = score_to_tier(score)
    
    # SHAP explanation
    shap_vals = _explainer.shap_values(X_scaled)[0]
    shap_dict = {feat: round(float(sv), 4) for feat, sv in zip(FEATURE_COLS, shap_vals)}
    
    # Top 3 risk factors (highest absolute SHAP, sorted)
    sorted_shap = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
    top_factors = [
        {
            'feature': feat,
            'impact': round(abs(val), 4),
            'direction': 'increasing_risk' if val > 0 else 'decreasing_risk',
            'human_label': FEATURE_HUMAN_LABELS.get(feat, feat)
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


# Human-readable labels for SHAP display in UI
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
```

---

## EXPECTED MODEL PERFORMANCE

With 5000 borrowers and ~25–35% stressed class:

| Metric | Expected Value |
|---|---|
| ROC-AUC | 0.88–0.94 |
| Precision (stressed) | 0.78–0.87 |
| Recall (stressed) | 0.80–0.90 |
| F1 (stressed) | 0.79–0.88 |

If your ROC-AUC is below 0.82, check:
1. Is `is_stressed` label being propagated correctly in transactions?
2. Is the feature matrix built on the LAST 6 months (not all months)?
3. Is `scale_pos_weight` set to handle imbalance?

---

## HOW TO RUN TRAINING

```bash
cd backend/
pip install xgboost shap scikit-learn pandas numpy faker
mkdir -p ml/models

# Generate data first
python data/generate_synthetic.py

# Train model
cd ml/
python train.py
```

Training should take 2–5 minutes on a laptop. You will see:
- Loss decreasing each 50 iterations
- Final classification report
- Top 5 SHAP features printed
- 3 model files in `models/`

---

## SHAP EXPLANATION — HOW TO EXPLAIN TO JUDGES

"SHAP (SHapley Additive exPlanations) is a game-theory-based technique that assigns each feature a contribution score for a specific prediction. Unlike a global feature importance chart, SHAP tells us WHY THIS SPECIFIC BORROWER was scored the way they were.

For example:
- Borrower Rajesh has a risk score of 71 (Orange tier)
- SHAP says: EMI missed last 3 months (+28), Cheque bounces (+15), Balance trend (-8 = reducing risk slightly)
- So the loan officer knows EXACTLY why Rajesh is flagged and what to discuss

This makes the AI system trustworthy — it's not a black box."

---

## REQUIREMENTS

```
# requirements.txt
fastapi==0.111.0
uvicorn==0.29.0
xgboost==2.0.3
shap==0.45.0
scikit-learn==1.4.2
pandas==2.2.2
numpy==1.26.4
faker==24.0.0
scipy==1.13.0
sqlalchemy==2.0.30
pydantic==2.7.1
python-multipart==0.0.9
celery==5.3.6
redis==5.0.4
```

---
