import uuid
import json
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Loan, RiskScore, Alert, Transaction, Borrower

router = APIRouter()


ML_AVAILABLE = False
try:
    MODEL_DIR = Path(__file__).resolve().parent.parent / "ml" / "models"
    if (MODEL_DIR / "xgb_model.pkl").exists():
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from ml.predict import predict_risk
        from ml.features import build_feature_matrix, FEATURE_COLS
        ML_AVAILABLE = True
        print("✅ ML model loaded — real scoring active")
    else:
        print("⚠️  ML models not found — using stub scores until models/ is pushed")
except Exception as e:
    print(f"⚠️  ML import failed ({e}) — using stub scores")


def _stub_prediction():
    """Fallback when ML models aren't trained yet."""
    return {
        "score": 72.5,
        "tier": "orange",
        "shap_values": {
            "emi_missed_last_3": 0.25,
            "bounce_count_3m": 0.15,
            "balance_trend_slope": -0.10,
            "income_coverage_ratio": -0.05
        },
        "top_risk_factors": [
            {"feature": "emi_missed_last_3", "impact": 0.25, "direction": "increasing_risk", "human_label": "EMI missed (last 3 months)"},
            {"feature": "bounce_count_3m",   "impact": 0.15, "direction": "increasing_risk", "human_label": "Cheque bounces (last 3 months)"},
            {"feature": "balance_trend_slope","impact": 0.10, "direction": "increasing_risk", "human_label": "Account balance trend"}
        ]
    }


def _real_prediction(loan, borrower, db):
    """Run actual ML inference using trained XGBoost model."""
    transactions = db.query(Transaction).filter(
        Transaction.loan_id == loan.id
    ).all()

    if not transactions:
        return None  # Not enough data, fall back to stub

    tx_df = pd.DataFrame([{
        "loan_id":           t.loan_id,
        "borrower_id":       t.borrower_id,
        "month":             t.month,
        "avg_balance":       t.avg_balance,
        "min_balance":       t.min_balance,
        "total_credits":     t.total_credits,
        "total_debits":      t.total_debits,
        "emi_paid":          t.emi_paid,
        "emi_paid_late":     t.emi_paid_late,
        "bounce_count":      t.bounce_count,
        "utility_bills_paid":t.utility_bills_paid,
    } for t in transactions])

    loans_df = pd.DataFrame([{
        "id":                  loan.id,
        "borrower_id":         loan.borrower_id,
        "emi_amount":          loan.emi_amount,
        "outstanding_balance": loan.outstanding_balance,
        "principal_amount":    loan.principal_amount,
        "tenure_months":       loan.tenure_months,
        "months_completed":    loan.months_completed,
        "loan_type":           loan.loan_type,
    }])

    borrowers_df = pd.DataFrame([{
        "id":               borrower.id,
        "monthly_income":   borrower.monthly_income,
        "employment_type":  borrower.employment_type,
    }])

    feat_df = build_feature_matrix(tx_df, loans_df, borrowers_df)
    if feat_df.empty:
        return None

    feature_dict = feat_df[FEATURE_COLS].iloc[0].to_dict()
    return predict_risk(feature_dict)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/{loan_id}")
def get_risk(loan_id: str, db: Session = Depends(get_db)):
    scores = db.query(RiskScore).filter(
        RiskScore.loan_id == loan_id
    ).order_by(RiskScore.scored_at.desc()).all()

    if not scores:
        raise HTTPException(status_code=404, detail="No risk scores found for this loan")

    current = scores[0]
    history = [
        {
            "scored_at": s.scored_at.strftime('%Y-%m-%d') if isinstance(s.scored_at, datetime) else str(s.scored_at)[:10],
            "score":     s.score,
            "tier":      s.tier
        }
        for s in scores[1:7]
    ]

    return {
        "loan_id": loan_id,
        "current": {
            "score":            current.score,
            "tier":             current.tier,
            "scored_at":        current.scored_at.isoformat() if isinstance(current.scored_at, datetime) else current.scored_at,
            "top_risk_factors": json.loads(current.top_risk_factors or "[]"),
            "shap_values":      json.loads(current.shap_values or "{}"),
            "ml_powered":       ML_AVAILABLE
        },
        "history": history
    }


@router.post("/{loan_id}/score")
def rescore_loan(loan_id: str, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    prev = db.query(RiskScore).filter(
        RiskScore.loan_id == loan_id
    ).order_by(RiskScore.scored_at.desc()).first()

    
    result = None
    if ML_AVAILABLE:
        borrower = db.query(Borrower).filter(Borrower.id == loan.borrower_id).first()
        result = _real_prediction(loan, borrower, db)

    if result is None:
        result = _stub_prediction()

    score           = result["score"]
    tier            = result["tier"]
    shap_values     = result["shap_values"]
    top_risk_factors= result["top_risk_factors"]

    new_score = RiskScore(
        id=str(uuid.uuid4()),
        loan_id=loan_id,
        score=score,
        tier=tier,
        shap_values=json.dumps(shap_values),
        top_risk_factors=json.dumps(top_risk_factors),
        trigger='manual'
    )
    db.add(new_score)

    prev_tier    = prev.tier if prev else None
    tier_changed = prev_tier != tier
    if tier_changed and tier in ['orange', 'red']:
        alert = Alert(
            id=str(uuid.uuid4()),
            loan_id=loan_id,
            alert_type='tier_upgrade',
            severity='critical' if tier == 'red' else 'warning',
            message=f"Risk tier changed from {prev_tier.upper() if prev_tier else 'UNSCORED'} to {tier.upper()}"
        )
        db.add(alert)

    db.commit()

    return {
        "loan_id":        loan_id,
        "new_score":      score,
        "new_tier":       tier,
        "previous_score": prev.score if prev else None,
        "previous_tier":  prev_tier,
        "tier_changed":   tier_changed,
        "top_risk_factors": top_risk_factors,
        "ml_powered":     ML_AVAILABLE
    }