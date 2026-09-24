"""Fake banking data for the demo. One hardcoded demo user is enough —
this is a prop for a talk, not a real bank. Balances are mutable module
state so the dashboard reflects any simulated activity."""

DEMO_USER = {"username": "demo", "password": "demo123"}

ACCOUNTS = [
    {"id": "chk-001", "type": "checking", "name": "Everyday Checking", "balance": 4231.55},
    {"id": "sav-001", "type": "savings", "name": "High-Yield Savings", "balance": 18250.00, "apy": 4.25},
]

# ~4 months of transactions across both accounts, enough to build a
# money-in vs money-out chart. Amounts: positive = money in, negative = out.
TRANSACTIONS = [
    # June
    {"id": "t1", "account_id": "chk-001", "date": "2026-06-02", "desc": "Payroll Deposit", "amount": 3200.00},
    {"id": "t2", "account_id": "chk-001", "date": "2026-06-05", "desc": "Rent", "amount": -1850.00},
    {"id": "t3", "account_id": "chk-001", "date": "2026-06-08", "desc": "Whole Foods", "amount": -142.30},
    {"id": "t4", "account_id": "chk-001", "date": "2026-06-16", "desc": "Payroll Deposit", "amount": 3200.00},
    {"id": "t5", "account_id": "chk-001", "date": "2026-06-20", "desc": "Netflix", "amount": -15.49},
    {"id": "t6", "account_id": "sav-001", "date": "2026-06-15", "desc": "Interest Payment", "amount": 58.40},
    # July
    {"id": "t7", "account_id": "chk-001", "date": "2026-07-02", "desc": "Payroll Deposit", "amount": 3200.00},
    {"id": "t8", "account_id": "chk-001", "date": "2026-07-05", "desc": "Rent", "amount": -1850.00},
    {"id": "t9", "account_id": "chk-001", "date": "2026-07-10", "desc": "Whole Foods", "amount": -168.90},
    {"id": "t10", "account_id": "chk-001", "date": "2026-07-16", "desc": "Payroll Deposit", "amount": 3200.00},
    {"id": "t11", "account_id": "chk-001", "date": "2026-07-22", "desc": "Flight - Air Canada", "amount": -420.00},
    {"id": "t12", "account_id": "sav-001", "date": "2026-07-15", "desc": "Interest Payment", "amount": 60.10},
    # August
    {"id": "t13", "account_id": "chk-001", "date": "2026-08-02", "desc": "Payroll Deposit", "amount": 3200.00},
    {"id": "t14", "account_id": "chk-001", "date": "2026-08-05", "desc": "Rent", "amount": -1850.00},
    {"id": "t15", "account_id": "chk-001", "date": "2026-08-12", "desc": "Whole Foods", "amount": -151.20},
    {"id": "t16", "account_id": "chk-001", "date": "2026-08-16", "desc": "Payroll Deposit", "amount": 3200.00},
    {"id": "t17", "account_id": "chk-001", "date": "2026-08-19", "desc": "Netflix", "amount": -15.49},
    {"id": "t18", "account_id": "sav-001", "date": "2026-08-15", "desc": "Interest Payment", "amount": 61.85},
    # September (current month)
    {"id": "t19", "account_id": "chk-001", "date": "2026-09-02", "desc": "Payroll Deposit", "amount": 3200.00},
    {"id": "t20", "account_id": "chk-001", "date": "2026-09-05", "desc": "Rent", "amount": -1850.00},
    {"id": "t21", "account_id": "chk-001", "date": "2026-09-18", "desc": "Payroll Deposit", "amount": 3200.00},
    {"id": "t22", "account_id": "chk-001", "date": "2026-09-20", "desc": "Whole Foods", "amount": -86.42},
    {"id": "t23", "account_id": "chk-001", "date": "2026-09-19", "desc": "Netflix", "amount": -15.49},
    {"id": "t24", "account_id": "sav-001", "date": "2026-09-15", "desc": "Interest Payment", "amount": 62.10},
]


def get_cashflow_by_month() -> list[dict]:
    """Aggregate checking+savings transactions into money-in vs money-out per month."""
    buckets: dict[str, dict] = {}
    for tx in TRANSACTIONS:
        month = tx["date"][:7]  # "2026-06"
        b = buckets.setdefault(month, {"month": month, "in": 0.0, "out": 0.0})
        if tx["amount"] >= 0:
            b["in"] += tx["amount"]
        else:
            b["out"] += -tx["amount"]
    return [buckets[k] for k in sorted(buckets.keys())]
