"""
DETERMINISTIC ACTION EXECUTOR — the security boundary for anything that moves
money in this demo.

The orchestrator's LLM can PROPOSE an action (via a read-only MCP tool that
just computes numbers and returns a plan) but it can never call this endpoint
itself — there is no MCP tool wired to it. The only path to executing a
proposal is a human clicking "Confirm & Execute" in the UI, which calls this
endpoint directly with an explicit amount the user has seen.

This is worth calling out in the talk: it's the same shape as a real
brokerage's "review order -> confirm -> execute" flow, and for the same
reason — a model (or a person) should never be one ambiguous sentence away
from moving money.
"""
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.config import settings
from app.core import token_store

router = APIRouter(prefix="/actions", tags=["actions"])


class ExecuteRequest(BaseModel):
    type: str
    amount: float


async def _post(portal: str, path: str, json_body: dict) -> dict:
    token = token_store.get_token(portal)
    if not token:
        raise HTTPException(400, f"{portal} is not connected")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.INTERNAL_URL}{path}",
            json=json_body,
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code != 200:
        raise HTTPException(502, f"{portal} call failed: {resp.text}")
    return resp.json()


@router.post("/execute")
async def execute(req: ExecuteRequest):
    if req.type != "payoff_creditcard_from_brokerage":
        raise HTTPException(400, f"unknown action type: {req.type}")
    if req.amount <= 0:
        raise HTTPException(400, "amount must be positive")

    # Step 1: withdraw from brokerage. If this fails (e.g. insufficient
    # funds), nothing else happens.
    cash_result = await _post("brokerage", "/portals/brokerage/api/withdraw", {"amount": req.amount})

    # Step 2: apply the payment to the credit card. If this fails, refund the
    # brokerage withdrawal so the two portals never end up inconsistent —
    # simple compensation since both are in-memory for this demo.
    try:
        card_result = await _post("creditcard", "/portals/creditcard/api/payment", {"amount": req.amount})
    except HTTPException:
        await _post("brokerage", "/portals/brokerage/api/deposit", {"amount": req.amount})
        raise

    return {
        "executed": True,
        "type": req.type,
        "amount": req.amount,
        "brokerage_cash": cash_result["cash"],
        "creditcard": card_result["card"],
    }
