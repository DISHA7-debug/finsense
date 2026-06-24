# FinSense ML Starter

This package contains the ML-side files for FinSense:

- `backend/data/generate_synthetic.py` generates borrowers, loans, and monthly transaction summaries.
- `backend/ml/features.py` converts raw tables into the 12 ML features.
- `backend/ml/train.py` trains XGBoost and saves model artifacts.
- `backend/ml/predict.py` loads saved artifacts and returns risk score, tier, SHAP values, and top risk factors.
- `backend/ml/test_inference.py` tests a single prediction after training.

## Run

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
python data/generate_synthetic.py
cd ml
python train.py
python test_inference.py
```

Expected artifacts:

```text
backend/ml/models/xgb_model.pkl
backend/ml/models/scaler.pkl
backend/ml/models/explainer.pkl
backend/ml/models/feature_cols.json
backend/ml/models/training_feature_matrix.csv
```
