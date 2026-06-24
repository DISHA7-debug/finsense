# FinSense — Backend API Reference
## Context File 03 for AI Coding Agents

---

## FastAPI MAIN APP

Save as `backend/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import loans, risk, agent, dashboard
from database import init_db

app = FastAPI(
    title="FinSense API",
    description="NPA Prevention Intelligence Platform for SBI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()

app.include_router(loans.router, prefix="/api/loans", tags=["Loans"])
app.include_router(risk.router, prefix="/api/risk", tags=["Risk Scoring"])
app.include_router(agent.router, prefix="/api/agent", tags=["AI Agent"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "FinSense"}
```

---

## DATABASE SETUP

Save as `backend/database.py`

```python
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./finsense.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

class Borrower(Base):
    __tablename__ = "borrowers"
    id = Column(String, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    city = Column(String)
    employment_type = Column(String)
    monthly_income = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class Loan(Base):
    __tablename__ = "loans"
    id = Column(String, primary_key=True)
    borrower_id = Column(String)
    loan_type = Column(String)
    principal_amount = Column(Float)
    outstanding_balance = Column(Float)
    emi_amount = Column(Float)
    interest_rate = Column(Float)
    tenure_months = Column(Integer)
    months_completed = Column(Integer)
    disbursement_date = Column(String)
    status = Column(String, default='active')
    created_at = Column(DateTime, default=datetime.utcnow)

class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(String, primary_key=True)
    loan_id = Column(String)
    score = Column(Float)
    tier = Column(String)
    scored_at = Column(DateTime, default=datetime.utcnow)
    shap_values = Column(Text)   # JSON string
    top_risk_factors = Column(Text)  # JSON string
    trigger = Column(String)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True)
    borrower_id = Column(String)
    loan_id = Column(String)
    month = Column(String)
    credits_count = Column(Integer)
    debits_count = Column(Integer)
    total_credits = Column(Float)
    total_debits = Column(Float)
    avg_balance = Column(Float)
    min_balance = Column(Float)
    emi_paid = Column(Boolean)
    emi_paid_late = Column(Boolean)
    bounce_count = Column(Integer)
    utility_bills_paid = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True)
    loan_id = Column(String)
    alert_type = Column(String)
    severity = Column(String)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentConversation(Base):
    __tablename__ = "agent_conversations"
    id = Column(String, primary_key=True)
    loan_id = Column(String)
    started_at = Column(DateTime, default=datetime.utcnow)
    channel = Column(String)
    outcome = Column(String, default='pending')
    messages = Column(Text)  # JSON array
```

---

## ALL API ENDPOINTS

### DASHBOARD ROUTER

`GET /api/dashboard/summary`

Returns portfolio-level stats for the officer's home screen.

**Response:**
```json
{
  "total_loans": 5000,
  "by_tier": {
    "green": 3200,
    "amber": 950,
    "orange": 620,
    "red": 230
  },
  "npa_risk_amount": 284000000,
  "alerts_unread": 47,
  "avg_portfolio_risk": 34.2,
  "trend": [
    {"month": "2025-12", "avg_score": 31.1},
    {"month": "2026-01", "avg_score": 32.8},
    {"month": "2026-02", "avg_score": 34.2}
  ]
}
```

---

`GET /api/dashboard/high-risk?limit=20&tier=orange,red`

Returns paginated list of high-risk loans.

**Response:**
```json
{
  "loans": [
    {
      "loan_id": "uuid",
      "borrower_name": "Rajesh Kumar",
      "loan_type": "personal",
      "outstanding_balance": 280000,
      "current_score": 78.4,
      "tier": "red",
      "score_change_30d": +12.3,
      "top_risk_factor": "EMI missed (last 3 months)",
      "last_scored": "2026-06-01T10:00:00"
    }
  ],
  "total": 230
}
```

---

### RISK ROUTER

`GET /api/risk/{loan_id}`

Returns the latest risk score for a loan + history.

**Response:**
```json
{
  "loan_id": "uuid",
  "current": {
    "score": 78.4,
    "tier": "red",
    "probability": 0.784,
    "scored_at": "2026-06-01T10:00:00",
    "top_risk_factors": [
      {
        "feature": "emi_missed_last_3",
        "impact": 0.312,
        "direction": "increasing_risk",
        "human_label": "EMI missed (last 3 months)"
      }
    ],
    "shap_values": { "emi_missed_last_3": 0.312, "bounce_count_3m": 0.187 }
  },
  "history": [
    {"scored_at": "2026-05-01", "score": 66.1, "tier": "orange"},
    {"scored_at": "2026-04-01", "score": 51.2, "tier": "amber"}
  ]
}
```

---

`POST /api/risk/{loan_id}/score`

Manually trigger a re-score for a loan.

**Response:**
```json
{
  "loan_id": "uuid",
  "new_score": 78.4,
  "new_tier": "red",
  "previous_score": 66.1,
  "previous_tier": "orange",
  "tier_changed": true,
  "message": "Risk tier upgraded from ORANGE to RED"
}
```

