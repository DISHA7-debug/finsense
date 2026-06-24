import os
import json
from groq import Groq

# Initialize Groq client
# Fallback to empty string if GROQ_API_KEY is not defined, to prevent validation errors at startup
client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

SYSTEM_PROMPT = """
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

def build_borrower_context(loan, borrower, risk_data) -> str:
    factors = risk_data.get('top_risk_factors', [])
    factor_lines = "\n".join([f"  * {f['human_label']}" for f in factors[:3]])
    return f"""
BORROWER CONTEXT:
- Name: {borrower.name}
- Loan Type: {loan.loan_type.title()} Loan
- EMI Amount: ₹{loan.emi_amount:,.0f}/month
- Outstanding Balance: ₹{loan.outstanding_balance:,.0f}
- Risk Score: {risk_data['score']:.1f} ({risk_data['tier'].upper()} tier)
- Top Risk Signals:
{factor_lines}
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
        model="llama3-70b-8192",
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
            messages.append({
                "role": "assistant",
                "content": json.dumps({
                    "message": msg['content'],
                    "suggested_actions": [],
                    "outcome_signal": "open_to_help"
                })
            })
        else:
            messages.append({"role": "user", "content": f"Borrower says: {msg['content']}"})
            
    messages.append({"role": "user", "content": f"Borrower says: {borrower_message}"})
    
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.7
    )
    
    return json.loads(response.choices[0].message.content)
