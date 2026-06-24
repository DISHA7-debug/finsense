from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Loan, Borrower, RiskScore

router = APIRouter()

@router.get("")
def get_loans(tier: str = None, type: str = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(Loan)
    if type:
        query = query.filter(Loan.loan_type == type)
        
    loans = query.all()
    results = []
    
    for loan in loans:
        latest_score = db.query(RiskScore).filter(RiskScore.loan_id == loan.id).order_by(RiskScore.scored_at.desc()).first()
        loan_tier = latest_score.tier if latest_score else "green"
        if tier and loan_tier.lower() != tier.lower():
            continue
            
        borrower = db.query(Borrower).filter(Borrower.id == loan.borrower_id).first()
        borrower_name = borrower.name if borrower else "Unknown"
        
        results.append({
            "id": loan.id,
            "borrower_id": loan.borrower_id,
            "borrower_name": borrower_name,
            "loan_type": loan.loan_type,
            "principal_amount": loan.principal_amount,
            "outstanding_balance": loan.outstanding_balance,
            "emi_amount": loan.emi_amount,
            "interest_rate": loan.interest_rate,
            "tenure_months": loan.tenure_months,
            "months_completed": loan.months_completed,
            "disbursement_date": loan.disbursement_date,
            "status": loan.status,
            "tier": loan_tier,
            "current_score": latest_score.score if latest_score else 0.0
        })
        
    return results[:limit]

@router.get("/{loan_id}")
def get_loan(loan_id: str, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
        
    borrower = db.query(Borrower).filter(Borrower.id == loan.borrower_id).first()
    if not borrower:
        raise HTTPException(status_code=404, detail="Borrower not found")
        
    return {
        "id": loan.id,
        "borrower_id": loan.borrower_id,
        "loan_type": loan.loan_type,
        "principal_amount": loan.principal_amount,
        "outstanding_balance": loan.outstanding_balance,
        "emi_amount": loan.emi_amount,
        "interest_rate": loan.interest_rate,
        "tenure_months": loan.tenure_months,
        "months_completed": loan.months_completed,
        "disbursement_date": loan.disbursement_date,
        "status": loan.status,
        "created_at": loan.created_at.isoformat() if loan.created_at else None,
        "borrower": {
            "id": borrower.id,
            "name": borrower.name,
            "age": borrower.age,
            "city": borrower.city,
            "employment_type": borrower.employment_type,
            "monthly_income": borrower.monthly_income,
            "created_at": borrower.created_at.isoformat() if borrower.created_at else None
        }
    }

@router.get("/borrower/{borrower_id}")
def get_loans_by_borrower(borrower_id: str, db: Session = Depends(get_db)):
    loans = db.query(Loan).filter(Loan.borrower_id == borrower_id).all()
    return loans
