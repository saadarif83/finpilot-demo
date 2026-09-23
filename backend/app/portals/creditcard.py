"""
SIMULATED CREDIT CARD PORTAL
Auth mechanism: OAuth 2.0 Client Credentials Grant — no user redirect at all.
FinPilot authenticates as ITSELF using a client_id/client_secret pair issued
once when it registered as a developer with the card issuer (this is how
most server-to-server fintech data APIs and market-data providers work).
Because it's machine-to-machine, there's no login screen here — just a
direct token request.
"""
from fastapi import APIRouter, Form, Depends, HTTPException
from app.core.security import create_access_token, require_bearer_token
from app.portals.creditcard_data import CARD, TRANSACTIONS, REGISTERED_CLIENTS

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

    # subject is the CLIENT (the app), not a human user — that's the point of this grant
    token = create_access_token(subject=client_id, portal="creditcard", scope="account.read")
    return {"access_token": token, "token_type": "bearer", "expires_in": 3600}


@router.get("/api/account")
def get_account(claims: dict = Depends(require_bearer_token("creditcard"))):
    return {"card": CARD}


@router.get("/api/transactions")
def get_transactions(claims: dict = Depends(require_bearer_token("creditcard"))):
    return {"transactions": TRANSACTIONS}
