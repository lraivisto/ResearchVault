import pytest

from fastapi import HTTPException


def test_stateless_session_cookie_roundtrip(monkeypatch):
    import portal.backend.app.auth as auth

    monkeypatch.setenv("RESEARCHVAULT_PORTAL_TOKEN", "t0k3n")

    sid = auth.create_session("t0k3n")
    assert isinstance(sid, str) and "." in sid

    # Should not raise.
    auth.require_session(rv_session=sid)


def test_stateless_session_cookie_expires(monkeypatch):
    import portal.backend.app.auth as auth

    monkeypatch.setenv("RESEARCHVAULT_PORTAL_TOKEN", "t0k3n")

    now = 1_000_000
    monkeypatch.setattr(auth.time, "time", lambda: now)

    sid = auth.create_session("t0k3n")
    auth.require_session(rv_session=sid)

    now = now + auth.SESSION_TTL_S + 1
    monkeypatch.setattr(auth.time, "time", lambda: now)

    with pytest.raises(HTTPException) as e:
        auth.require_session(rv_session=sid)
    assert "expired" in str(e.value.detail).lower()

