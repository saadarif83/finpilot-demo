"""Fake banking data for the demo. One hardcoded demo user is enough —
this is a prop for a talk, not a real bank."""

DEMO_USER = {"username": "demo", "password": "demo123"}

ACCOUNTS = [
    {"id": "chk-001", "type": "checking", "name": "Everyday Checking", "balance": 4231.55},
    {"id": "sav-001", "type": "savings", "name": "High-Yield Savings", "balance": 18250.00, "apy": 4.25},
]

TRANSACTIONS = [
    {"id": "t1", "account_id": "chk-001", "date": "2026-09-20", "desc": "Whole Foods", "amount": -86.42},
    {"id": "t2", "account_id": "chk-001", "date": "2026-09-19", "desc": "Payroll Deposit", "amount": 3200.00},
    {"id": "t3", "account_id": "chk-001", "date": "2026-09-18", "desc": "Netflix", "amount": -15.49},
    {"id": "t4", "account_id": "sav-001", "date": "2026-09-15", "desc": "Interest Payment", "amount": 62.10},
]
