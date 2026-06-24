# FinSense — NPA Prevention Intelligence Platform
## Master Context File for AI Coding Agents

---

## WHAT IS THIS PROJECT?

**FinSense** is an AI-powered, post-disbursement loan health monitoring system built specifically for SBI (State Bank of India). It continuously monitors borrower financial behaviour after a loan is given out, detects early warning signals of potential default, and proactively engages the borrower via a conversational AI agent — BEFORE the account slips into NPA (Non-Performing Asset) status.

### The Core Problem It Solves
- SBI wrote off ₹16,000+ crore in bad loans in FY24–25
- Current systems (like CIBIL) score creditworthiness ONLY at loan application time
- There is NO system that watches borrower health AFTER disbursement
- By the time a loan is flagged NPA, it's too late — recovery is expensive and often futile
- The Supreme Court in 2026 called out SBI for being "casual in granting huge loans" while harassing small borrowers

### Why FinSense Wins
FinSense is NOT another chatbot. NOT another KYC tool. NOT another credit score dashboard.  
It works UPSTREAM — catching risk 60–90 days before default. No other team will do this.

---

## CRITICAL DIFFERENTIATOR (Memorize This)

| Feature | CIBIL / Traditional | FinSense |
|---|---|---|
| Timing | At loan application | Continuously post-disbursement |
| Data used | Historical credit history | Real-time transaction patterns |
| Action | Accept/Reject | Proactive outreach + restructuring |
| Explainability | Black box score | SHAP-based per-feature explanation |
| Borrower empathy | None | AI agent with empathetic tone |

---

## TECH STACK (Team of 3)

### Person 1 — ML Engineer
- Python, scikit-learn, XGBoost, SHAP
- FastAPI (for model serving)
- Pandas, NumPy, Faker (synthetic data)

### Person 2 — Backend / DevOps
- FastAPI (REST APIs)
- SQLite (dev) → PostgreSQL (prod)
- Celery + Redis (scheduled risk re-scoring)
- WebSockets (real-time dashboard updates)

### Person 3 — Frontend Developer
- React.js + Tailwind CSS
- Recharts (risk graphs)
- React Router
- Axios (API calls)

---

## PROJECT STRUCTURE

```
finsense/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── database.py                # SQLAlchemy models + DB init
│   ├── routers/
│   │   ├── loans.py               # Loan CRUD endpoints
│   │   ├── risk.py                # Risk scoring endpoints
│   │   ├── agent.py               # AI agent conversation endpoints
│   │   └── dashboard.py           # Dashboard data endpoints
│   ├── ml/
│   │   ├── train.py               # Model training script
│   │   ├── predict.py             # Inference + SHAP explanations
│   │   ├── features.py            # Feature engineering pipeline
│   │   └── models/
│   │       ├── xgb_model.pkl      # Trained XGBoost model
│   │       └── scaler.pkl         # Feature scaler
│   ├── data/
│   │   ├── generate_synthetic.py  # Synthetic dataset generator
│   │   └── synthetic_loans.csv    # Generated dataset
│   ├── agent/
│   │   ├── conversation.py        # LLM-based agent logic
│   │   └── templates.py           # Message templates per risk tier
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx      # Main officer dashboard
│   │   │   ├── BorrowerDetail.jsx # Individual borrower risk view
│   │   │   ├── AgentChat.jsx      # AI agent conversation UI
│   │   │   └── Alerts.jsx         # High-risk alerts feed
│   │   ├── components/
│   │   │   ├── RiskGauge.jsx      # Animated risk meter
│   │   │   ├── TrendChart.jsx     # Risk score over time chart
│   │   │   ├── ShapBar.jsx        # SHAP explanation bar chart
│   │   │   ├── BorrowerCard.jsx   # Summary card component
│   │   │   └── AlertBadge.jsx     # Risk tier badge
│   │   ├── api/
│   │   │   └── client.js          # Axios API client
│   │   └── styles/
│   │       └── globals.css
│   └── package.json
│
├── docs/
│   ├── 00_PROJECT_MASTER.md       # This file
│   ├── 01_DATA_SCHEMA.md          # All data models
│   ├── 02_ML_PIPELINE.md          # ML training + inference guide
│   ├── 03_API_REFERENCE.md        # All API endpoints
│   ├── 04_FRONTEND_GUIDE.md       # UI component guide
│   ├── 05_AGENT_DESIGN.md         # AI agent logic
│   └── 06_DEMO_SCRIPT.md          # Hackathon demo script
│
└── README.md
```

---

## 30-DAY BUILD PLAN (Overview)

| Phase | Days | Goal |
|---|---|---|
| 0 — Setup | 1–2 | Repo, env, DB, project scaffold |
| 1 — Data | 3–7 | Synthetic dataset of 5000 borrowers |
| 2 — ML | 8–14 | Trained model + SHAP API endpoint |
| 3 — Backend | 15–20 | All FastAPI routes live |
| 4 — Frontend | 18–24 | Dashboard + BorrowerDetail + Alerts |
| 5 — Agent | 22–26 | AI agent conversation flow |
| 6 — Demo | 27–30 | Rehearsed 3-min demo, polish |

Phases 3 and 4 overlap intentionally — backend and frontend can build in parallel once the API contract (see 03_API_REFERENCE.md) is agreed.

---

## RISK TIER SYSTEM

FinSense classifies every borrower into one of 4 tiers after each scoring cycle:

| Tier | Score | Colour | Meaning | Action |
|---|---|---|---|---|
| GREEN | 0–30 | 🟢 | Healthy | No action |
| AMBER | 31–55 | 🟡 | Early stress | Automated check-in message |
| ORANGE | 56–75 | 🟠 | High risk | Officer review + loan restructuring offer |
| RED | 76–100 | 🔴 | Pre-default | Immediate branch escalation |

---

## SCORING FREQUENCY

- Full re-score: Every 30 days (Celery cron job)
- Trigger re-score: On any large unusual transaction (webhook)
- Manual re-score: Officer can trigger from dashboard anytime

---

## JUDGING CRITERIA TO HIT

1. **Problem Relevance** → NPA is SBI's #1 documented pain point. ✅
2. **Innovation** → No competitor or existing SBI product does post-disbursement AI monitoring. ✅
3. **Feasibility** → Full working demo with real ML inference. ✅
4. **Scalability** → API-first design, Celery workers, Postgres-ready. ✅
5. **Presentation** → One borrower, one risk journey, one proactive message. Rehearsed. ✅

---

## ELEVATOR PITCH (Practice This)

> "SBI's NPA problem is not a lending problem — it's a monitoring problem.
> CIBIL tells you who is risky before you lend. FinSense tells you who is BECOMING risky after you lend.
> We monitor 12 behavioural signals continuously, score every borrower on a 0–100 risk scale with full explainability, and deploy an empathetic AI agent to intervene 60–90 days before any default — saving SBI the cost of recovery entirely."

---
