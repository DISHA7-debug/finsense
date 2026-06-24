from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
import json
from datetime import datetime

from database import get_db, Loan, Borrower, AgentConversation, RiskScore
from agent.conversation import get_opening_message, continue_conversation

router = APIRouter()

class StartRequest(BaseModel):
    channel: str = "in_app"

class MessageRequest(BaseModel):
    conversation_id: str
    message: str

@router.post("/{loan_id}/start")
def start_conversation(loan_id: str, req: StartRequest, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
        
    borrower = db.query(Borrower).filter(Borrower.id == loan.borrower_id).first()
    risk = db.query(RiskScore).filter(RiskScore.loan_id == loan_id).order_by(
        RiskScore.scored_at.desc()
    ).first()
    
    if not risk:
        raise HTTPException(status_code=400, detail="Loan must be scored before starting agent conversation")
        
    risk_data = {
        "score": risk.score,
        "tier": risk.tier,
        "top_risk_factors": json.loads(risk.top_risk_factors or "[]")
    }
    
    opening = get_opening_message(loan, borrower, risk_data)
    
    convo_id = str(uuid.uuid4())
    messages = [{"role": "agent", "content": opening["message"], "timestamp": datetime.utcnow().isoformat()}]
    
    convo = AgentConversation(
        id=convo_id,
        loan_id=loan_id,
        channel=req.channel,
        messages=json.dumps(messages),
        outcome="pending"
    )
    db.add(convo)
    db.commit()
    
    return {
        "conversation_id": convo_id,
        "opening_message": opening["message"],
        "suggested_actions": opening.get("suggested_actions", []),
    }

@router.post("/{loan_id}/message")
def send_message(loan_id: str, req: MessageRequest, db: Session = Depends(get_db)):
    convo = db.query(AgentConversation).filter(
        AgentConversation.id == req.conversation_id
    ).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    borrower = db.query(Borrower).filter(Borrower.id == loan.borrower_id).first()
    risk = db.query(RiskScore).filter(RiskScore.loan_id == loan_id).order_by(
        RiskScore.scored_at.desc()
    ).first()
    
    risk_data = {
        "score": risk.score,
        "tier": risk.tier,
        "top_risk_factors": json.loads(risk.top_risk_factors or "[]")
    }
    
    messages = json.loads(convo.messages or "[]")
    
    # Add borrower message
    messages.append({"role": "borrower", "content": req.message, "timestamp": datetime.utcnow().isoformat()})
    
    # Get agent reply
    reply = continue_conversation(loan, borrower, risk_data, messages, req.message)
    
    # Add agent reply
    messages.append({"role": "agent", "content": reply["message"], "timestamp": datetime.utcnow().isoformat()})
    
    # Update conversation
    convo.messages = json.dumps(messages)
    convo.outcome = reply.get("outcome_signal", "pending")
    db.commit()
    
    return {
        "reply": reply["message"],
        "suggested_actions": reply.get("suggested_actions", []),
        "outcome_signal": reply.get("outcome_signal", "pending"),
    }

@router.get("/{loan_id}/conversations")
def get_conversations(loan_id: str, db: Session = Depends(get_db)):
    convos = db.query(AgentConversation).filter(AgentConversation.loan_id == loan_id).order_by(AgentConversation.started_at.desc()).all()
    return [
        {
            "id": c.id,
            "loan_id": c.loan_id,
            "started_at": c.started_at.isoformat() if isinstance(c.started_at, datetime) else c.started_at,
            "channel": c.channel,
            "outcome": c.outcome,
            "messages": json.loads(c.messages or "[]")
        }
        for c in convos
    ]
