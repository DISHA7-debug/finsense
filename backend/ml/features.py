import pandas as pd
import numpy as np
from scipy import stats

FEATURE_COLS = [
    'emi_missed_last_3', 'balance_trend_slope', 'bounce_count_3m',
    'income_coverage_ratio', 'credit_debit_ratio', 'utilisation_rate',
    'months_to_completion', 'late_payment_rate', 'utility_miss_rate',
    'min_balance_ratio', 'loan_to_income_ratio', 'employment_risk'
]


def build_feature_matrix(transactions_df: pd.DataFrame, loans_df: pd.DataFrame, borrowers_df: pd.DataFrame) -> pd.DataFrame:
    """Build one ML feature row per loan using the latest six transaction months."""
    feats = []
    for _, loan_data in loans_df.iterrows():
        lid = loan_data['id']
        bid = loan_data['borrower_id']
        tx = transactions_df[transactions_df['loan_id'] == lid].sort_values('month').tail(6)
        if len(tx) < 2:
            continue
        borrower_rows = borrowers_df[borrowers_df['id'] == bid]
        if borrower_rows.empty:
            continue
        borrower = borrower_rows.iloc[0]

        emi_missed_3 = int((~tx.tail(3)['emi_paid'].astype(bool)).sum())
        balances = tx['avg_balance'].astype(float).values
        months_idx = np.arange(len(balances))
        slope = stats.linregress(months_idx, balances).slope if len(balances) > 1 else 0.0
        bounce_3m = int(tx.tail(3)['bounce_count'].sum())
        avg_balance = float(tx['avg_balance'].mean())
        income_coverage = avg_balance / max(float(loan_data['emi_amount']), 1.0)
        credit_debit_ratio = float(tx['total_credits'].sum()) / max(float(tx['total_debits'].sum()), 1.0)
        utilisation = float(loan_data['outstanding_balance']) / max(float(loan_data['principal_amount']), 1.0)
        months_remaining = int(loan_data['tenure_months'] - loan_data['months_completed'])
        late_rate = float(tx['emi_paid_late'].astype(bool).mean())
        utility_miss = 1.0 - float(tx['utility_bills_paid'].astype(bool).mean())
        min_balance_ratio = float(tx['min_balance'].mean()) / max(float(loan_data['emi_amount']), 1.0)
        annual_income = float(borrower['monthly_income']) * 12.0
        loan_to_income = float(loan_data['principal_amount']) / max(annual_income, 1.0)
        emp_map = {'salaried': 0.0, 'self_employed': 0.5, 'business': 1.0}
        employment_risk = emp_map.get(str(borrower['employment_type']), 0.5)
        is_stressed = tx['is_stressed'].iloc[-1] if 'is_stressed' in tx.columns else None

        feats.append({
            'loan_id': lid,
            'borrower_id': bid,
            'emi_missed_last_3': emi_missed_3,
            'balance_trend_slope': slope,
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
