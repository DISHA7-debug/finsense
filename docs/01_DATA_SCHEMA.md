# FinSense — Data Schema & Synthetic Data Generation
## Context File 01 for AI Coding Agents

---

## OVERVIEW

FinSense uses **synthetic data** because SBI's real loan data is confidential. The synthetic data must be realistic enough to train a meaningful ML model. We use the Python `Faker` library + domain-specific rules to generate 5000 borrower records.

---

## CORE DATABASE TABLES

### 1. `borrowers`
Represents a loan customer.

```sql
CREATE TABLE borrowers (
    id              TEXT PRIMARY KEY,          -- UUID
    name            TEXT NOT NULL,
    age             INTEGER,                   -- 21–65
    city            TEXT,
    employment_type TEXT,                      -- salaried | self_employed | business
    monthly_income  REAL,                      -- INR, 15000–500000
    created_at      TIMESTAMP DEFAULT NOW()
);
```

### 2. `loans`
One borrower can have multiple loans.

```sql
CREATE TABLE loans (
    id                  TEXT PRIMARY KEY,       -- UUID
    borrower_id         TEXT REFERENCES borrowers(id),
    loan_type           TEXT,                  -- home | personal | business | vehicle | education
    principal_amount    REAL,                  -- INR
    outstanding_balance REAL,                  -- Current remaining balance
    emi_amount          REAL,                  -- Monthly EMI
    interest_rate       REAL,                  -- Annual %
    tenure_months       INTEGER,               -- Total tenure
    months_completed    INTEGER,               -- How many paid so far
    disbursement_date   DATE,
    next_emi_date       DATE,
    status              TEXT DEFAULT 'active', -- active | closed | npa | restructured
    created_at          TIMESTAMP DEFAULT NOW()
);
```

### 3. `risk_scores`
A time-series of risk scores. New row added every scoring cycle.

```sql
CREATE TABLE risk_scores (
    id              TEXT PRIMARY KEY,
    loan_id         TEXT REFERENCES loans(id),
    score           REAL,                      -- 0.0 to 100.0
    tier            TEXT,                      -- green | amber | orange | red
    scored_at       TIMESTAMP DEFAULT NOW(),
    shap_values     TEXT,                      -- JSON: {feature: shap_value}
    trigger         TEXT                       -- scheduled | manual | transaction_spike
);
```

### 4. `transactions`
Monthly financial behaviour summary per borrower.

```sql
CREATE TABLE transactions (
    id                      TEXT PRIMARY KEY,
    borrower_id             TEXT REFERENCES borrowers(id),
    month                   TEXT,              -- YYYY-MM
    credits_count           INTEGER,           -- Number of credit transactions
    debits_count            INTEGER,           -- Number of debit transactions
    total_credits           REAL,              -- Total money in
    total_debits            REAL,              -- Total money out
    avg_balance             REAL,              -- Average monthly balance
    min_balance             REAL,              -- Lowest point in month
    emi_paid                BOOLEAN,           -- Was EMI paid this month?
    emi_paid_late           BOOLEAN,           -- Was it paid after due date?
    bounce_count            INTEGER,           -- Cheque/ECS bounces
    utility_bills_paid      BOOLEAN,           -- Electricity, water etc.
    created_at              TIMESTAMP DEFAULT NOW()
);
```

### 5. `agent_conversations`
Stores AI agent chat history per borrower.

```sql
CREATE TABLE agent_conversations (
    id              TEXT PRIMARY KEY,
    loan_id         TEXT REFERENCES loans(id),
    started_at      TIMESTAMP DEFAULT NOW(),
    channel         TEXT,                      -- sms | whatsapp | in_app
    outcome         TEXT,                      -- pending | restructured | ignored | escalated
    messages        TEXT                       -- JSON array of {role, content, timestamp}
);
```

### 6. `alerts`
System-generated alerts for loan officers.

