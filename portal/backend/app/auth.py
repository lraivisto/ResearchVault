from __future__ import annotations

import hmac
import os
import secrets
import time
from dataclasses import dataclass
from typing import Optional

from fastapi import Cookie, HTTPException, status


SESSION_COOKIE_NAME = "rv_session"
SESSION_TTL_S = 12 * 60 * 60  # 12h


@dataclass
class Session:
    created_at: float


# In-memory session store (single-user local app).
_SESSIONS: dict[str, Session] = {}


def _expected_token() -> str:
    expected = os.getenv("RESEARCHVAULT_PORTAL_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Portal token not configured (set RESEARCHVAULT_PORTAL_TOKEN).",
        )
    return expected


def create_session(provided_token: str) -> str:
    expected = _expected_token()
    if not provided_token or not hmac.compare_digest(provided_token, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    sid = secrets.token_urlsafe(32)
    _SESSIONS[sid] = Session(created_at=time.time())
    return sid


def revoke_session(session_id: str) -> None:
    if session_id:
        _SESSIONS.pop(session_id, None)


def require_session(rv_session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME)) -> None:
    if not rv_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    sess = _SESSIONS.get(rv_session)
    if not sess:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if time.time() - sess.created_at > SESSION_TTL_S:
        _SESSIONS.pop(rv_session, None)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
