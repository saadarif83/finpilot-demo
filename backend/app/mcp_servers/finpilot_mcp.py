"""
The MCP tool server. This is what the orchestrator (Day 4) connects to as an
MCP client — it doesn't know or care that under the hood these tools call
four different simulated portals with four different auth mechanisms. That
uniformity is the whole point of MCP: the LLM sees one consistent tool
interface no matter how varied the underlying auth/data sources are.

Each tool checks the token vault for that portal. If the user hasn't
connected it yet, the tool tells the LLM so — the LLM can then explain to
the user which account still needs to be connected, rather than crashing.
"""
import httpx
from mcp.server.mcpserver import MCPServer
from app.core.config import settings
from app.core import token_store

mcp_server = MCPServer(
    name="finpilot-portals",
    instructions="Tools for reading a user's connected financial accounts: banking, mortgage, credit card, brokerage, and real-time market news.",
)


async def _get(portal: str, path: str) -> dict:
    token = token_store.get_token(portal)
    if not token:
        return {"error": f"The user has not connected their {portal} account yet. Ask them to connect it in FinPilot first."}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.BACKEND_URL}{path}", headers={"Authorization": f"Bearer {token}"})
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
async def get_mortgage_details() -> dict:
    """Get the user's mortgage: current principal, interest rate (APR), monthly
    payment, years remaining, and the estimated interest savings from an extra
    principal payment."""
    return await _get("mortgage", "/portals/mortgage/api/loan")


@mcp_server.tool()
async def get_creditcard_account() -> dict:
    """Get the user's credit card balance, credit limit, APR, and minimum payment due."""
    return await _get("creditcard", "/portals/creditcard/api/account")


@mcp_server.tool()
async def get_creditcard_transactions() -> dict:
    """Get the user's recent credit card transactions."""
    return await _get("creditcard", "/portals/creditcard/api/transactions")


@mcp_server.tool()
async def get_brokerage_positions() -> dict:
    """Get the user's brokerage stock/ETF positions, share counts, and current prices."""
    return await _get("brokerage", "/portals/brokerage/api/positions")


@mcp_server.tool()
async def get_brokerage_cash() -> dict:
    """Get the user's uninvested cash balance and buying power in their brokerage account."""
    return await _get("brokerage", "/portals/brokerage/api/cash")


@mcp_server.tool()
async def get_market_news(topic: str = "stock market") -> dict:
    """Get recent real-time market news headlines relevant to a topic (e.g. a
    stock ticker, 'interest rates', 'stock market')."""
    if not settings.FINNHUB_API_KEY:
        # Graceful fallback so the demo never dies on stage over a missing API key.
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


mcp_app = mcp_server.streamable_http_app(streamable_http_path="/")
