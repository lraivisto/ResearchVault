from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from portal.backend.app.db_resolver import resolve_effective_db
from portal.backend.app.portal_secrets import get_brave_api_key, get_searxng_base_url, get_serper_api_key


@dataclass
class VaultRunResult:
    argv: List[str]
    exit_code: int
    stdout: str
    stderr: str
    truncated: bool


_SENSITIVE_QS_RE = re.compile(r"([?&](?:api_key|token|auth|key|secret)=)[^&]+", flags=re.I)
_URL_CREDS_RE = re.compile(r"(https?://)([^/:]+):([^/@]+)@")
_ABS_PATH_RE = re.compile(r"/(?:Users|home|root|etc|var/log)/[a-zA-Z0-9._/-]+")


def scrub_text(s: str) -> str:
    if not s:
        return s
    s = _URL_CREDS_RE.sub(r"\1REDACTED:REDACTED@", s)
    s = _SENSITIVE_QS_RE.sub(r"\1REDACTED", s)
    s = _ABS_PATH_RE.sub("[REDACTED_PATH]", s)
    return s


def _repo_root() -> Path:
    # .../ResearchVault/portal/backend/app/vault_exec.py -> parents[3] == ResearchVault/
    return Path(__file__).resolve().parents[3]


def run_vault(
    args: List[str],
    *,
    timeout_s: int = 60,
    max_output_bytes: int = 200_000,
    db_path: Optional[str] = None,
) -> VaultRunResult:
    """Execute `python -m scripts.vault <args...>` and return captured output.

    The Portal must be a strict shell over vault.py. This function is the only
    sanctioned execution path.
    """

    root = _repo_root()

    # Ensure rich doesn't emit ANSI in captured output.
    env = dict(os.environ)
    env.setdefault("NO_COLOR", "1")
    env.setdefault("RICH_NO_COLOR", "1")
    env.setdefault("TERM", "dumb")

    # Portal defaults: make watchdog/verify produce real findings by ingesting top URLs from search results.
    # Users can override via environment variables if they want lighter/faster runs.
    env.setdefault("RESEARCHVAULT_WATCHDOG_INGEST_TOP", "2")
    env.setdefault("RESEARCHVAULT_VERIFY_INGEST_TOP", "1")

    # Force the vault subprocess to use the Portal's resolved DB.
    # This is the critical fix for "DB split" issues between CLI and Portal.
    effective = db_path or resolve_effective_db().path
    env["RESEARCHVAULT_DB"] = str(effective)

    # Allow portal-configured secrets (e.g. Brave API key) to drive research commands.
    if not env.get("BRAVE_API_KEY"):
        brave = get_brave_api_key()
        if brave:
            env["BRAVE_API_KEY"] = brave

    if not env.get("SERPER_API_KEY"):
        serper = get_serper_api_key()
        if serper:
            env["SERPER_API_KEY"] = serper

    if not env.get("SEARXNG_BASE_URL"):
        searx = get_searxng_base_url()
        if searx:
            env["SEARXNG_BASE_URL"] = searx

    argv = [sys.executable, "-m", "scripts.vault", *args]

    try:
        proc = subprocess.run(
            argv,
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        exit_code = int(proc.returncode)
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode("utf-8", "ignore") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = (
            (e.stderr.decode("utf-8", "ignore") if isinstance(e.stderr, bytes) else (e.stderr or ""))
            + f"\n\nERROR: Subprocess timed out after {timeout_s}s"
        )
        exit_code = 124  # Standard timeout exit code
    except Exception as e:
        stdout = ""
        stderr = f"ERROR: Subprocess execution failed: {e}"
        exit_code = 1

    truncated = False
    total = len(stdout.encode("utf-8", errors="ignore")) + len(stderr.encode("utf-8", errors="ignore"))
    if total > max_output_bytes:
        truncated = True
        # Hard truncate (keep tail of stderr and head of stdout).
        # Keep it boring and predictable.
        stdout = stdout[: max_output_bytes // 2]
        stderr = stderr[-max_output_bytes // 2 :]

    return VaultRunResult(
        argv=argv,
        exit_code=exit_code,
        stdout=scrub_text(stdout),
        stderr=scrub_text(stderr),
        truncated=truncated,
    )
