"""
Holds the access token FinPilot obtained for each portal once the user
completed that portal's auth flow. This is intentionally a simple in-memory
dict — the demo has exactly one user and no persistence requirement. In a
real product this would be a per-user, encrypted, database-backed vault.
"""
import time

_tokens: dict[str, dict] = {}
# shape: { "banking": {"access_token": "...", "obtained_at": 123, "id_token": "..." }, ... }


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
