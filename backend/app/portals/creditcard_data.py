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

TRANSACTIONS = [
    {"id": "c1", "date": "2026-09-21", "desc": "Amazon", "amount": -142.30},
    {"id": "c2", "date": "2026-09-19", "desc": "Shell Gas", "amount": -54.10},
    {"id": "c3", "date": "2026-09-12", "desc": "Restaurant - Cantina", "amount": -78.20},
]

# In a real Client Credentials setup, FinPilot would have its own
# client_id/client_secret pair registered with the card issuer (like an API key).
REGISTERED_CLIENTS = {
    "finpilot-backend": "finpilot-cc-secret-demo",
}