```sql
CREATE TABLE alerts (
    id              TEXT PRIMARY KEY,
    loan_id         TEXT REFERENCES loans(id),
    alert_type      TEXT,                      -- tier_upgrade | missed_emi | balance_drop | bounce
    severity        TEXT,                      -- info | warning | critical
    message         TEXT,
    is_read         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## THE 12 RISK FEATURES (ML Input)

These 12 features are derived from `transactions` + `loans` tables and fed into the ML model:

| # | Feature Name | Derivation | Why It Matters |
|---|---|---|---|
| 1 | `emi_missed_last_3` | Count of months with emi_paid=False in last 3 months | Strongest predictor of NPA |
| 2 | `balance_trend_slope` | Linear regression slope of avg_balance over 6 months | Falling balance = stress |
| 3 | `bounce_count_3m` | Sum of bounce_count last 3 months | Bounces = liquidity crisis |
| 4 | `income_coverage_ratio` | avg_balance / emi_amount | Can they actually afford EMI? |
| 5 | `credit_debit_ratio` | total_credits / total_debits | Money in vs money out |
| 6 | `utilisation_rate` | outstanding_balance / principal_amount | How deep in the loan |
| 7 | `months_to_completion` | tenure_months - months_completed | Risk spikes near end |
| 8 | `late_payment_rate` | emi_paid_late count / months_completed | Pattern of being late |
| 9 | `utility_miss_rate` | months utility unpaid / total months | Failing to pay basics |
| 10 | `min_balance_ratio` | min_balance / emi_amount | Safety buffer |
| 11 | `loan_to_income_ratio` | principal_amount / (monthly_income * 12) | Overextension |
| 12 | `employment_risk` | Encoded: salaried=0, self_employed=0.5, business=1 | Business owners riskier |

---

## SYNTHETIC DATA GENERATION — Full Script

Save as `backend/data/generate_synthetic.py`

```python
import pandas as pd
import numpy as np
from faker import Faker
import uuid
import random
from datetime import datetime, timedelta

fake = Faker('en_IN')
np.random.seed(42)
random.seed(42)

N = 5000  # Number of borrowers

def generate_borrowers(n):
    employment_types = ['salaried', 'self_employed', 'business']
    cities = ['Mumbai', 'Delhi', 'Bengaluru', 'Chennai', 'Hyderabad', 
              'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow']
    
    records = []
    for _ in range(n):
        emp = random.choices(employment_types, weights=[0.55, 0.30, 0.15])[0]
        if emp == 'salaried':
            income = np.random.lognormal(mean=10.5, sigma=0.5)  # ~30k–1.5L
        elif emp == 'self_employed':
            income = np.random.lognormal(mean=10.8, sigma=0.7)  # More variable
        else:
            income = np.random.lognormal(mean=11.2, sigma=0.9)  # Higher but riskier
        
        records.append({
            'id': str(uuid.uuid4()),
            'name': fake.name(),
            'age': random.randint(21, 62),
            'city': random.choice(cities),
            'employment_type': emp,
            'monthly_income': round(min(max(income, 12000), 600000), 2),
        })
    return pd.DataFrame(records)

def generate_loans(borrowers_df):
    loan_types = ['home', 'personal', 'business', 'vehicle', 'education']
    loan_configs = {
        'home':      {'range': (500000, 8000000), 'tenure': (120, 240), 'rate': (7.5, 9.5)},
        'personal':  {'range': (50000, 500000),   'tenure': (12, 60),   'rate': (11.0, 16.0)},
        'business':  {'range': (200000, 5000000), 'tenure': (36, 84),   'rate': (10.0, 14.0)},
        'vehicle':   {'range': (200000, 2000000), 'tenure': (36, 84),   'rate': (8.5, 11.0)},
        'education': {'range': (100000, 2000000), 'tenure': (60, 120),  'rate': (8.0, 10.0)},
    }
    
    records = []
    for _, b in borrowers_df.iterrows():
        # Weighted loan type by employment
        if b['employment_type'] == 'salaried':
            lt = random.choices(loan_types, weights=[0.35, 0.30, 0.05, 0.25, 0.05])[0]
        elif b['employment_type'] == 'self_employed':
            lt = random.choices(loan_types, weights=[0.25, 0.25, 0.30, 0.15, 0.05])[0]
        else:
            lt = random.choices(loan_types, weights=[0.20, 0.15, 0.45, 0.15, 0.05])[0]
        
        cfg = loan_configs[lt]
        principal = round(random.uniform(*cfg['range']), -3)
        tenure = random.randint(*cfg['tenure'])
        rate = round(random.uniform(*cfg['rate']), 2)
        months_done = random.randint(1, tenure - 1)
        
        monthly_rate = rate / (12 * 100)
        emi = principal * monthly_rate * (1 + monthly_rate)**tenure / ((1 + monthly_rate)**tenure - 1)
        outstanding = principal * ((1 + monthly_rate)**tenure - (1 + monthly_rate)**months_done) / ((1 + monthly_rate)**tenure - 1)
        
        disbursement = datetime.now() - timedelta(days=months_done * 30)
        
        records.append({
            'id': str(uuid.uuid4()),
            'borrower_id': b['id'],
            'loan_type': lt,
            'principal_amount': round(principal, 2),
            'outstanding_balance': round(outstanding, 2),
            'emi_amount': round(emi, 2),
            'interest_rate': rate,
            'tenure_months': tenure,
            'months_completed': months_done,
            'disbursement_date': disbursement.date(),
            'status': 'active',
        })
    return pd.DataFrame(records)

