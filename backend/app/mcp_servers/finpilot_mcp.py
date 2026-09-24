"""
The MCP tool server. This is what the orchestrator connects to as an MCP
client — it doesn't know or care that under the hood these tools call four
different simulated portals with four different auth mechanisms. That
uniformity is the whole point of MCP.

IMPORTANT SECURITY NOTE: every tool here is READ-ONLY. Nothing that moves
money is exposed as a tool the LLM can call directly — see app/actions.py
for why. `propose_creditcard_payoff_from_brokerage` computes a plan and
returns numbers; it never touches a portal's write endpoint.
"""
import httpx
from mcp.server.mcpserver import MCPServer
from app.core.config import settings
from app.core import token_store

mcp_server = MCPServer(
    name="finpilot-portals",
    instructions="Read-only tools for a user's connected financial accounts: banking, mortgage, credit card, brokerage, and real-time market news.",
)


async def _get(portal: str, path: str) -> dict:
    token = token_store.get_token(portal)
    if not token:
        return {"error": f"The user has not connected their {portal} account yet. Ask them to connect it in FinPilot first."}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.INTERNAL_URL}{path}", headers={"Authorization": f"Bearer {token}"})
    if resp.status_code != 200:
        return {"error": f"{portal} API returned {resp.status_code}: {resp.text}"}
    return resp.json()


@mcp_server.tool()
async def get_banking_accounts() -> dict:
    """Get the user's checking and savings account balances."""
    return await _get("banking", "/portals/banking/api/accounts")


@mcp_server.tool()
async def get_banking_transactions() -> dict:
    """Get the user's recent checking/savings transactions."""
    return await _get("banking", "/portals/banking/api/transactions")


@mcp_server.tool()
async def get_banking_cashflow() -> dict:
    """Get the user's money-in vs money-out totals per month, for trend analysis."""
    return await _get("banking", "/portals/banking/api/cashflow")


@mcp_server.tool()
async def get_mortgage_details() -> dict:
    """Get the user's mortgage: current principal, interest rate (APR), monthly
    payment, years remaining, and the estimated interest savings from an extra
    principal payment."""
    return await _get("mortgage", "/portals/mortgage/api/loan")


@mcp_server.tool()
async def get_mortgage_amortization() -> dict:
    """Get the user's mortgage principal vs interest paid per year."""
    return await _get("mortgage", "/portals/mortgage/api/amortization")


@mcp_server.tool()
async def get_creditcard_account() -> dict:
    """Get the user's credit card balance, credit limit, APR, and minimum payment due."""
    return await _get("creditcard", "/portals/creditcard/api/account")


@mcp_server.tool()
async def get_creditcard_transactions() -> dict:
    """Get the user's recent credit card transactions."""
    return await _get("creditcard", "/portals/creditcard/api/transactions")


@mcp_server.tool()
async def get_creditcard_spending_breakdown() -> dict:
    """Get the user's credit card spending broken down by category for the current month."""
    return await _get("creditcard", "/portals/creditcard/api/spending-breakdown")


@mcp_server.tool()
async def get_brokerage_positions() -> dict:
    """Get the user's brokerage stock/ETF positions, share counts, and current prices."""
    return await _get("brokerage", "/portals/brokerage/api/positions")


@mcp_server.tool()
async def get_brokerage_cash() -> dict:
    """Get the user's uninvested cash balance and buying power in their brokerage account."""
    return await _get("brokerage", "/portals/brokerage/api/cash")


@mcp_server.tool()
async def get_brokerage_performance() -> dict:
    """Get the user's total brokerage portfolio value over the past several months."""
    return await _get("brokerage", "/portals/brokerage/api/performance")


@mcp_server.tool()
async def get_market_news(topic: str = "stock market") -> dict:
    """Get recent real-time market news headlines relevant to a topic (e.g. a
    stock ticker, 'interest rates', 'stock market')."""
    if not settings.FINNHUB_API_KEY:
        return {
            "note": "Using sample data (no FINNHUB_API_KEY configured).",
            "headlines": [
                "Fed signals rates may hold steady through Q4",
                "Tech stocks rally on strong earnings season",
                "10-year Treasury yield dips to three-month low",
            ],
        }
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://finnhub.io/api/v1/news",
            params={"category": "general", "token": settings.FINNHUB_API_KEY},
        )
    if resp.status_code != 200:
        return {"error": f"Finnhub returned {resp.status_code}"}
    items = resp.json()[:5]
    return {"headlines": [item.get("headline") for item in items]}


@mcp_server.tool()
async def propose_creditcard_payoff_from_brokerage() -> dict:
    """Compute a proposal for paying down the user's credit card balance using
    idle brokerage cash, when the card's APR is meaningfully higher than what
    that cash is likely earning sitting uninvested. Returns a structured plan
    with the recommended amount, before/after balances, and estimated annual
    interest savings. This tool ONLY computes and returns numbers — it never
    moves any money. If the user wants to proceed, FinPilot's UI shows a
    confirmation button that executes the plan through a separate, secured
    endpoint — never automatically."""
    card = await _get("creditcard", "/portals/creditcard/api/account")
    cash = await _get("brokerage", "/portals/brokerage/api/cash")

    if "error" in card:
        return card
    if "error" in cash:
        return cash

    card_balance = card["card"]["current_balance"]
    card_apr = card["card"]["apr"]
    settled_cash = cash["cash"]["settled_cash"]

    # Keep a cash buffer rather than sweeping the account to zero — a real
    # advisor would never recommend draining brokerage cash entirely.
    buffer_amount = min(1000.0, settled_cash * 0.15)
    available = max(0.0, settled_cash - buffer_amount)
    recommended_amount = round(min(card_balance, available), 2)

    if recommended_amount <= 0:
        return {
            "recommended": False,
            "reason": "Not enough idle brokerage cash above a safe buffer to make a meaningful payment, or the card is already paid off.",
            "card_balance": card_balance,
            "card_apr": card_apr,
            "brokerage_cash": settled_cash,
        }

    # Rough annualized interest saved by removing this balance from a card
    # charging card_apr, versus letting it sit as ~0-yield idle cash.
    estimated_annual_savings = round(recommended_amount * (card_apr / 100), 2)

    return {
        "recommended": True,
        "type": "payoff_creditcard_from_brokerage",
        "amount": recommended_amount,
        "rationale": (
            f"Your card charges {card_apr}% APR while this brokerage cash is sitting uninvested. "
            f"Paying down ${recommended_amount:,.2f} now saves an estimated ${estimated_annual_savings:,.2f}/year "
            f"in interest, and keeps a ${buffer_amount:,.2f} cash buffer in the brokerage account."
        ),
        "estimated_annual_savings": estimated_annual_savings,
        "before": {"creditcard_balance": card_balance, "brokerage_cash": settled_cash},
        "after": {
            "creditcard_balance": round(card_balance - recommended_amount, 2),
            "brokerage_cash": round(settled_cash - recommended_amount, 2),
        },
    }


mcp_app = mcp_server.streamable_http_app(streamable_http_path="/")
