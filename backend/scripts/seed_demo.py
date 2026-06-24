import sys
import os
import uuid
import json
from datetime import datetime, timedelta

# Inject parent directory into path for database imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Borrower, Loan, Transaction, RiskScore, Alert, init_db

# Initialize DB tables if they don't exist
init_db()
db = SessionLocal()

# Borrower
BORROWER_ID = "demo-borrower-rajesh-001"
LOAN_ID = "demo-loan-personal-001"

b = Borrower(
    id=BORROWER_ID,
    name="Rajesh Kumar",
    age=38,
    city="Mumbai",
    employment_type="salaried",
    monthly_income=45000
)
db.merge(b)

l = Loan(
    id=LOAN_ID,
    borrower_id=BORROWER_ID,
    loan_type="personal",
    principal_amount=350000,
    outstanding_balance=280000,
    emi_amount=8200,
    interest_rate=13.5,
    tenure_months=60,
    months_completed=18,
    disbursement_date="2024-12-01",
    status="active"
)
db.merge(l)

# Healthy months (months 1–15)
for i in range(15):
    month = (datetime(2024, 12, 1) + timedelta(days=i*30)).strftime('%Y-%m')
    db.merge(Transaction(
        id=f"tx-healthy-{i}",
        borrower_id=BORROWER_ID,
        loan_id=LOAN_ID,
        month=month,
        credits_count=8, debits_count=22,
        total_credits=47000, total_debits=38000,
        avg_balance=42000, min_balance=28000,
        emi_paid=True, emi_paid_late=False,
        bounce_count=0, utility_bills_paid=True
    ))

# STRESSED months (months 16–18) — this is what drives the score up
for i, month in enumerate(['2026-03', '2026-04', '2026-05']):
    db.merge(Transaction(
        id=f"tx-stressed-{i}",
        borrower_id=BORROWER_ID,
        loan_id=LOAN_ID,
        month=month,
        credits_count=5, debits_count=28,
        total_credits=38000, total_debits=41000,
        avg_balance=9200, min_balance=1100,
        emi_paid=(i == 0),      # Paid only in first stressed month
        emi_paid_late=True,
        bounce_count=i+1,       # Bounces increasing
        utility_bills_paid=(i == 0)
    ))

# Historical risk scores (showing progression)
historical_scores = [
    ("2026-01-01", 24.1, "green"),
    ("2026-02-01", 31.8, "amber"),
    ("2026-03-01", 51.2, "amber"),
    ("2026-04-01", 66.4, "orange"),
    ("2026-05-01", 78.4, "red"),
]

shap_demo = {
    "emi_missed_last_3": 0.312, "bounce_count_3m": 0.187,
    "balance_trend_slope": -0.124, "income_coverage_ratio": -0.091,
    "credit_debit_ratio": 0.089
}
top_factors = [
    {"feature": "emi_missed_last_3", "impact": 0.312, "direction": "increasing_risk", "human_label": "EMI missed (last 3 months)"},
    {"feature": "bounce_count_3m", "impact": 0.187, "direction": "increasing_risk", "human_label": "Cheque bounces (last 3 months)"},
    {"feature": "balance_trend_slope", "impact": 0.124, "direction": "increasing_risk", "human_label": "Account balance trend"},
]

for i, (dt, score, tier) in enumerate(historical_scores):
    db.merge(RiskScore(
        id=f"score-demo-{i}",
        loan_id=LOAN_ID,
        score=score, tier=tier,
        scored_at=datetime.fromisoformat(dt),
        shap_values=json.dumps(shap_demo),
        top_risk_factors=json.dumps(top_factors),
        trigger="scheduled"
    ))

db.merge(Alert(
    id="alert-demo-001",
    loan_id=LOAN_ID,
    alert_type="tier_upgrade",
    severity="critical",
    message="Rajesh Kumar: Risk tier upgraded from ORANGE to RED. Proactive intervention recommended.",
    is_read=False,
))

db.commit()
db.close()
print("✅ Demo data seeded. Rajesh Kumar loan ID:", LOAN_ID)
