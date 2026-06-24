import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Fetch DATABASE_URL from environment or fallback to local SQLite
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finsense.db")

# Setup SQLAlchemy engine and sessions
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)
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

# 1. Borrower Table
class Borrower(Base):
    __tablename__ = "borrowers"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    city = Column(String)
    employment_type = Column(String)
    monthly_income = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# 2. Loan Table
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

# 3. RiskScore Table
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

# 4. Transaction Table
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

# 5. Alert Table
class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True)
    loan_id = Column(String)
    alert_type = Column(String)
    severity = Column(String)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 6. AgentConversation Table
class AgentConversation(Base):
    __tablename__ = "agent_conversations"
    id = Column(String, primary_key=True)
    loan_id = Column(String)
    started_at = Column(DateTime, default=datetime.utcnow)
    channel = Column(String)
    outcome = Column(String, default='pending')
    messages = Column(Text)  # JSON array string
