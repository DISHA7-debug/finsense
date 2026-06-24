# FinSense — Context Files Index
## Feed these to your AI coding agent in order

---

## FILES IN THIS PACKAGE

| File | What It Contains | Feed This To Agent When... |
|---|---|---|
| `00_PROJECT_MASTER.md` | Full project overview, tech stack, folder structure, risk tiers | Starting any new coding session — always include this |
| `01_DATA_SCHEMA.md` | All DB tables, 12 ML features, complete data generation script | Building the database or generating synthetic data |
| `02_ML_PIPELINE.md` | Training script, inference module, SHAP explanation | Training the model or building the `/api/risk` endpoint |
| `03_API_REFERENCE.md` | All FastAPI routes with full implementations | Building backend routes |
| `04_FRONTEND_GUIDE.md` | React components, Tailwind setup, routing | Building any frontend page or component |
| `05_AGENT_DESIGN.md` | LLM system prompt, conversation logic, Groq/OpenAI setup | Building the AI agent feature |
| `06_DEMO_SCRIPT.md` | 3-min demo script, seed data, Q&A prep, slide outline | Preparing for the hackathon presentation |

---

## HOW TO USE WITH AI CODING AGENTS (Cursor / Windsurf / Claude Code)

### For each coding session:

1. **Always include `00_PROJECT_MASTER.md`** as the first context file — it's the map
2. Add the specific file for what you're building today
3. Tell the agent your goal clearly

### Example prompts to give your agent:

**Starting data generation:**
```
Using the context in 00_PROJECT_MASTER.md and 01_DATA_SCHEMA.md,
create the file backend/data/generate_synthetic.py exactly as specified
and run it to generate 5000 borrower records.
```

**Starting ML training:**
```
Using 00_PROJECT_MASTER.md and 02_ML_PIPELINE.md,
create backend/ml/features.py and backend/ml/train.py,
then train the XGBoost model and save it to backend/ml/models/.
```

**Starting backend:**
```
Using 00_PROJECT_MASTER.md and 03_API_REFERENCE.md,
scaffold the full FastAPI backend with all routers and database models.
Start with main.py and database.py.
```

**Starting frontend:**
```
Using 00_PROJECT_MASTER.md and 04_FRONTEND_GUIDE.md,
build the Dashboard.jsx page and the RiskGauge, ShapBar, TrendChart components.
Connect them to the API client.
```

**Building the agent:**
```
Using 00_PROJECT_MASTER.md and 05_AGENT_DESIGN.md,
implement the agent conversation module and the /api/agent router.
Use Groq with llama3-70b-8192 as the LLM.
```

---

## 30-DAY BUILD ORDER

```
Week 1 (Days 1–7):   Setup + Synthetic Data
  Day 1–2: Repo setup, install dependencies, scaffold folder structure
  Day 3–4: generate_synthetic.py → run → verify CSV outputs
  Day 5–7: features.py → build_feature_matrix → verify feature outputs

Week 2 (Days 8–14):  ML Core
  Day 8–10:  train.py → train XGBoost → save model files
  Day 11–12: predict.py → test inference locally
  Day 13–14: FastAPI setup → /api/risk endpoint → test with Postman

Week 3 (Days 15–22): Backend + Frontend Parallel
  Day 15–17: All backend routes (dashboard, loans, alerts)
  Day 18–20: Dashboard.jsx + BorrowerDetail.jsx
  Day 21–22: AgentChat.jsx + Alert page

Week 4 (Days 23–30): Agent + Polish + Demo
  Day 23–25: AI Agent full implementation (Groq)
  Day 26–27: Seed demo data, end-to-end testing
  Day 28–29: Slide deck + demo rehearsal
  Day 30:    Presentation day ✅
```

---

## ENVIRONMENT VARIABLES NEEDED

Create a `.env` file in `backend/`:

```
GROQ_API_KEY=your_groq_api_key_here
# OR
OPENAI_API_KEY=your_openai_key_here

DATABASE_URL=sqlite:///./finsense.db
```

Get free Groq key at: https://console.groq.com
Free tier: 14,400 requests/day — more than enough for demo.

---

## GOOD LUCK 🏆

The idea is strong. The implementation is achievable in 30 days.
The demo is tight and rehearsed.

What wins hackathons: a working demo that tells a clear story.
FinSense has both.
```