**Implementation:**
```python
# routers/risk.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid, json
from datetime import datetime

from database import get_db, Loan, RiskScore, Transaction, Borrower, Alert
from ml.predict import predict_risk
from ml.features import build_feature_matrix, FEATURE_COLS
import pandas as pd

router = APIRouter()

@router.get("/{loan_id}")
def get_risk(loan_id: str, db: Session = Depends(get_db)):
    scores = db.query(RiskScore).filter(
        RiskScore.loan_id == loan_id
    ).order_by(RiskScore.scored_at.desc()).all()
    
    if not scores:
        raise HTTPException(404, "No risk scores found for this loan")
    
    current = scores[0]
    history = [{"scored_at": s.scored_at, "score": s.score, "tier": s.tier} for s in scores[1:7]]
    
    return {
        "loan_id": loan_id,
        "current": {
            "score": current.score,
            "tier": current.tier,
            "scored_at": current.scored_at,
            "top_risk_factors": json.loads(current.top_risk_factors or "[]"),
            "shap_values": json.loads(current.shap_values or "{}")
        },
        "history": history
    }

@router.post("/{loan_id}/score")
def rescore_loan(loan_id: str, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    
    # Get last risk score
    prev = db.query(RiskScore).filter(
        RiskScore.loan_id == loan_id
    ).order_by(RiskScore.scored_at.desc()).first()
    
    # Build features
    transactions = db.query(Transaction).filter(
        Transaction.loan_id == loan_id
    ).all()
    
    tx_df = pd.DataFrame([{
        'loan_id': t.loan_id,
        'borrower_id': t.borrower_id,
        'month': t.month,
        'avg_balance': t.avg_balance,
        'min_balance': t.min_balance,
        'total_credits': t.total_credits,
        'total_debits': t.total_debits,
        'emi_paid': t.emi_paid,
        'emi_paid_late': t.emi_paid_late,
        'bounce_count': t.bounce_count,
        'utility_bills_paid': t.utility_bills_paid,
    } for t in transactions])
    
    loans_df = pd.DataFrame([{
        'id': loan.id,
        'borrower_id': loan.borrower_id,
        'emi_amount': loan.emi_amount,
        'outstanding_balance': loan.outstanding_balance,
        'principal_amount': loan.principal_amount,
        'tenure_months': loan.tenure_months,
        'months_completed': loan.months_completed,
        'loan_type': loan.loan_type,
    }])
    
    borrower = db.query(Borrower).filter(Borrower.id == loan.borrower_id).first()
    borrowers_df = pd.DataFrame([{
        'id': borrower.id,
        'monthly_income': borrower.monthly_income,
        'employment_type': borrower.employment_type,
    }])
    
    feat_df = build_feature_matrix(tx_df, loans_df, borrowers_df)
    if feat_df.empty:
        raise HTTPException(400, "Not enough transaction history to score")
    
    feature_dict = feat_df[FEATURE_COLS].iloc[0].to_dict()
    result = predict_risk(feature_dict)
    
    # Save new score
    new_score = RiskScore(
        id=str(uuid.uuid4()),
        loan_id=loan_id,
        score=result['score'],
        tier=result['tier'],
        shap_values=json.dumps(result['shap_values']),
        top_risk_factors=json.dumps(result['top_risk_factors']),
        trigger='manual'
    )
    db.add(new_score)
    
    # Create alert if tier changed
    prev_tier = prev.tier if prev else None
    tier_changed = prev_tier != result['tier']
    if tier_changed and result['tier'] in ['orange', 'red']:
        alert = Alert(
            id=str(uuid.uuid4()),
            loan_id=loan_id,
            alert_type='tier_upgrade',
            severity='critical' if result['tier'] == 'red' else 'warning',
            message=f"Risk tier changed from {prev_tier.upper() if prev_tier else 'UNSCORED'} to {result['tier'].upper()}"
        )
        db.add(alert)
    
    db.commit()
    
    return {
        "loan_id": loan_id,
        "new_score": result['score'],
        "new_tier": result['tier'],
        "previous_score": prev.score if prev else None,
        "previous_tier": prev_tier,
        "tier_changed": tier_changed,
        "top_risk_factors": result['top_risk_factors'],
    }
```

---

### AGENT ROUTER

`POST /api/agent/{loan_id}/start`

Starts an AI agent conversation for a loan.

**Request body:**
```json
{ "channel": "in_app" }
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "opening_message": "Namaste Rajesh ji, I'm calling from SBI regarding your personal loan account..."
}
```

`POST /api/agent/{loan_id}/message`

Send a borrower reply and get the agent's next response.

**Request:**
```json
{
  "conversation_id": "uuid",
  "message": "I had some medical expenses last month, that's why the EMI was late"
}
```

**Response:**
```json
{
  "reply": "I completely understand, Rajesh ji. Health comes first. SBI has a loan restructuring option that can reduce your EMI by up to 30% for the next 6 months while you recover. Would you like me to explain how that works?",
  "suggested_actions": ["Learn about restructuring", "Speak to branch officer", "Schedule callback"],
  "outcome_signal": "open_to_help"
}
```

`GET /api/agent/{loan_id}/conversations`

Lists all past agent conversations for a loan.

---

### LOANS ROUTER

`GET /api/loans/{loan_id}`

Full borrower + loan details.

`GET /api/loans/borrower/{borrower_id}`

All loans for a borrower.

`GET /api/loans/?tier=red&type=personal&limit=50`

Filtered loan list.

---

## RUNNING THE SERVER

```bash
cd backend/
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs auto-generated at: `http://localhost:8000/docs`

---
