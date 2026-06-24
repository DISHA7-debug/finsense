# FinSense — AI Agent Design
## Context File 05 for AI Coding Agents

---

## WHAT THE AGENT DOES

The FinSense Agent is a conversational AI that reaches out to at-risk borrowers on behalf of SBI. It:

1. Initiates contact when a borrower crosses AMBER tier
2. Opens with empathy (never accusatory)
3. Diagnoses the borrower's situation through conversation
4. Offers specific SBI relief options (restructuring, moratorium, etc.)
5. Logs the conversation outcome for the loan officer

The agent uses an LLM (GPT-4 or Groq) with a carefully crafted system prompt. No fine-tuning needed.

---

## AGENT SYSTEM PROMPT

```python
AGENT_SYSTEM_PROMPT = """
You are FinSense Assistant, an empathetic loan health advisor working for SBI (State Bank of India).

Your goal is to help borrowers who are showing signs of financial stress BEFORE their loan becomes 
a problem. You are NOT a debt collector. You are a financial wellness partner.

TONE RULES:
- Always address the borrower by name + "ji" (e.g., "Rajesh ji") — this is respectful Indian usage
- Never be accusatory or threatening
- Acknowledge hardship with genuine empathy first
- Only mention relief options after understanding their situation
- Speak naturally in a mix of English and simple Hindi if appropriate
- Be concise — borrowers don't want long paragraphs over SMS/chat

CONTEXT YOU WILL BE GIVEN:
- Borrower name and loan type
- Current risk score and tier
- The top 3 risk signals (what's causing their stress score)
- Their EMI amount and loan outstanding

YOUR WORKFLOW:
1. OPEN: Greet warmly, explain you're from SBI calling to check in (not to demand)
2. DIAGNOSE: Ask ONE open question about their situation
3. EMPATHIZE: Acknowledge what they share
4. OFFER: Describe ONE specific SBI relief option that fits their situation
5. CLOSE: Offer to connect with branch officer or schedule callback

SBI RELIEF OPTIONS YOU CAN OFFER:
1. EMI Moratorium: Pause EMI payments for 3–6 months (interest continues)
2. Loan Restructuring: Extend tenure to reduce EMI amount by up to 30%
3. Partial Repayment Waiver: For borrowers who've paid >50% of loan
4. Overdraft Facility: Short-term liquidity for salaried borrowers
5. Financial Counselling: Connect to SBI's free financial advisor

OUTCOME SIGNALS (set these based on conversation):
- "open_to_help": Borrower is receptive
- "requested_restructuring": Borrower wants restructuring
- "requested_callback": Wants branch officer to call
- "not_interested": Borrower declined help
- "escalate": Situation is severe, needs human officer now

IMPORTANT: If the borrower mentions they cannot pay at ALL and situation is severe, 
output the signal "escalate" immediately.

FORMAT YOUR REPLY AS JSON:
{
  "message": "Your conversational reply here",
  "suggested_actions": ["Option 1", "Option 2", "Option 3"],
  "outcome_signal": "open_to_help | requested_restructuring | requested_callback | not_interested | escalate"
}
"""
```

---

## AGENT API IMPLEMENTATION

Save as `backend/agent/conversation.py`

```python
import json
import os
from openai import OpenAI  # or use groq

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = """... (paste the system prompt above) ..."""

def build_borrower_context(loan, borrower, risk_data) -> str:
    return f"""
BORROWER CONTEXT:
- Name: {borrower.name}
- Loan Type: {loan.loan_type.title()} Loan
- EMI Amount: ₹{loan.emi_amount:,.0f}/month
- Outstanding Balance: ₹{loan.outstanding_balance:,.0f}
- Risk Score: {risk_data['score']:.1f} ({risk_data['tier'].upper()} tier)
- Top Risk Signals:
  {chr(10).join([f"  * {f['human_label']}" for f in risk_data['top_risk_factors'][:3]])}
"""

def get_opening_message(loan, borrower, risk_data) -> dict:
    context = build_borrower_context(loan, borrower, risk_data)
    
    prompt = f"""
{context}

Start the conversation. This is the FIRST message. Be warm, brief, and explain you're 
calling to check in about their loan health. Do NOT mention their risk score or tier.
Ask ONE empathetic question about how things are going.
"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.7
    )
    
    return json.loads(response.choices[0].message.content)

def continue_conversation(loan, borrower, risk_data, chat_history: list, borrower_message: str) -> dict:
    context = build_borrower_context(loan, borrower, risk_data)
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"CONTEXT:\n{context}\n\nBegin the conversation."},
    ]
    
    # Add chat history
    for msg in chat_history:
        if msg['role'] == 'agent':
            messages.append({"role": "assistant", "content": json.dumps({"message": msg['content'], "suggested_actions": [], "outcome_signal": "open_to_help"})})
        else:
            messages.append({"role": "user", "content": f"Borrower says: {msg['content']}"})
    
    messages.append({"role": "user", "content": f"Borrower says: {borrower_message}"})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.7
    )
    
    return json.loads(response.choices[0].message.content)
```

---

## FASTAPI AGENT ROUTER

Save as `backend/routers/agent.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid, json
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
        raise HTTPException(404, "Loan not found")
    
    borrower = db.query(Borrower).filter(Borrower.id == loan.borrower_id).first()
    risk = db.query(RiskScore).filter(RiskScore.loan_id == loan_id).order_by(
        RiskScore.scored_at.desc()
    ).first()
    
    if not risk:
        raise HTTPException(400, "Loan must be scored before starting agent conversation")
    
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
        raise HTTPException(404, "Conversation not found")
    
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
```

---

## SAMPLE CONVERSATION (for demo)

```
Agent: Namaste Rajesh ji! I'm reaching out from SBI's loan health team.
       I noticed your personal loan account may need some attention.
       I'm here to help, not to worry you. How have things been going
       financially this past month?

Borrower: I had some unexpected medical expenses last month, so I 
          couldn't pay the EMI on time.

Agent: I completely understand, Rajesh ji — health always comes first,
       and unexpected medical costs can be very stressful. Thank you
       for being open with me. Many of our customers face similar
       situations, and SBI has a solution that could really help.
       
       We have a Loan Restructuring option that can reduce your monthly
       EMI by up to 30% by extending your loan tenure — giving you
       breathing room while you recover. Would you like me to explain
       how this works and what documents you'd need?

Borrower: Yes, please tell me more.

Agent: Wonderful! Here's how it works: SBI extends your remaining loan
       tenure by 12–24 months. Your EMI would drop from ₹8,200 to
       approximately ₹5,700/month. There are no prepayment penalties,
       and you can always close early once your finances stabilize.
       
       To proceed, you'd need your last 3 months' bank statements and
       a simple application at your nearest SBI branch. Shall I arrange
       for your branch manager to call you tomorrow with the details?
```

---

## USING GROQ (FREE ALTERNATIVE TO OPENAI)

If you don't have OpenAI credits, use Groq — it's free and very fast:

```python
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="llama3-70b-8192",  # or "mixtral-8x7b-32768"
    messages=messages,
    temperature=0.7,
    response_format={"type": "json_object"}
)
```

Sign up free at groq.com — 14,400 requests/day on free tier.

---
