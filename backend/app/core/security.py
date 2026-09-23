"""
Shared helpers for issuing and verifying access tokens.

Every simulated portal (banking, mortgage, credit card, brokerage) uses these
so the *pattern* is identical, even though the auth *flow* in front of it
differs per portal (Authorization Code, OIDC, Client Credentials, etc).
This mirrors how real fintech APIs almost always land on a signed bearer
token at the end, no matter how you got there.
"""
import time
import uuid
from jose import jwt, JWTError
from fastapi import Header, HTTPException
from app.core.config import settings


def create_access_token(subject: str, portal: str, scope: str = "read", expires_in: int = 3600) -> str:
    now = int(time.time())
    payload = {
        "sub": subject,          # the "user" this token represents
        "portal": portal,        # which simulated portal issued it (banking, mortgage, ...)
        "scope": scope,
        "iat": now,
        "exp": now + expires_in,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_bearer_token(portal: str):
    """FastAPI dependency factory: verifies the Authorization header and that
    the token was actually issued by *this* portal (so a mortgage token can't
    be replayed against the banking API, etc)."""
    def _dep(authorization: str = Header(None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing bearer token")
        token = authorization.removeprefix("Bearer ").strip()
        claims = decode_access_token(token)
        if claims.get("portal") != portal:
            raise HTTPException(status_code=403, detail="Token not valid for this portal")
        return claims
    return _dep
