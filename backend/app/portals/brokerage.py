"""
SIMULATED BROKERAGE PORTAL
Auth mechanism: OAuth 2.0 Authorization Code Grant + PKCE (Proof Key for Code
Exchange). This is the required pattern for "public clients" — apps like
FinPilot that run on a user's device and can't safely hold a client_secret.
Instead of a secret, the client proves it's the same app that started the
flow by generating a random `code_verifier`, sending its hash (`code_challenge`)
up front, and revealing the original verifier only at token exchange time.
Also shows an explicit per-scope consent screen (checkboxes), matching how
real brokerages/Open Banking UIs let users pick exactly what to share.
"""
import time
import uuid
import hashlib
import base64
from fastapi import APIRouter, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.core.security import create_access_token, require_bearer_token
from app.portals.brokerage_data import POSITIONS, CASH_BALANCE
from app.portals.banking_data import DEMO_USER  # reuse same demo creds

router = APIRouter(prefix="/portals/brokerage", tags=["brokerage"])

_AUTH_CODES: dict[str, dict] = {}


def _b64url_sha256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


@router.get("/authorize", response_class=HTMLResponse)
def authorize_screen(client_id: str, redirect_uri: str, code_challenge: str, code_challenge_method: str = "S256", state: str = ""):
    if code_challenge_method != "S256":
        raise HTTPException(400, "unsupported code_challenge_method")
    return f"""
    <html><head><title>StreetTrade — Sign in</title>
    <style>
      body {{ font-family: -apple-system, sans-serif; background:#2a1a3a; color:#fff;
              display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }}
      .card {{ background:#3a2452; padding:32px; border-radius:16px; width:340px; }}
      h2 {{ margin-top:0; }}
      input[type=text], input[type=password] {{ width:100%; padding:10px; margin:8px 0; border-radius:8px; border:none; box-sizing:border-box; }}
      button {{ width:100%; padding:12px; margin-top:12px; border-radius:8px; border:none;
                background:#a855f7; color:white; font-weight:600; font-size:15px; }}
      .app-name {{ color:#d8b4fe; font-size:13px; }}
      .badge {{ display:inline-block; background:#a855f7; color:#fff; font-size:11px; padding:2px 8px; border-radius:10px; margin-bottom:8px;}}
      .scopes {{ background:#2a1a3a; padding:10px; border-radius:8px; font-size:13px; margin:12px 0; }}
      .scopes label {{ display:block; margin:6px 0; }}
    </style></head>
    <body>
      <div class="card">
        <div class="badge">OAuth2 + PKCE</div>
        <div class="app-name">📈 StreetTrade (demo)</div>
        <h2>Sign in to connect</h2>
        <div class="scopes">
          <b>{client_id}</b> is requesting:
          <label><input type="checkbox" checked disabled /> View positions</label>
          <label><input type="checkbox" checked disabled /> View cash balance</label>
          <label><input type="checkbox" disabled /> Place trades (not requested)</label>
        </div>
        <form method="post" action="/portals/brokerage/authorize">
          <input type="hidden" name="redirect_uri" value="{redirect_uri}" />
          <input type="hidden" name="state" value="{state}" />
          <input type="hidden" name="client_id" value="{client_id}" />
          <input type="hidden" name="code_challenge" value="{code_challenge}" />
          <input type="text" name="username" placeholder="Username (try: demo)" />
          <input type="password" name="password" placeholder="Password (try: demo123)" />
          <button type="submit">Sign in &amp; Authorize</button>
        </form>
      </div>
    </body></html>
    """


@router.post("/authorize")
def authorize_submit(
    username: str = Form(...),
    password: str = Form(...),
    redirect_uri: str = Form(...),
    state: str = Form(""),
    client_id: str = Form(...),
    code_challenge: str = Form(...),
):
    if username != DEMO_USER["username"] or password != DEMO_USER["password"]:
        return HTMLResponse("<h3>Invalid credentials. Go back and try demo / demo123.</h3>", status_code=401)

    code = str(uuid.uuid4())
    _AUTH_CODES[code] = {
        "redirect_uri": redirect_uri,
        "expires": time.time() + 300,
        "user": username,
        "code_challenge": code_challenge,
    }
    sep = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(f"{redirect_uri}{sep}code={code}&state={state}", status_code=302)


@router.post("/token")
def exchange_token(
    grant_type: str = Form(...),
    code: str = Form(...),
    redirect_uri: str = Form(...),
    code_verifier: str = Form(...),
):
    if grant_type != "authorization_code":
        raise HTTPException(400, "unsupported_grant_type")
    entry = _AUTH_CODES.get(code)
    if not entry or entry["expires"] < time.time():
        raise HTTPException(400, "invalid_grant")
    if entry["redirect_uri"] != redirect_uri:
        raise HTTPException(400, "redirect_uri_mismatch")

    # THE PKCE CHECK: no client_secret involved. We hash the verifier the
    # client reveals now and confirm it matches the challenge sent up front.
    if _b64url_sha256(code_verifier) != entry["code_challenge"]:
        raise HTTPException(400, "invalid_grant: PKCE verification failed")

    del _AUTH_CODES[code]
    token = create_access_token(subject=entry["user"], portal="brokerage", scope="positions.read cash.read")
    return {"access_token": token, "token_type": "bearer", "expires_in": 3600}


@router.get("/api/positions")
def get_positions(claims: dict = Depends(require_bearer_token("brokerage"))):
    return {"positions": POSITIONS}


@router.get("/api/cash")
def get_cash(claims: dict = Depends(require_bearer_token("brokerage"))):
    return {"cash": CASH_BALANCE}
