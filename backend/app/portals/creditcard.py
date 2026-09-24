"""
SIMULATED CREDIT CARD PORTAL
Auth mechanism: OAuth 2.0 Client Credentials Grant — no user redirect at all.
FinPilot authenticates as ITSELF using a client_id/client_secret pair issued
once when it registered as a developer with the card issuer (this is how
most server-to-server fintech data APIs and market-data providers work).
"""
from fastapi import APIRouter, Form, Depends, HTTPException
from pydantic import BaseModel
from app.core.security import create_access_token, require_bearer_token
from app.portals.creditcard_data import CARD, TRANSACTIONS, REGISTERED_CLIENTS, get_spending_breakdown, apply_payment

router = APIRouter(prefix="/portals/creditcard", tags=["creditcard"])


@router.post("/token")
def client_credentials_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
):
    if grant_type != "client_credentials":
        raise HTTPException(400, "unsupported_grant_type")
    expected_secret = REGISTERED_CLIENTS.get(client_id)
    if not expected_secret or expected_secret != client_secret:
        raise HTTPException(401, "invalid_client")

    token = create_access_token(subject=client_id, portal="creditcard", scope="account.read account.write")
    return {"access_token": token, "token_type": "bearer", "expires_in": 3600}


@router.get("/api/account")
def get_account(claims: dict = Depends(require_bearer_token("creditcard"))):
    return {"card": CARD}


@router.get("/api/transactions")
def get_transactions(claims: dict = Depends(require_bearer_token("creditcard"))):
    return {"transactions": TRANSACTIONS}


@router.get("/api/spending-breakdown")
def spending_breakdown(claims: dict = Depends(require_bearer_token("creditcard"))):
    """Category totals for the current month, for the dashboard drill-down chart."""
    return get_spending_breakdown()


class PaymentRequest(BaseModel):
    amount: float


@router.post("/api/payment")
def make_payment(body: PaymentRequest, claims: dict = Depends(require_bearer_token("creditcard"))):
    """Apply a payment to the card balance. This is a WRITE endpoint — it is
    intentionally NOT exposed as an MCP tool to the LLM. Only the deterministic
    /actions/execute endpoint (triggered by an explicit user confirmation in
    the UI) calls this."""
    if body.amount <= 0:
        raise HTTPException(400, "amount must be positive")
    updated = apply_payment(body.amount)
    return {"card": updated}
