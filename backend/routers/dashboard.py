import json
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, Loan, RiskScore, Alert, Borrower

router = APIRouter()

@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    loans = db.query(Loan).all()
    total_loans = len(loans)
    
    # Fetch risk scores sorted by date ascending
    scores = db.query(RiskScore).order_by(RiskScore.scored_at.asc()).all()
    
    # Group by loan to find the latest score
    latest_scores = {}
    for s in scores:
        latest_scores[s.loan_id] = s
        
    by_tier = {"green": 0, "amber": 0, "orange": 0, "red": 0}
    npa_risk_amount = 0.0
    total_score = 0.0
    scored_count = 0
    
    for loan in loans:
        latest = latest_scores.get(loan.id)
        if latest:
            tier = latest.tier.lower() if latest.tier else "green"
            score = latest.score
            scored_count += 1
            total_score += score
        else:
            tier = "green"
            
        by_tier[tier] = by_tier.get(tier, 0) + 1
        
        # Stressed tiers are orange and red
        if tier in ["orange", "red"]:
            npa_risk_amount += loan.outstanding_balance
            
    avg_portfolio_risk = round(total_score / scored_count, 1) if scored_count > 0 else 0.0
    alerts_unread = db.query(Alert).filter(Alert.is_read == False).count()
    
    # Calculate historical trend (group scores by YYYY-MM)
    monthly_scores = {}
    for s in scores:
        if isinstance(s.scored_at, datetime):
            month = s.scored_at.strftime('%Y-%m')
        else:
            month = str(s.scored_at)[:7]
        if month not in monthly_scores:
            monthly_scores[month] = []
        monthly_scores[month].append(s.score)
        
    trend = []
    for month in sorted(monthly_scores.keys()):
        avg = round(sum(monthly_scores[month]) / len(monthly_scores[month]), 1)
        trend.append({"month": month, "avg_score": avg})
        
    return {
        "total_loans": total_loans,
        "by_tier": by_tier,
        "npa_risk_amount": npa_risk_amount,
        "alerts_unread": alerts_unread,
        "avg_portfolio_risk": avg_portfolio_risk,
        "trend": trend[-6:]  # return up to last 6 months
    }

@router.get("/high-risk")
def get_high_risk(tier: str = "orange,red", limit: int = 20, db: Session = Depends(get_db)):
    allowed_tiers = [t.strip().lower() for t in tier.split(",")]
    
    loans = db.query(Loan).all()
    borrowers = {b.id: b for b in db.query(Borrower).all()}
    
    loan_scores = {}
    for s in db.query(RiskScore).order_by(RiskScore.scored_at.asc()).all():
        if s.loan_id not in loan_scores:
            loan_scores[s.loan_id] = []
        loan_scores[s.loan_id].append(s)
        
    high_risk_list = []
    
    for loan in loans:
        scores_history = loan_scores.get(loan.id, [])
        if not scores_history:
            continue
            
        latest_score = scores_history[-1]
        if latest_score.tier.lower() not in allowed_tiers:
            continue
            
        borrower = borrowers.get(loan.borrower_id)
        borrower_name = borrower.name if borrower else "Unknown"
        
        # 30d change is difference between latest and second-latest score
        if len(scores_history) > 1:
            prev_score = scores_history[-2].score
            score_change = round(latest_score.score - prev_score, 2)
        else:
            score_change = 0.0
            
        top_factors = json.loads(latest_score.top_risk_factors or "[]")
        top_risk_factor = top_factors[0]["human_label"] if top_factors else "Unknown"
        
        high_risk_list.append({
            "loan_id": loan.id,
            "borrower_name": borrower_name,
            "loan_type": loan.loan_type,
            "outstanding_balance": loan.outstanding_balance,
            "current_score": latest_score.score,
            "tier": latest_score.tier,
            "score_change_30d": score_change,
            "top_risk_factor": top_risk_factor,
            "last_scored": latest_score.scored_at.isoformat() if isinstance(latest_score.scored_at, datetime) else latest_score.scored_at
        })
        
    # Sort by current_score descending
    high_risk_list.sort(key=lambda x: x["current_score"], reverse=True)
    
    return {
        "loans": high_risk_list[:limit],
        "total": len(high_risk_list)
    }
