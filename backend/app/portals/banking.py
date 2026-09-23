"""
SIMULATED BANKING PORTAL
Auth mechanism: OAuth 2.0 Authorization Code Grant (the flow real banks like
Chase/Plaid use). The user is redirected to a login+consent screen hosted by
THIS "bank", approves access, and is redirected back to FinPilot with a
short-lived code that FinPilot exchanges server-side for an access token.
"""
import time
import uuid
from fastapi import APIRouter, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.core.security import create_access_token, require_bearer_token
from app.portals.banking_data import DEMO_USER, ACCOUNTS, TRANSACTIONS

router = APIRouter(prefix="/portals/banking", tags=["banking"])

# In-memory store of issued auth codes: code -> {redirect_uri, state, expires}
_AUTH_CODES: dict[str, dict] = {}


@router.get("/authorize", response_class=HTMLResponse)
def authorize_screen(client_id: str, redirect_uri: str, state: str = ""):
    """Step 1: the bank's own login + consent page. This is what a user would
    see if FinPilot redirected them to their bank to grant access."""
    return f"""
    <html><head><title>SecureBank — Sign in</title>
    <style>
      body {{ font-family: -apple-system, sans-serif; background:#0b1e3a; color:#fff;
              display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }}
      .card {{ background:#122a52; padding:32px; border-radius:16px; width:320px; }}
      h2 {{ margin-top:0; }}
      input {{ width:100%; padding:10px; margin:8px 0; border-radius:8px; border:none; box-sizing:border-box; }}
      button {{ width:100%; padding:12px; margin-top:12px; border-radius:8px; border:none;
                background:#2f7ef7; color:white; font-weight:600; font-size:15px; }}
      .app-name {{ color:#8fb4ff; font-size:13px; }}
      .scope {{ background:#0b1e3a; padding:10px; border-radius:8px; font-size:13px; margin:12px 0; }}
    </style></head>
    <body>
      <div class="card">
        <div class="app-name">🏦 SecureBank (demo)</div>
        <h2>Sign in to connect</h2>
        <div class="scope"><b>{client_id}</b> is requesting read access to your account balances and transactions.</div>
        <form method="post" action="/portals/banking/authorize">
          <input type="hidden" name="redirect_uri" value="{redirect_uri}" />
          <input type="hidden" name="state" value="{state}" />
          <input type="hidden" name="client_id" value="{client_id}" />
          <input name="username" placeholder="Username (try: demo)" />
          <input name="password" type="password" placeholder="Password (try: demo123)" />
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
):
    """Step 2: verify credentials, issue a short-lived authorization code,
    redirect back to FinPilot with it — exactly like a real OAuth provider."""
    if username != DEMO_USER["username"] or password != DEMO_USER["password"]:
        return HTMLResponse("<h3>Invalid credentials. Go back and try demo / demo123.</h3>", status_code=401)

    code = str(uuid.uuid4())
    _AUTH_CODES[code] = {"redirect_uri": redirect_uri, "expires": time.time() + 300, "user": username}
    sep = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(f"{redirect_uri}{sep}code={code}&state={state}", status_code=302)


@router.post("/token")
def exchange_token(grant_type: str = Form(...), code: str = Form(...), redirect_uri: str = Form(...)):
    """Step 3: FinPilot's backend exchanges the code for an access token.
    This call happens server-to-server and is never seen by the user."""
    if grant_type != "authorization_code":
        raise HTTPException(400, "unsupported_grant_type")
    entry = _AUTH_CODES.get(code)
    if not entry or entry["expires"] < time.time():
        raise HTTPException(400, "invalid_grant")
    if entry["redirect_uri"] != redirect_uri:
        raise HTTPException(400, "redirect_uri_mismatch")
    del _AUTH_CODES[code]  # codes are single-use

    token = create_access_token(subject=entry["user"], portal="banking")
    return {"access_token": token, "token_type": "bearer", "expires_in": 3600}


# ---- Protected resource endpoints (what FinPilot actually calls once connected) ----

@router.get("/api/accounts")
def get_accounts(claims: dict = Depends(require_bearer_token("banking"))):
    return {"accounts": ACCOUNTS}


@router.get("/api/transactions")
def get_transactions(claims: dict = Depends(require_bearer_token("banking"))):
    return {"transactions": TRANSACTIONS}
