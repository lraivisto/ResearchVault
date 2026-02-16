---
name: researchvault
description: "Local-first research orchestration engine. Manages state, synthesis, and optional background services (MCP/Watchdog)."
homepage: https://github.com/lraivisto/ResearchVault
disable-model-invocation: true
user-invocable: true
install:
  - id: vault-venv
    kind: exec
    command: python3 -m venv .venv && . .venv/bin/activate && pip install -e .
    label: Initialize ResearchVault (Standard)
env:
  RESEARCHVAULT_DB:
    description: "Optional: Custom path to the SQLite database file."
    required: false
  RESEARCHVAULT_PORTAL_TOKEN:
    description: "Optional: Static token for Portal authentication. If unset, start_portal.sh generates .portal_auth and exports this variable for the backend."
    required: false
  BRAVE_API_KEY:
    description: "Optional: API key for Brave Search."
    required: false
  SERPER_API_KEY:
    description: "Optional: API key for Serper.dev search."
    required: false
  SEARXNG_BASE_URL:
    description: "Optional: Base URL for a SearXNG instance."
    required: false
  RESEARCHVAULT_PORTAL_SCAN_OPENCLAW:
    description: "Optional: Set to '1' to allow Portal DB discovery and DB selection under ~/.openclaw/workspace."
    required: false
  RESEARCHVAULT_PORTAL_PERSIST_SECRETS:
    description: "Optional: Set to '1' to persist Portal-entered provider secrets to ~/.researchvault/portal/secrets.json."
    required: false
  RESEARCHVAULT_PORTAL_INJECT_SECRETS:
    description: "Optional: Set to '1' to inject Portal-managed provider secrets into vault subprocess environments."
    required: false
  RESEARCHVAULT_PORTAL_STATE_DIR:
    description: "Optional: Directory for portal local state and secrets files (default ~/.researchvault/portal)."
    required: false
  RESEARCHVAULT_PORTAL_ALLOW_ANY_DB:
    description: "Optional: Set to 'true' to bypass DB path allowlist checks."
    required: false
  RESEARCHVAULT_PORTAL_HOST:
    description: "Optional: Portal backend bind host (default 127.0.0.1)."
    required: false
  RESEARCHVAULT_PORTAL_PORT:
    description: "Optional: Portal backend port (default 8000)."
    required: false
  RESEARCHVAULT_PORTAL_FRONTEND_HOST:
    description: "Optional: Portal frontend bind host (default 127.0.0.1)."
    required: false
  RESEARCHVAULT_PORTAL_FRONTEND_PORT:
    description: "Optional: Portal frontend port (default 5173)."
    required: false
  RESEARCHVAULT_PORTAL_CORS_ORIGINS:
    description: "Optional: Comma-separated allowed CORS origins for the backend."
    required: false
  RESEARCHVAULT_PORTAL_RELOAD:
    description: "Optional: Set to 'true' to enable backend auto-reload (default true)."
    required: false
  RESEARCHVAULT_PORTAL_COOKIE_SECURE:
    description: "Optional: Set to 'true' to mark auth cookies as Secure."
    required: false
  RESEARCHVAULT_PORTAL_PID_DIR:
    description: "Optional: Directory used by start_portal.sh for PID/log files."
    required: false
metadata:
  openclaw:
    emoji: "🦞"
    requires:
      python: ">=3.13"
---

# ResearchVault 🦞

**Local-first research orchestration engine.**

ResearchVault manages persistent state, synthesis, and autonomous verification for agents.

## Security & Privacy (Local First)

- **Local Storage**: All data is stored in a local SQLite database (~/.researchvault/research_vault.db). No cloud sync.
- **Network Transparency**: Outbound connections occur ONLY for user-requested research or Brave Search (if configured). 
- **SSRF Hardening**: Strict internal network blocking by default. Local/private IPs (localhost, 10.0.0.0/8, etc.) are blocked. Use `--allow-private-networks` to override.
- **Manual Opt-in Services**: Background watchers and MCP servers are in `scripts/services/` and must be started manually.
- **Strict Control**: `disable-model-invocation: true` prevents the model from autonomously starting background tasks.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick Start

1. **Initialize Project**:
   ```bash
   python scripts/vault.py init --objective "Analyze AI trends" --name "Trends-2026"
   ```

2. **Ingest Data**:
   ```bash
   python scripts/vault.py scuttle "https://example.com" --id "trends-2026"
   ```

3. **Autonomous Strategist**:
   ```bash
   python scripts/vault.py strategy --id "trends-2026"
   ```

## Portal (Manual Opt-In)

Start the portal explicitly:

```bash
./start_portal.sh
```

- Backend: `127.0.0.1:8000`
- Frontend: `127.0.0.1:5173`
- Token login: `.portal_auth` and URL hash `#token=<token>`
- Both hosts are supported for browser access:
  - `http://127.0.0.1:5173/#token=<token>`
  - `http://localhost:5173/#token=<token>`

Operational commands:

```bash
./start_portal.sh --status
./start_portal.sh --stop
```

Security parity with CLI:
- SSRF blocking is on by default (private/local/link-local targets denied).
- Portal toggle **Allow private networks** is equivalent to CLI `--allow-private-networks`.

## Optional Services (Manual Start)

- **MCP Server**: `python scripts/services/mcp_server.py`
- **Watchdog**: `python scripts/services/watchdog.py --once`

## Provenance & Maintenance

- **Maintainer**: lraivisto
- **License**: MIT
- **Issues**: [GitHub Issues](https://github.com/lraivisto/ResearchVault/issues)
- **Security**: See [SECURITY.md](SECURITY.md)
