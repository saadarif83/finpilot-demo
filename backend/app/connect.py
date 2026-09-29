"""
Generic "connect an account" flow. The PWA links to GET /connect/{portal},
which redirects the user's browser to that portal's own login/consent
screen. Once the user approves, the portal redirects back here, and THIS
backend exchanges the code for a token server-side and stores it in the
token vault — exactly how a real aggregator (e.g. Plaid) works from the
app's point of view.

POST /connect/demo-all is a demo-day shortcut: it runs the SAME protocol
steps for every portal (authorize -> code -> token exchange, with PKCE and
OIDC where applicable), but submits the demo credentials server-side instead
of waiting for a human to type them into each login screen.
"""
import time
import uuid
import hashlib
import base64
import secrets
from urllib.parse import urlparse, parse_qs
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

# Demo-only saved credentials used by the "Connect all" shortcut.
DEMO_CREDENTIALS = {"username": "demo", "password": "demo123"}
OIDC_SCOPE = "openid profile loan.read"

_pending_states: dict[str, dict] = {}


def _b64url_sha256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def _redirect_uri(portal: str) -> str:
    # Public, browser-facing URL — the user's browser must be able to reach this.
    return f"{settings.BACKEND_URL}/connect/{portal}/callback"


async def _exchange_code(portal: str, code: str, code_verifier: str | None = None):
    """Exchange an authorization code for tokens and store them. Shared by the
    browser callback and the demo auto-connect."""
    data = {"grant_type": "authorization_code", "code": code, "redirect_uri": _redirect_uri(portal)}
    if code_verifier:
        data["code_verifier"] = code_verifier

    # Internal, server-to-server call: use INTERNAL_URL (localhost), never
    # BACKEND_URL — a service calling its own public hostname is unreliable
    # on many hosts (Render included).
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{settings.INTERNAL_URL}/portals/{portal}/token", data=data)
    if resp.status_code != 200:
        raise HTTPException(502, f"{portal} token exchange failed: {resp.text}")

    body = resp.json()
    token_store.set_token(portal, body["access_token"], body.get("id_token"))


async def _connect_creditcard_internal():
    """Client Credentials — no user, no redirect."""
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
        raise HTTPException(502, f"creditcard token request failed: {resp.text}")
    token_store.set_token("creditcard", resp.json()["access_token"])


async def _auto_connect_redirect_portal(portal: str):
    """Run a redirect-based portal's flow end to end without a browser:
    submit the login form with the demo credentials, read the code off the
    302 Location header (instead of letting a browser follow it), verify
    state, then do the normal token exchange."""
    cfg = PORTAL_CONFIG[portal]
    state = str(uuid.uuid4())
    form = {
        **DEMO_CREDENTIALS,
        "client_id": "finpilot",
        "redirect_uri": _redirect_uri(portal),
        "state": state,
    }

    verifier = None
    if cfg["pkce"]:
        verifier = secrets.token_urlsafe(32)
        form["code_challenge"] = _b64url_sha256(verifier)
    if cfg["oidc"]:
        form["scope"] = OIDC_SCOPE

    async with httpx.AsyncClient(follow_redirects=False) as client:
        resp = await client.post(f"{settings.INTERNAL_URL}/portals/{portal}/authorize", data=form)
    if resp.status_code != 302:
        raise HTTPException(502, f"{portal} login failed ({resp.status_code})")

    params = parse_qs(urlparse(resp.headers["location"]).query)
    code = params.get("code", [None])[0]
    returned_state = params.get("state", [None])[0]
    if not code or returned_state != state:
        raise HTTPException(502, f"{portal} returned an invalid code or state")

    await _exchange_code(portal, code, verifier)


@router.get("/status")
def status():
    return {"connected": token_store.connected_portals()}


@router.post("/demo-all")
async def connect_all_demo():
    """Demo shortcut: connect all four portals using the saved demo
    credentials. Each portal still goes through its own real protocol
    steps; only the human typing is skipped. Returns per-portal results so
    one failure doesn't hide the others."""
    results: dict[str, str] = {}
    for portal in ["banking", "mortgage", "creditcard", "brokerage"]:
        try:
            if portal == "creditcard":
                await _connect_creditcard_internal()
            else:
                await _auto_connect_redirect_portal(portal)
            results[portal] = "connected"
        except HTTPException as e:
            results[portal] = f"failed: {e.detail}"
        except Exception as e:
            results[portal] = f"failed: {e}"
    return {"results": results, "connected": token_store.connected_portals()}


@router.get("/{portal}")
def start_connect(portal: str):
    if portal == "creditcard":
        raise HTTPException(400, "creditcard uses POST /connect/creditcard (machine-to-machine, no redirect)")
    if portal not in PORTAL_CONFIG:
        raise HTTPException(404, "unknown portal")

    cfg = PORTAL_CONFIG[portal]
    state = str(uuid.uuid4())
    redirect_uri = _redirect_uri(portal)
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

    await _exchange_code(portal, code, pending.get("code_verifier"))

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
    await _connect_creditcard_internal()
    return {"connected": True}


@router.post("/{portal}/disconnect")
def disconnect(portal: str):
    token_store.disconnect(portal)
    return {"disconnected": portal}
