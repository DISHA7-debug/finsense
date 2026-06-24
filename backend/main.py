from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import loans, risk, agent, dashboard, alerts
from database import init_db

app = FastAPI(
    title="FinSense API",
    description="NPA Prevention Intelligence Platform for SBI",
    version="1.0.0"
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()

# Include routers
app.include_router(loans.router, prefix="/api/loans", tags=["Loans"])
app.include_router(risk.router, prefix="/api/risk", tags=["Risk Scoring"])
app.include_router(agent.router, prefix="/api/agent", tags=["AI Agent"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(alerts.router, prefix="/api/dashboard", tags=["Alerts"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "FinSense"}