def generate_risk_profile(loan_row, borrower_row):
    """
    Deterministically assign a risk profile based on loan and borrower characteristics.
    Risk increases if:
    - EMI > 50% of income
    - Business/self-employed
    - Low months completed (early in loan)
    - High loan-to-income ratio
    """
    income = borrower_row['monthly_income']
    emi = loan_row['emi_amount']
    emp = borrower_row['employment_type']
    
    base_risk = 0.15  # 15% base probability of stress
    if emi / income > 0.5:
        base_risk += 0.25
    if emi / income > 0.7:
        base_risk += 0.20
    if emp == 'business':
        base_risk += 0.15
    if emp == 'self_employed':
        base_risk += 0.08
    if loan_row['loan_type'] == 'personal':
        base_risk += 0.10
    if loan_row['months_completed'] < 6:
        base_risk += 0.05  # Early stress detection
    
    return min(base_risk, 0.90)

def generate_transactions(loans_df, borrowers_df):
    borrowers_map = borrowers_df.set_index('id').to_dict('index')
    records = []
    
    for _, loan in loans_df.iterrows():
        borrower = borrowers_map[loan['borrower_id']]
        risk_prob = generate_risk_profile(loan, borrower)
        is_stressed = random.random() < risk_prob
        
        for m in range(loan['months_completed']):
            month_str = (datetime.now() - timedelta(days=(loan['months_completed'] - m) * 30)).strftime('%Y-%m')
            
            income = borrower['monthly_income']
            emi = loan['emi_amount']
            
            if is_stressed:
                # Stressed borrower patterns
                stress_level = min(m / 6, 1.0) if m > 3 else 0  # Stress worsens over time
                credits = round(income * random.uniform(0.7, 1.0), 2)
                debits = round(credits * random.uniform(0.85, 1.10), 2)
                avg_balance = round(random.uniform(emi * 0.2, emi * 1.2), 2)
                min_balance = round(avg_balance * random.uniform(0.0, 0.5), 2)
                emi_paid = random.random() > (0.2 + stress_level * 0.5)
                emi_late = not emi_paid or random.random() < 0.4
                bounce = random.randint(0, 3) if stress_level > 0.3 else random.randint(0, 1)
                utility = random.random() > 0.3
            else:
                # Healthy borrower patterns
                credits = round(income * random.uniform(0.95, 1.15), 2)
                debits = round(credits * random.uniform(0.60, 0.85), 2)
                avg_balance = round(random.uniform(emi * 1.5, emi * 5), 2)
                min_balance = round(avg_balance * random.uniform(0.4, 0.9), 2)
                emi_paid = random.random() > 0.04
                emi_late = not emi_paid or random.random() < 0.08
                bounce = random.randint(0, 1) if random.random() < 0.05 else 0
                utility = random.random() > 0.05
            
            records.append({
                'id': str(uuid.uuid4()),
                'borrower_id': loan['borrower_id'],
                'loan_id': loan['id'],
                'month': month_str,
                'credits_count': random.randint(3, 15),
                'debits_count': random.randint(10, 40),
                'total_credits': credits,
                'total_debits': debits,
                'avg_balance': avg_balance,
                'min_balance': min_balance,
                'emi_paid': emi_paid,
                'emi_paid_late': emi_late,
                'bounce_count': bounce,
                'utility_bills_paid': utility,
                'is_stressed': is_stressed,  # Ground truth label
            })
    
    return pd.DataFrame(records)

if __name__ == '__main__':
    print("Generating borrowers...")
    borrowers = generate_borrowers(N)
    
    print("Generating loans...")
    loans = generate_loans(borrowers)
    
    print("Generating transactions (this takes ~2 min)...")
    transactions = generate_transactions(loans, borrowers)
    
    borrowers.to_csv('synthetic_borrowers.csv', index=False)
    loans.to_csv('synthetic_loans.csv', index=False)
    transactions.to_csv('synthetic_transactions.csv', index=False)
    
    stressed = transactions[transactions['is_stressed'] == True]['borrower_id'].nunique()
    print(f"\nDone! Stats:")
    print(f"  Borrowers: {len(borrowers)}")
    print(f"  Loans: {len(loans)}")
    print(f"  Transaction rows: {len(transactions)}")
    print(f"  Stressed borrowers: {stressed} ({stressed/N*100:.1f}%)")
