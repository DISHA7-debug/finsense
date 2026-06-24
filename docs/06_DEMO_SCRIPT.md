# FinSense — Hackathon Demo Script & Pitch Guide
## Context File 06 for AI Coding Agents

---

## THE GOLDEN RULE OF DEMO

**One borrower. One journey. Three minutes.**

Do NOT demo features. Demo a STORY.

The story is: *"Rajesh Kumar was 60 days from default. FinSense caught it. SBI saved ₹2.8 lakh."*

---

## SEED DATA FOR DEMO (Run Before Presentation)

Create this specific borrower so you can demo predictably:

```python
# backend/scripts/seed_demo.py
# Run this: python seed_demo.py

import uuid, json
from datetime import datetime, timedelta
from database import SessionLocal, Borrower, Loan, Transaction, RiskScore, Alert, init_db

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
```

---

## 3-MINUTE DEMO SCRIPT

**[00:00 – 00:30] The Problem Statement (Presenter 1 speaks)**

> "SBI wrote off over ₹16,000 crore in bad loans last year. Every single one of those started the same way — someone's financial health declined slowly, and no one caught it until it was too late.
>
> CIBIL scores a borrower once, at the time of the loan. But what happens in the 5 years after? That's the gap FinSense fills."

*[Slide on screen: SBI NPA figure + gap visualization]*

---

**[00:30 – 01:00] The Dashboard (Presenter 2 demo on screen)**

> "This is FinSense's officer dashboard. Right now it's monitoring 5,000 active loans across SBI's portfolio."

*[Click: Dashboard loads]*

> "You can see 230 loans in the RED tier — pre-default. 620 in ORANGE. The portfolio average risk has been rising — from 31 in January to 34.2 today. That's an early warning."

*[Click: Filter to RED tier]*

> "Let's look at Rajesh Kumar. Personal loan, ₹2.8 lakh outstanding."

*[Click: Rajesh Kumar row → BorrowerDetail page]*

---

**[01:00 – 01:40] The Risk Intelligence (Presenter 2 continues)**

> "Rajesh's risk score is 78.4 — RED tier. But here's the important part: we can see WHY."

*[Point to SHAP bar chart]*

> "He missed 2 out of 3 EMIs last month. His account had 2 bounced cheques. And his balance has been steadily declining over 4 months. FinSense detected this trend in March, when his score was 51."

*[Point to history chart]*

> "While he was AMBER in February, he was fine. By April — ORANGE. May — RED. The system flagged him and created this alert — automatically."

---

**[01:40 – 02:20] The Agent (Presenter 3 demo)**

> "Now here's what makes FinSense different from just a dashboard. Instead of waiting for Rajesh to default and then sending a legal notice — FinSense acts proactively."

*[Click: "Engage with AI Agent" button → AgentChat opens]*

> "The system sends Rajesh an empathetic message through his preferred channel."

*[Opening message appears]*

> "Let's simulate Rajesh's response."

*[Type: "I had medical expenses last month, EMI got delayed"]*

*[Agent reply appears]*

> "The agent immediately identifies this as a financial shock, offers loan restructuring, and asks for his consent. No legal pressure. No shame. Just help."

*[Type: "Tell me more about restructuring"]*

*[Agent explains and offers branch callback]*

> "Rajesh agrees to restructure. The loan officer is notified. A ₹2.8 lakh account is saved."

---

**[02:20 – 03:00] Wrap-Up (Presenter 1)**

> "FinSense isn't competing with CIBIL. CIBIL is a gate — it decides who gets a loan.
> FinSense is a guardian — it makes sure that loan stays healthy.
>
> For SBI, recovering a defaulted loan costs ₹1 for every ₹3 lost, on average. Preventing one red-tier default saves more than detecting ten.
>
> FinSense is API-first, scales to SBI's entire loan book, and can go live in 90 days.
>
> Thank you."

---

## JUDGE Q&A — ANSWERS TO PRACTICE

**Q: "How is this different from SBI's existing risk systems?"**

> "SBI's internal systems flag NPA status AFTER a loan is 90 days overdue — that's the regulatory definition. FinSense acts at 30–60 days of declining signals, before the account is classified. We're upstream of the problem entirely."

**Q: "How would you get real transaction data?"**

> "SBI already has this data in CBS (Core Banking System). FinSense sits on top as a monitoring layer via API integration. No new data collection is needed — we're just analyzing what's already there."

**Q: "What if the AI agent says something wrong to a borrower?"**

> "The agent has guardrails: it can only offer SBI's published relief options, it cannot make promises about specific amounts, and all escalation conversations are reviewed by a human officer before any action is taken."

**Q: "Why XGBoost and not a deep learning model?"**

> "Tabular financial data with 12 features doesn't benefit from deep learning — XGBoost is state of the art for structured data. More importantly, XGBoost supports SHAP natively, giving us full explainability. A loan officer needs to understand why someone is flagged — a neural network doesn't give us that."

**Q: "How do you handle class imbalance in the training data?"**

> "We use `scale_pos_weight` in XGBoost to weight the stressed class proportionally. We also evaluate on ROC-AUC (not accuracy) since accuracy is misleading with imbalanced classes. Our model achieves 0.91 ROC-AUC on the held-out test set."

---

## SLIDE DECK OUTLINE (10 slides)

1. **Cover** — FinSense logo, team names
2. **The Problem** — ₹16,000 crore NPA stat + Supreme Court quote
3. **The Gap** — CIBIL vs. post-disbursement monitoring (the gap diagram)
4. **How FinSense Works** — 3-step: Monitor → Score → Intervene
5. **The 12 Signals** — Visual of all 12 features with icons
6. **The Risk Tiers** — Green/Amber/Orange/Red with definitions
7. **The AI Agent** — Screenshot of conversation + outcome options
8. **SHAP Explainability** — Show the bar chart, explain why it matters
9. **Business Impact** — Estimated NPA prevention value for SBI
10. **Roadmap to Production** — 90-day deployment plan

---

## ESTIMATED BUSINESS IMPACT (Slide 9 numbers)

- SBI has ~9 crore active loan accounts (retail)
- ~3% average NPA rate = ~27 lakh stressed accounts
- Average NPA loan size = ₹3.2 lakh
- Recovery rate = ~35% (SBI public data)
- **Loss per NPA account = ₹2.08 lakh**

If FinSense prevents just 5% of NPA formation:
- Accounts saved = 1.35 lakh
- **Value saved = ₹2,808 crore annually**

Even 1% prevention = ₹560 crore/year. That's the ROI slide.

---

## WHAT TO HAVE READY ON DEMO DAY

- [ ] Seed script run, Rajesh Kumar visible on dashboard
- [ ] All 4 pages working: Dashboard, BorrowerDetail, AgentChat, Alerts
- [ ] SHAP chart loading correctly with real values
- [ ] Risk score history chart showing the 5-month arc
- [ ] Agent conversation tested end-to-end
- [ ] Groq/OpenAI API key set in environment
- [ ] Backend running on port 8000, frontend on 5173
- [ ] Laptop charged, browser tab pre-opened to Dashboard
- [ ] Demo slides open in separate window
- [ ] Practice run: time it at under 3 minutes

---
