"""Fake credit card data. CARD is mutable module state — a payment (from the
agentic payoff action) reduces current_balance in place."""

CARD = {
    "card_id": "cc-001",
    "product_name": "Everyday Rewards Visa",
    "last4": "4821",
    "credit_limit": 12000.00,
    "current_balance": 2143.87,
    "apr": 21.99,
    "minimum_payment_due": 65.00,
    "payment_due_date": "2026-10-08",
}

# Categorized transactions across the current month, for the spending
# breakdown chart. Category set kept to <= 6 so the pie/bar chart stays
# within the palette's safe categorical slot count.
TRANSACTIONS = [
    {"id": "c1", "date": "2026-09-21", "desc": "Amazon", "amount": -142.30, "category": "Shopping"},
    {"id": "c2", "date": "2026-09-19", "desc": "Shell Gas", "amount": -54.10, "category": "Transport"},
    {"id": "c3", "date": "2026-09-12", "desc": "Restaurant - Cantina", "amount": -78.20, "category": "Dining"},
    {"id": "c4", "date": "2026-09-10", "desc": "Save-On-Foods", "amount": -96.40, "category": "Groceries"},
    {"id": "c5", "date": "2026-09-08", "desc": "Spotify", "amount": -12.99, "category": "Entertainment"},
    {"id": "c6", "date": "2026-09-06", "desc": "Uber Eats", "amount": -41.75, "category": "Dining"},
    {"id": "c7", "date": "2026-09-04", "desc": "BC Hydro", "amount": -88.50, "category": "Utilities"},
    {"id": "c8", "date": "2026-09-02", "desc": "Best Buy", "amount": -210.00, "category": "Shopping"},
]


def get_spending_breakdown() -> dict:
    totals: dict[str, float] = {}
    for tx in TRANSACTIONS:
        totals[tx["category"]] = totals.get(tx["category"], 0.0) + (-tx["amount"])
    categories = [{"name": k, "amount": round(v, 2)} for k, v in totals.items()]
    categories.sort(key=lambda c: -c["amount"])
    return {"month": "2026-09", "categories": categories}


def apply_payment(amount: float) -> dict:
    """Reduce the card balance by `amount` (never below 0). Returns the new state."""
    CARD["current_balance"] = round(max(0.0, CARD["current_balance"] - amount), 2)
    return dict(CARD)


REGISTERED_CLIENTS = {
    "finpilot-backend": "finpilot-cc-secret-demo",
}
