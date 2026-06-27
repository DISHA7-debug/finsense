import uuid, json
from datetime import datetime, timedelta
from database import SessionLocal, Borrower, Loan, Transaction, RiskScore, Alert, init_db

init_db()
db = SessionLocal()

BORROWER_ID = "demo-borrower-rajesh-001"
LOAN_ID = "demo-loan-personal-001"

# Clear existing data
db.query(Alert).filter(Alert.loan_id == LOAN_ID).delete()
db.query(RiskScore).filter(RiskScore.loan_id == LOAN_ID).delete()
db.query(Transaction).filter(Transaction.borrower_id == BORROWER_ID).delete()
db.query(Loan).filter(Loan.id == LOAN_ID).delete()
db.query(Borrower).filter(Borrower.id == BORROWER_ID).delete()
db.commit()

b = Borrower(
    id=BORROWER_ID,
    name="Rajesh Kumar",
    age=38,
    city="Mumbai",
    employment_type="salaried",
    monthly_income=45000
)
db.add(b)

l = Loan(
    id=LOAN_ID,
    borrower_id=BORROWER_ID,
    loan_type="personal",
    principal_amount=350000,
    outstanding_balance=280000,
    emi_amount=8200,
    interest_rate=13.5,
    tenure_months=60,
    months_completed=7,
    disbursement_date="2024-12-01",
    status="active"
)
db.add(l)

# 4 borderline healthy months — balance just barely above EMI
healthy_months = ['2025-09', '2025-10', '2025-11', '2025-12']
for month in healthy_months:
    db.add(Transaction(
        id=str(uuid.uuid4()),
        borrower_id=BORROWER_ID,
        loan_id=LOAN_ID,
        month=month,
        credits_count=6, debits_count=20,
        total_credits=41000, total_debits=39500,
        avg_balance=9800,   # just above EMI of 8200
        min_balance=5200,
        emi_paid=True, emi_paid_late=True,  # paid but late
        bounce_count=1,
        utility_bills_paid=True
    ))

# 3 severely stressed months
stressed = [
    ('2026-01', False, 2, 4100, 800, False),
    ('2026-02', False, 3, 3200, 200, False),
    ('2026-03', False, 4, 1800, 0,   False),
]
for month, emi_paid, bounces, avg_bal, min_bal, utility in stressed:
    db.add(Transaction(
        id=str(uuid.uuid4()),
        borrower_id=BORROWER_ID,
        loan_id=LOAN_ID,
        month=month,
        credits_count=3, debits_count=25,
        total_credits=32000, total_debits=38000,
        avg_balance=avg_bal,
        min_balance=min_bal,
        emi_paid=emi_paid, emi_paid_late=True,
        bounce_count=bounces,
        utility_bills_paid=utility
    ))

# Historical risk scores showing the arc
historical_scores = [
    ("2025-10-01", 24.1, "green"),
    ("2025-11-01", 38.4, "amber"),
    ("2025-12-01", 51.2, "amber"),
    ("2026-01-01", 66.4, "orange"),
    ("2026-02-01", 78.4, "red"),
]
shap_demo = {"emi_missed_last_3": 0.312, "bounce_count_3m": 0.187, "balance_trend_slope": -0.124}
top_factors = [
    {"feature": "emi_missed_last_3", "impact": 0.312, "direction": "increasing_risk", "human_label": "EMI missed (last 3 months)"},
    {"feature": "bounce_count_3m", "impact": 0.187, "direction": "increasing_risk", "human_label": "Cheque bounces (last 3 months)"},
    {"feature": "balance_trend_slope", "impact": 0.124, "direction": "increasing_risk", "human_label": "Account balance trend"},
]
for i, (dt, score, tier) in enumerate(historical_scores):
    db.add(RiskScore(
        id=f"score-demo-{i}",
        loan_id=LOAN_ID,
        score=score, tier=tier,
        scored_at=datetime.fromisoformat(dt),
        shap_values=json.dumps(shap_demo),
        top_risk_factors=json.dumps(top_factors),
        trigger="scheduled"
    ))

db.add(Alert(
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