from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


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
    # .../ResearchVault/portal/backend/app/vault_exec.py -> parents[4] == ResearchVault/
    return Path(__file__).resolve().parents[4]


def run_vault(
    args: List[str],
    *,
    timeout_s: int = 60,
    max_output_bytes: int = 200_000,
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

    argv = [sys.executable, "-m", "scripts.vault", *args]

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
        exit_code=int(proc.returncode),
        stdout=scrub_text(stdout),
        stderr=scrub_text(stderr),
        truncated=truncated,
    )
