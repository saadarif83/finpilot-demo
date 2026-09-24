"""
Holds the access token FinPilot obtained for each portal once the user
completed that portal's auth flow. Intentionally simple/in-memory — the demo
has exactly one user and no persistence requirement, and resets on every
backend restart (worth knowing for demo day: reconnect after any redeploy).
"""
import time

_tokens: dict[str, dict] = {}


def set_token(portal: str, access_token: str, id_token: str | None = None):
    _tokens[portal] = {"access_token": access_token, "id_token": id_token, "obtained_at": time.time()}


def get_token(portal: str) -> str | None:
    entry = _tokens.get(portal)
    return entry["access_token"] if entry else None


def is_connected(portal: str) -> bool:
    return portal in _tokens


def connected_portals() -> list[str]:
    return list(_tokens.keys())


def disconnect(portal: str):
    _tokens.pop(portal, None)


def disconnect_all():
    _tokens.clear()
