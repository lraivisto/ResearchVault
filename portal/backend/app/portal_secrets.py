from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Optional

from portal.backend.app.portal_state import state_dir


_LOCK = Lock()


def _secrets_file() -> Path:
    return state_dir() / "secrets.json"


@dataclass(frozen=True)
class SecretsStatus:
    brave_api_key_configured: bool
    brave_api_key_source: str  # env|portal|none


def _read_secrets() -> dict[str, Any]:
    path = _secrets_file()
    try:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_secrets(data: dict[str, Any]) -> None:
    path = _secrets_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)
    try:
        os.chmod(path, 0o600)
    except Exception:
        # Best-effort; permissions may not be supported on some platforms.
        pass


def brave_key_status() -> SecretsStatus:
    if os.getenv("BRAVE_API_KEY"):
        return SecretsStatus(brave_api_key_configured=True, brave_api_key_source="env")

    with _LOCK:
        data = _read_secrets()
        key = data.get("brave_api_key")
        if isinstance(key, str) and key.strip():
            return SecretsStatus(brave_api_key_configured=True, brave_api_key_source="portal")

    return SecretsStatus(brave_api_key_configured=False, brave_api_key_source="none")


def get_brave_api_key() -> Optional[str]:
    # Prefer real env vars if set (user controls process env).
    env = os.getenv("BRAVE_API_KEY")
    if env:
        return env

    with _LOCK:
        data = _read_secrets()
        key = data.get("brave_api_key")
        if isinstance(key, str) and key.strip():
            return key.strip()
    return None


def set_brave_api_key(api_key: str) -> SecretsStatus:
    key = (api_key or "").strip()
    if not key:
        raise ValueError("api_key must be non-empty")

    with _LOCK:
        data = _read_secrets()
        data["brave_api_key"] = key
        _write_secrets(data)

    # Make it immediately available to the current backend process too.
    os.environ["BRAVE_API_KEY"] = key
    return brave_key_status()


def clear_brave_api_key() -> SecretsStatus:
    with _LOCK:
        data = _read_secrets()
        data.pop("brave_api_key", None)
        if data:
            _write_secrets(data)
        else:
            try:
                _secrets_file().unlink(missing_ok=True)
            except Exception:
                pass

    # Clear from the backend process env (this does not affect the user's shell).
    os.environ.pop("BRAVE_API_KEY", None)
    return brave_key_status()

