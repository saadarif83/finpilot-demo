"""
SIMULATED MORTGAGE PORTAL
Auth mechanism: OpenID Connect (OIDC) — OAuth 2.0 plus a standardized
identity layer. Real-world example: banks/lenders that use Okta/Auth0/Azure AD
B2C under the hood expose a discovery document and issue an ID token
(a JWT with identity claims) alongside the access token.
"""
import time
import uuid
from fastapi import APIRouter, Form, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jose import jwt
from app.core.config import settings
from app.core.security import create_access_token, require_bearer_token
from app.portals.mortgage_data import DEMO_USER, LOAN, AMORTIZATION_SCHEDULE

router = APIRouter(prefix="/portals/mortgage", tags=["mortgage"])

_AUTH_CODES: dict[str, dict] = {}


@router.get("/.well-known/openid-configuration")
def oidc_discovery(request: Request):
    base = str(request.base_url).rstrip("/") + "/portals/mortgage"
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "userinfo_endpoint": f"{base}/userinfo",
        "response_types_supported": ["code"],
        "id_token_signing_alg_values_supported": ["HS256"],
        "scopes_supported": ["openid", "profile", "loan.read"],
    }


@router.get("/authorize", response_class=HTMLResponse)
def authorize_screen(client_id: str, redirect_uri: str, state: str = "", scope: str = "openid profile loan.read"):
    return f"""
    <html><head><title>HomeLend — Sign in</title>
    <style>
      body {{ font-family: -apple-system, sans-serif; background:#1a2e1a; color:#fff;
              display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }}
      .card {{ background:#22391f; padding:32px; border-radius:16px; width:320px; }}
      h2 {{ margin-top:0; }}
      input {{ width:100%; padding:10px; margin:8px 0; border-radius:8px; border:none; box-sizing:border-box; }}
      button {{ width:100%; padding:12px; margin-top:12px; border-radius:8px; border:none;
                background:#4caf50; color:white; font-weight:600; font-size:15px; }}
      .app-name {{ color:#9fdca0; font-size:13px; }}
      .scope {{ background:#1a2e1a; padding:10px; border-radius:8px; font-size:13px; margin:12px 0; }}
      .badge {{ display:inline-block; background:#4caf50; color:#fff; font-size:11px; padding:2px 8px; border-radius:10px; margin-bottom:8px;}}
    </style></head>
    <body>
      <div class="card">
        <div class="badge">OpenID Connect</div>
        <div class="app-name">🏠 HomeLend (demo)</div>
        <h2>Sign in to connect</h2>
        <div class="scope"><b>{client_id}</b> requests: <code>{scope}</code></div>
        <form method="post" action="/portals/mortgage/authorize">
          <input type="hidden" name="redirect_uri" value="{redirect_uri}" />
          <input type="hidden" name="state" value="{state}" />
          <input type="hidden" name="client_id" value="{client_id}" />
          <input type="hidden" name="scope" value="{scope}" />
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
    scope: str = Form("openid profile loan.read"),
):
    if username != DEMO_USER["username"] or password != DEMO_USER["password"]:
        return HTMLResponse("<h3>Invalid credentials. Go back and try demo / demo123.</h3>", status_code=401)

    code = str(uuid.uuid4())
    _AUTH_CODES[code] = {"redirect_uri": redirect_uri, "expires": time.time() + 300, "user": username, "scope": scope}
    sep = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(f"{redirect_uri}{sep}code={code}&state={state}", status_code=302)


@router.post("/token")
def exchange_token(grant_type: str = Form(...), code: str = Form(...), redirect_uri: str = Form(...)):
    if grant_type != "authorization_code":
        raise HTTPException(400, "unsupported_grant_type")
    entry = _AUTH_CODES.get(code)
    if not entry or entry["expires"] < time.time():
        raise HTTPException(400, "invalid_grant")
    if entry["redirect_uri"] != redirect_uri:
        raise HTTPException(400, "redirect_uri_mismatch")
    del _AUTH_CODES[code]

    access_token = create_access_token(subject=entry["user"], portal="mortgage", scope=entry["scope"])

    now = int(time.time())
    id_token = jwt.encode(
        {
            "iss": "mortgage-portal-demo",
            "sub": entry["user"],
            "aud": "finpilot",
            "iat": now,
            "exp": now + 3600,
            "name": "Demo User",
            "email": "demo@example.com",
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    return {
        "access_token": access_token,
        "id_token": id_token,
        "token_type": "bearer",
        "expires_in": 3600,
    }


@router.get("/userinfo")
def userinfo(claims: dict = Depends(require_bearer_token("mortgage"))):
    return {"sub": claims["sub"], "name": "Demo User", "email": "demo@example.com"}


@router.get("/api/loan")
def get_loan(claims: dict = Depends(require_bearer_token("mortgage"))):
    return {"loan": LOAN}


@router.get("/api/amortization")
def get_amortization(claims: dict = Depends(require_bearer_token("mortgage"))):
    """Principal vs interest per year, for the dashboard drill-down chart."""
    return {"schedule": AMORTIZATION_SCHEDULE}
