DEMO_USER = {"username": "demo", "password": "demo123"}

LOAN = {
    "loan_id": "mtg-001",
    "property_address": "142 Maple Grove Dr",
    "original_principal": 620000.00,
    "current_principal": 541230.18,
    "interest_rate_apr": 5.85,
    "term_years": 30,
    "years_remaining": 24.5,
    "monthly_payment": 3652.10,
    "next_payment_due": "2026-10-01",
    "extra_payment_impact_note": "Every extra $1,000 to principal today saves roughly $2,140 in interest over the loan's remaining term at the current rate.",
}

# Simplified yearly amortization breakdown (principal vs interest portion of
# payments) for the chart — illustrative figures consistent with the loan
# terms above, not a precise amortization calculation.
AMORTIZATION_SCHEDULE = [
    {"year": 2022, "principal": 9800.00, "interest": 34000.00},
    {"year": 2023, "principal": 10500.00, "interest": 33300.00},
    {"year": 2024, "principal": 11250.00, "interest": 32550.00},
    {"year": 2025, "principal": 12050.00, "interest": 31750.00},
    {"year": 2026, "principal": 12900.00, "interest": 30900.00},
]