```

---

## FEATURE ENGINEERING SCRIPT

Save as `backend/ml/features.py`

```python
import pandas as pd
import numpy as np
from scipy import stats

def build_feature_matrix(transactions_df, loans_df, borrowers_df):
    """
    Given raw tables, produce one feature row per loan.
    Returns DataFrame ready for ML model.
    """
    feats = []
    
    for loan_id, loan_data in loans_df.iterrows():
        lid = loan_data['id']
        bid = loan_data['borrower_id']
        
        # Get last 6 months of transactions for this loan
        tx = transactions_df[
            (transactions_df['loan_id'] == lid)
        ].sort_values('month').tail(6)
        
        if len(tx) < 2:
            continue
        
        borrower = borrowers_df[borrowers_df['id'] == bid].iloc[0]
        
        # Feature 1: EMI missed last 3 months
        emi_missed_3 = int((~tx.tail(3)['emi_paid']).sum())
        
        # Feature 2: Balance trend slope (linear regression)
        balances = tx['avg_balance'].values
        months_idx = np.arange(len(balances))
        if len(balances) > 1:
            slope, _, _, _, _ = stats.linregress(months_idx, balances)
        else:
            slope = 0
        balance_trend_slope = slope
        
        # Feature 3: Bounce count last 3 months
        bounce_3m = int(tx.tail(3)['bounce_count'].sum())
        
        # Feature 4: Income coverage ratio
        avg_balance = tx['avg_balance'].mean()
        income_coverage = avg_balance / max(loan_data['emi_amount'], 1)
        
        # Feature 5: Credit/debit ratio
        total_credits = tx['total_credits'].sum()
        total_debits = tx['total_debits'].sum()
        credit_debit_ratio = total_credits / max(total_debits, 1)
        
        # Feature 6: Utilisation rate
        utilisation = loan_data['outstanding_balance'] / max(loan_data['principal_amount'], 1)
        
        # Feature 7: Months to completion
        months_remaining = loan_data['tenure_months'] - loan_data['months_completed']
        
        # Feature 8: Late payment rate
        late_rate = tx['emi_paid_late'].mean()
        
        # Feature 9: Utility miss rate
        utility_miss = 1 - tx['utility_bills_paid'].mean()
        
        # Feature 10: Min balance ratio
        min_bal = tx['min_balance'].mean()
        min_balance_ratio = min_bal / max(loan_data['emi_amount'], 1)
        
        # Feature 11: Loan to income ratio
        annual_income = borrower['monthly_income'] * 12
        loan_to_income = loan_data['principal_amount'] / max(annual_income, 1)
        
        # Feature 12: Employment risk encoding
        emp_map = {'salaried': 0.0, 'self_employed': 0.5, 'business': 1.0}
        employment_risk = emp_map.get(borrower['employment_type'], 0.5)
        
        # Ground truth (for training only)
        is_stressed = tx['is_stressed'].iloc[-1] if 'is_stressed' in tx.columns else None
        
        feats.append({
            'loan_id': lid,
            'borrower_id': bid,
            'emi_missed_last_3': emi_missed_3,
            'balance_trend_slope': balance_trend_slope,
            'bounce_count_3m': bounce_3m,
            'income_coverage_ratio': income_coverage,
            'credit_debit_ratio': credit_debit_ratio,
            'utilisation_rate': utilisation,
            'months_to_completion': months_remaining,
            'late_payment_rate': late_rate,
            'utility_miss_rate': utility_miss,
            'min_balance_ratio': min_balance_ratio,
            'loan_to_income_ratio': loan_to_income,
            'employment_risk': employment_risk,
            'label': is_stressed,
        })
    
    return pd.DataFrame(feats)

FEATURE_COLS = [
    'emi_missed_last_3', 'balance_trend_slope', 'bounce_count_3m',
    'income_coverage_ratio', 'credit_debit_ratio', 'utilisation_rate',
    'months_to_completion', 'late_payment_rate', 'utility_miss_rate',
    'min_balance_ratio', 'loan_to_income_ratio', 'employment_risk'
]
```

---
