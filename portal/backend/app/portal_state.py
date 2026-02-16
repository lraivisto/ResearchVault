from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from threading import Lock
from typing import Any, Optional, Dict


_LOCK = Lock()


def _state_dir() -> Path:
    # Allow tests/dev to redirect state without touching the user's home directory.
    raw = os.getenv("RESEARCHVAULT_PORTAL_STATE_DIR", "~/.researchvault/portal")
    return Path(os.path.expanduser(raw)).resolve()


def state_dir() -> Path:
    return _state_dir()


def _state_file() -> Path:
    return _state_dir() / "state.json"


@dataclass(frozen=True)
class PortalState:
    selected_db_path: Optional[str] = None
    selected_db_set_at: Optional[float] = None
    secrets: Dict[str, str] = field(default_factory=dict)


def _coerce_state(data: Any) -> PortalState:
    if not isinstance(data, dict):
        return PortalState()
    raw_path = data.get("selected_db_path")
    raw_set_at = data.get("selected_db_set_at")
    raw_secrets = data.get("secrets", {})
    return PortalState(
        selected_db_path=str(raw_path) if raw_path else None,
        selected_db_set_at=float(raw_set_at) if raw_set_at else None,
        secrets=dict(raw_secrets) if isinstance(raw_secrets, dict) else {},
    )


def load_state() -> PortalState:
    path = _state_file()
    try:
        with _LOCK:
            if not path.exists():
                return PortalState()
            data = json.loads(path.read_text(encoding="utf-8"))
            return _coerce_state(data)
    except Exception:
        # Be resilient: a corrupt state file should never brick the Portal.
        return PortalState()


def save_state(state: PortalState) -> None:
    # Explicit opt-in for persisting secrets to state.json
    if os.getenv("RESEARCHVAULT_PORTAL_PERSIST_SECRETS") != "1":
        state = PortalState(
            selected_db_path=state.selected_db_path,
            selected_db_set_at=state.selected_db_set_at,
            secrets={},
        )

    path = _state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with _LOCK:
        tmp.write_text(json.dumps(asdict(state), indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)


def get_selected_db_path() -> Optional[str]:
    return load_state().selected_db_path


def set_selected_db_path(path: Optional[str]) -> PortalState:
    if path:
        expanded = str(Path(os.path.expanduser(path)).resolve())
        state = PortalState(selected_db_path=expanded, selected_db_set_at=time.time())
    else:
        state = PortalState(selected_db_path=None, selected_db_set_at=None)
    save_state(state)
    return state
