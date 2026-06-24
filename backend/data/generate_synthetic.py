import pandas as pd
import numpy as np
from faker import Faker
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

fake = Faker('en_IN')
np.random.seed(42)
random.seed(42)

N = 5000
DATA_DIR = Path(__file__).resolve().parent


def generate_borrowers(n: int) -> pd.DataFrame:
    employment_types = ['salaried', 'self_employed', 'business']
    cities = ['Mumbai', 'Delhi', 'Bengaluru', 'Chennai', 'Hyderabad',
              'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow']
    records = []
    for _ in range(n):
        emp = random.choices(employment_types, weights=[0.55, 0.30, 0.15])[0]
        if emp == 'salaried':
            income = np.random.lognormal(mean=10.5, sigma=0.5)
        elif emp == 'self_employed':
            income = np.random.lognormal(mean=10.8, sigma=0.7)
        else:
            income = np.random.lognormal(mean=11.2, sigma=0.9)
        records.append({
            'id': str(uuid.uuid4()),
            'name': fake.name(),
            'age': random.randint(21, 62),
            'city': random.choice(cities),
            'employment_type': emp,
            'monthly_income': round(min(max(income, 12000), 600000), 2),
        })
    return pd.DataFrame(records)


def generate_loans(borrowers_df: pd.DataFrame) -> pd.DataFrame:
    loan_types = ['home', 'personal', 'business', 'vehicle', 'education']
    loan_configs = {
        'home': {'range': (500000, 8000000), 'tenure': (120, 240), 'rate': (7.5, 9.5)},
        'personal': {'range': (50000, 500000), 'tenure': (12, 60), 'rate': (11.0, 16.0)},
        'business': {'range': (200000, 5000000), 'tenure': (36, 84), 'rate': (10.0, 14.0)},
        'vehicle': {'range': (200000, 2000000), 'tenure': (36, 84), 'rate': (8.5, 11.0)},
        'education': {'range': (100000, 2000000), 'tenure': (60, 120), 'rate': (8.0, 10.0)},
    }
    records = []
    for _, b in borrowers_df.iterrows():
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
        months_done = random.randint(2, tenure - 1)  # >=2 so feature rows are available
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


def generate_risk_profile(loan_row: pd.Series, borrower_row: pd.Series) -> float:
    income = borrower_row['monthly_income']
    emi = loan_row['emi_amount']
    emp = borrower_row['employment_type']
    base_risk = 0.15
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
        base_risk += 0.05
    return min(base_risk, 0.90)


def generate_transactions(loans_df: pd.DataFrame, borrowers_df: pd.DataFrame) -> pd.DataFrame:
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
                stress_level = min(m / 6, 1.0) if m > 3 else 0
                credits = round(income * random.uniform(0.7, 1.0), 2)
                debits = round(credits * random.uniform(0.85, 1.10), 2)
                avg_balance = round(random.uniform(emi * 0.2, emi * 1.2), 2)
                min_balance = round(avg_balance * random.uniform(0.0, 0.5), 2)
                emi_paid = random.random() > (0.2 + stress_level * 0.5)
                emi_late = (not emi_paid) or random.random() < 0.4
                bounce = random.randint(0, 3) if stress_level > 0.3 else random.randint(0, 1)
                utility = random.random() > 0.3
            else:
                credits = round(income * random.uniform(0.95, 1.15), 2)
                debits = round(credits * random.uniform(0.60, 0.85), 2)
                avg_balance = round(random.uniform(emi * 1.5, emi * 5), 2)
                min_balance = round(avg_balance * random.uniform(0.4, 0.9), 2)
                emi_paid = random.random() > 0.04
                emi_late = (not emi_paid) or random.random() < 0.08
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
                'is_stressed': is_stressed,
            })
    return pd.DataFrame(records)


if __name__ == '__main__':
    print('Generating borrowers...')
    borrowers = generate_borrowers(N)
    print('Generating loans...')
    loans = generate_loans(borrowers)
    print('Generating transactions...')
    transactions = generate_transactions(loans, borrowers)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    borrowers.to_csv(DATA_DIR / 'synthetic_borrowers.csv', index=False)
    loans.to_csv(DATA_DIR / 'synthetic_loans.csv', index=False)
    transactions.to_csv(DATA_DIR / 'synthetic_transactions.csv', index=False)

    stressed = transactions[transactions['is_stressed'] == True]['borrower_id'].nunique()
    print('\nDone! Stats:')
    print(f'  Borrowers: {len(borrowers):,}')
    print(f'  Loans: {len(loans):,}')
    print(f'  Transaction rows: {len(transactions):,}')
    print(f'  Stressed borrowers: {stressed:,} ({stressed/N*100:.1f}%)')
    print(f'  Output folder: {DATA_DIR}')
