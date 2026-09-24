"""Fake brokerage data. CASH_BALANCE is mutable module state — a withdrawal
(from the agentic payoff action) reduces settled_cash/buying_power in place."""

DEMO_USER = {"username": "demo", "password": "demo123"}

POSITIONS = [
    {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "shares": 42.5, "avg_cost": 210.30, "current_price": 268.90},
    {"symbol": "AAPL", "name": "Apple Inc.", "shares": 15, "avg_cost": 165.00, "current_price": 231.40},
    {"symbol": "NVDA", "name": "NVIDIA Corp.", "shares": 8, "avg_cost": 410.00, "current_price": 178.20},
]

CASH_BALANCE = {"settled_cash": 6420.55, "buying_power": 6420.55}

# Total portfolio value (positions + cash) at each month-end, for the
# performance chart. Values are illustrative, not derived from the position
# math above — this is a demo prop, not a backtester.
PERFORMANCE_HISTORY = [
    {"month": "2026-04", "value": 21800.00},
    {"month": "2026-05", "value": 22350.00},
    {"month": "2026-06", "value": 21990.00},
    {"month": "2026-07", "value": 23100.00},
    {"month": "2026-08", "value": 23840.00},
    {"month": "2026-09", "value": 24512.75},
]


def total_positions_value() -> float:
    return round(sum(p["shares"] * p["current_price"] for p in POSITIONS), 2)


def withdraw_cash(amount: float) -> dict:
    """Reduce settled cash by `amount`. Raises ValueError if insufficient funds."""
    if amount > CASH_BALANCE["settled_cash"]:
        raise ValueError("Insufficient settled cash")
    CASH_BALANCE["settled_cash"] = round(CASH_BALANCE["settled_cash"] - amount, 2)
    CASH_BALANCE["buying_power"] = round(CASH_BALANCE["buying_power"] - amount, 2)
    return dict(CASH_BALANCE)


def deposit_cash(amount: float) -> dict:
    """Increase settled cash by `amount` — used both for real deposits and to
    compensate/refund a withdrawal if a paired action fails partway through."""
    CASH_BALANCE["settled_cash"] = round(CASH_BALANCE["settled_cash"] + amount, 2)
    CASH_BALANCE["buying_power"] = round(CASH_BALANCE["buying_power"] + amount, 2)
    return dict(CASH_BALANCE)
