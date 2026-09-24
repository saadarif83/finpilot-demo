"""
Generic "connect an account" flow. The PWA links to GET /connect/{portal},
which redirects the user's browser to that portal's own login/consent
screen. Once the user approves, the portal redirects back here, and THIS
backend exchanges the code for a token server-side and stores it in the
token vault — exactly how a real aggregator (e.g. Plaid) works from the
app's point of view.
"""
import time
import uuid
import hashlib
import base64
import secrets
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from app.core.config import settings
from app.core import token_store

router = APIRouter(prefix="/connect", tags=["connect"])

PORTAL_CONFIG = {
    "banking": {"pkce": False, "oidc": False},
    "mortgage": {"pkce": False, "oidc": True},
    "brokerage": {"pkce": True, "oidc": False},
}

_pending_states: dict[str, dict] = {}


def _b64url_sha256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


@router.get("/status")
def status():
    return {"connected": token_store.connected_portals()}


@router.get("/{portal}")
def start_connect(portal: str):
    if portal == "creditcard":
        raise HTTPException(400, "creditcard uses POST /connect/creditcard (machine-to-machine, no redirect)")
    if portal not in PORTAL_CONFIG:
        raise HTTPException(404, "unknown portal")

    cfg = PORTAL_CONFIG[portal]
    state = str(uuid.uuid4())
    # Public, browser-facing URL — the user's browser must be able to reach this.
    redirect_uri = f"{settings.BACKEND_URL}/connect/{portal}/callback"
    pending = {"portal": portal, "expires": time.time() + 600}

    url = f"{settings.BACKEND_URL}/portals/{portal}/authorize?client_id=finpilot&redirect_uri={redirect_uri}&state={state}"

    if cfg["pkce"]:
        verifier = secrets.token_urlsafe(32)
        challenge = _b64url_sha256(verifier)
        pending["code_verifier"] = verifier
        url += f"&code_challenge={challenge}"

    _pending_states[state] = pending
    return RedirectResponse(url)


@router.get("/{portal}/callback")
async def connect_callback(portal: str, code: str, state: str):
    pending = _pending_states.pop(state, None)
    if not pending or pending["portal"] != portal or pending["expires"] < time.time():
        raise HTTPException(400, "invalid or expired state")

    redirect_uri = f"{settings.BACKEND_URL}/connect/{portal}/callback"
    data = {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri}
    if "code_verifier" in pending:
        data["code_verifier"] = pending["code_verifier"]

    # Internal, server-to-server call: use INTERNAL_URL (localhost), never
    # BACKEND_URL — a service calling its own public hostname is unreliable
    # on many hosts (Render included).
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{settings.INTERNAL_URL}/portals/{portal}/token", data=data)
    if resp.status_code != 200:
        raise HTTPException(502, f"token exchange failed: {resp.text}")

    body = resp.json()
    token_store.set_token(portal, body["access_token"], body.get("id_token"))

    return HTMLResponse(f"""
    <html><body style="font-family:-apple-system,sans-serif;text-align:center;padding-top:80px;">
    <h2>✅ {portal.capitalize()} connected</h2>
    <p>You can close this window and return to FinPilot.</p>
    <script>setTimeout(() => window.close(), 1500);</script>
    </body></html>
    """)


@router.post("/creditcard")
async def connect_creditcard():
    """Credit card uses Client Credentials — no user redirect needed."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.INTERNAL_URL}/portals/creditcard/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "finpilot-backend",
                "client_secret": "finpilot-cc-secret-demo",
            },
        )
    if resp.status_code != 200:
        raise HTTPException(502, f"token request failed: {resp.text}")
    body = resp.json()
    token_store.set_token("creditcard", body["access_token"])
    return {"connected": True}


@router.post("/{portal}/disconnect")
def disconnect(portal: str):
    token_store.disconnect(portal)
    return {"disconnected": portal}
