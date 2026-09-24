"""
Aggregates all connected portals into one summary payload for the home
screen — the "single pane of glass" view. Only connected portals are
included; the frontend shows a "connect this account" prompt for the rest.
"""
import httpx
from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.core import token_store
from app.portals.brokerage_data import total_positions_value

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


async def _get(portal: str, path: str) -> dict | None:
    token = token_store.get_token(portal)
    if not token:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.INTERNAL_URL}{path}", headers={"Authorization": f"Bearer {token}"})
    if resp.status_code != 200:
        return None
    return resp.json()


@router.get("/summary")
async def summary():
    result = {"connected": token_store.connected_portals(), "accounts": {}}

    banking = await _get("banking", "/portals/banking/api/accounts")
    if banking:
        checking = next((a for a in banking["accounts"] if a["type"] == "checking"), None)
        savings = next((a for a in banking["accounts"] if a["type"] == "savings"), None)
        result["accounts"]["banking"] = {
            "checking_balance": checking["balance"] if checking else 0,
            "savings_balance": savings["balance"] if savings else 0,
            "total": round((checking["balance"] if checking else 0) + (savings["balance"] if savings else 0), 2),
        }

    mortgage = await _get("mortgage", "/portals/mortgage/api/loan")
    if mortgage:
        loan = mortgage["loan"]
        result["accounts"]["mortgage"] = {
            "current_principal": loan["current_principal"],
            "interest_rate_apr": loan["interest_rate_apr"],
            "monthly_payment": loan["monthly_payment"],
        }

    creditcard = await _get("creditcard", "/portals/creditcard/api/account")
    if creditcard:
        card = creditcard["card"]
        result["accounts"]["creditcard"] = {
            "current_balance": card["current_balance"],
            "credit_limit": card["credit_limit"],
            "apr": card["apr"],
            "utilization_pct": round(100 * card["current_balance"] / card["credit_limit"], 1),
        }

    brokerage_positions = await _get("brokerage", "/portals/brokerage/api/positions")
    brokerage_cash = await _get("brokerage", "/portals/brokerage/api/cash")
    if brokerage_positions and brokerage_cash:
        result["accounts"]["brokerage"] = {
            "positions_value": total_positions_value(),
            "cash": brokerage_cash["cash"]["settled_cash"],
            "total": round(total_positions_value() + brokerage_cash["cash"]["settled_cash"], 2),
        }

    return result


# ---- Drill-down detail proxies ----
# The frontend never holds a portal's bearer token itself — tokens live only
# in this backend's token_store. These endpoints let the browser fetch the
# chart data it needs (cashflow, spending breakdown, etc.) without the
# frontend ever touching auth at all, exactly like a real mobile app talking
# to its own backend-for-frontend rather than each bank's API directly.

@router.get("/detail/banking/cashflow")
async def detail_banking_cashflow():
    data = await _get("banking", "/portals/banking/api/cashflow")
    if data is None:
        raise HTTPException(400, "banking is not connected")
    return data


@router.get("/detail/creditcard/spending-breakdown")
async def detail_creditcard_spending():
    data = await _get("creditcard", "/portals/creditcard/api/spending-breakdown")
    if data is None:
        raise HTTPException(400, "creditcard is not connected")
    return data


@router.get("/detail/brokerage/performance")
async def detail_brokerage_performance():
    data = await _get("brokerage", "/portals/brokerage/api/performance")
    if data is None:
        raise HTTPException(400, "brokerage is not connected")
    return data


@router.get("/detail/mortgage/amortization")
async def detail_mortgage_amortization():
    data = await _get("mortgage", "/portals/mortgage/api/amortization")
    if data is None:
        raise HTTPException(400, "mortgage is not connected")
    return data
