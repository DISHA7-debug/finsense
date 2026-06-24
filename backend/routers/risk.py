import uuid
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Loan, RiskScore, Alert

router = APIRouter()

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
            "score": s.score,
            "tier": s.tier
        }
        for s in scores[1:7]
    ]
    
    return {
        "loan_id": loan_id,
        "current": {
            "score": current.score,
            "tier": current.tier,
            "scored_at": current.scored_at.isoformat() if isinstance(current.scored_at, datetime) else current.scored_at,
            "top_risk_factors": json.loads(current.top_risk_factors or "[]"),
            "shap_values": json.loads(current.shap_values or "{}")
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
    
    # Stub the ML call for now
    # TODO: replace with predict_risk() once ml branch delivers predict.py
    score = 72.5
    tier = "orange"
    shap_values = {
        "emi_missed_last_3": 0.25,
        "bounce_count_3m": 0.15,
        "balance_trend_slope": -0.10,
        "income_coverage_ratio": -0.05
    }
    top_risk_factors = [
        {"feature": "emi_missed_last_3", "impact": 0.25, "direction": "increasing_risk", "human_label": "EMI missed (last 3 months)"},
        {"feature": "bounce_count_3m", "impact": 0.15, "direction": "increasing_risk", "human_label": "Cheque bounces (last 3 months)"},
        {"feature": "balance_trend_slope", "impact": 0.10, "direction": "increasing_risk", "human_label": "Account balance trend"}
    ]
    
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
    
    # Create alert if tier changed and it upgraded to orange/red
    prev_tier = prev.tier if prev else None
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
        "loan_id": loan_id,
        "new_score": score,
        "new_tier": tier,
        "previous_score": prev.score if prev else None,
        "previous_tier": prev_tier,
        "tier_changed": tier_changed,
        "top_risk_factors": top_risk_factors
    }
