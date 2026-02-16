from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Optional

from portal.backend.app.portal_state import state_dir


_LOCK = Lock()
_RUNTIME_SECRETS: dict[str, str] = {}


def _secrets_file() -> Path:
    return state_dir() / "secrets.json"


def _persist_enabled() -> bool:
    return os.getenv("RESEARCHVAULT_PORTAL_PERSIST_SECRETS") == "1"


@dataclass(frozen=True)
class SecretsStatus:
    brave_api_key_configured: bool
    brave_api_key_source: str  # env|portal|none
    serper_api_key_configured: bool
    serper_api_key_source: str  # env|portal|none
    searxng_base_url_configured: bool
    searxng_base_url_source: str  # env|portal|none
    searxng_base_url: Optional[str] = None


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


def _runtime_secret(name: str) -> Optional[str]:
    val = _RUNTIME_SECRETS.get(name)
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def secrets_status() -> SecretsStatus:
    brave_env = os.getenv("BRAVE_API_KEY")
    serper_env = os.getenv("SERPER_API_KEY")
    searx_env = os.getenv("SEARXNG_BASE_URL")

    brave_conf = bool(brave_env)
    serper_conf = bool(serper_env)
    searx_conf = bool(searx_env)

    brave_src = "env" if brave_conf else "none"
    serper_src = "env" if serper_conf else "none"
    searx_src = "env" if searx_conf else "none"
    searx_val: Optional[str] = searx_env if searx_conf else None

    with _LOCK:
        runtime = dict(_RUNTIME_SECRETS)
        data = _read_secrets() if _persist_enabled() else {}

    if not brave_conf:
        key = runtime.get("brave_api_key")
        if not isinstance(key, str) or not key.strip():
            key = data.get("brave_api_key")
        if isinstance(key, str) and key.strip():
            brave_conf = True
            brave_src = "portal"

    if not serper_conf:
        key = runtime.get("serper_api_key")
        if not isinstance(key, str) or not key.strip():
            key = data.get("serper_api_key")
        if isinstance(key, str) and key.strip():
            serper_conf = True
            serper_src = "portal"

    if not searx_conf:
        raw = runtime.get("searxng_base_url")
        if not isinstance(raw, str) or not raw.strip():
            raw = data.get("searxng_base_url")
        if isinstance(raw, str) and raw.strip():
            searx_conf = True
            searx_src = "portal"
            searx_val = raw.strip()

    return SecretsStatus(
        brave_api_key_configured=brave_conf,
        brave_api_key_source=brave_src,
        serper_api_key_configured=serper_conf,
        serper_api_key_source=serper_src,
        searxng_base_url_configured=searx_conf,
        searxng_base_url_source=searx_src,
        searxng_base_url=searx_val,
    )


def brave_key_status() -> SecretsStatus:
    # Back-compat alias.
    return secrets_status()


def get_brave_api_key() -> Optional[str]:
    # Prefer real env vars if set (user controls process env).
    env = os.getenv("BRAVE_API_KEY")
    if env:
        return env

    with _LOCK:
        runtime = _runtime_secret("brave_api_key")
        if runtime:
            return runtime
        if _persist_enabled():
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
        _RUNTIME_SECRETS["brave_api_key"] = key
        if _persist_enabled():
            data = _read_secrets()
            data["brave_api_key"] = key
            _write_secrets(data)
    return secrets_status()


def clear_brave_api_key() -> SecretsStatus:
    with _LOCK:
        _RUNTIME_SECRETS.pop("brave_api_key", None)
        if _persist_enabled():
            data = _read_secrets()
            data.pop("brave_api_key", None)
            if data:
                _write_secrets(data)
            else:
                try:
                    _secrets_file().unlink(missing_ok=True)
                except Exception:
                    pass
    return secrets_status()


def get_serper_api_key() -> Optional[str]:
    env = os.getenv("SERPER_API_KEY")
    if env:
        return env

    with _LOCK:
        runtime = _runtime_secret("serper_api_key")
        if runtime:
            return runtime
        if _persist_enabled():
            data = _read_secrets()
            key = data.get("serper_api_key")
            if isinstance(key, str) and key.strip():
                return key.strip()
    return None


def set_serper_api_key(api_key: str) -> SecretsStatus:
    key = (api_key or "").strip()
    if not key:
        raise ValueError("api_key must be non-empty")

    with _LOCK:
        _RUNTIME_SECRETS["serper_api_key"] = key
        if _persist_enabled():
            data = _read_secrets()
            data["serper_api_key"] = key
            _write_secrets(data)
    return secrets_status()


def clear_serper_api_key() -> SecretsStatus:
    with _LOCK:
        _RUNTIME_SECRETS.pop("serper_api_key", None)
        if _persist_enabled():
            data = _read_secrets()
            data.pop("serper_api_key", None)
            if data:
                _write_secrets(data)
            else:
                try:
                    _secrets_file().unlink(missing_ok=True)
                except Exception:
                    pass
    return secrets_status()


def get_searxng_base_url() -> Optional[str]:
    env = os.getenv("SEARXNG_BASE_URL")
    if env and env.strip():
        return env.strip()

    with _LOCK:
        runtime = _runtime_secret("searxng_base_url")
        if runtime:
            return runtime
        if _persist_enabled():
            data = _read_secrets()
            raw = data.get("searxng_base_url")
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
    return None


def set_searxng_base_url(url: str) -> SecretsStatus:
    val = (url or "").strip()
    if not val:
        raise ValueError("base_url must be non-empty")

    with _LOCK:
        _RUNTIME_SECRETS["searxng_base_url"] = val
        if _persist_enabled():
            data = _read_secrets()
            data["searxng_base_url"] = val
            _write_secrets(data)
    return secrets_status()


def clear_searxng_base_url() -> SecretsStatus:
    with _LOCK:
        _RUNTIME_SECRETS.pop("searxng_base_url", None)
        if _persist_enabled():
            data = _read_secrets()
            data.pop("searxng_base_url", None)
            if data:
                _write_secrets(data)
            else:
                try:
                    _secrets_file().unlink(missing_ok=True)
                except Exception:
                    pass
    return secrets_status()
