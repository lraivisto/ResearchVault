---
name: researchvault
description: "Local-first research orchestration engine. Manages state, synthesis, and optional background services (MCP/Watchdog)."
homepage: https://github.com/lraivisto/ResearchVault
disable-model-invocation: true
user-invocable: true
metadata:
  openclaw:
    emoji: "🦞"
    requires:
      python: ">=3.13"
      env:
        RESEARCHVAULT_DB:
          description: "Optional: Custom path to the SQLite database file."
          required: false
        BRAVE_API_KEY:
          description: "Optional: Brave Search API key."
          required: false
        SERPER_API_KEY:
          description: "Optional: Serper API key."
          required: false
        SEARXNG_BASE_URL:
          description: "Optional: SearXNG base URL."
          required: false
        RESEARCHVAULT_PORTAL_TOKEN:
          description: "Optional: static portal token. If unset, start_portal.sh sources/generates .portal_auth and exports this env var."
          required: false
        RESEARCHVAULT_PORTAL_ALLOWED_DB_ROOTS:
          description: "Optional: comma-separated absolute DB roots. Default: ~/.researchvault,/tmp."
          required: false
        RESEARCHVAULT_PORTAL_STATE_DIR:
          description: "Optional: portal state directory (default ~/.researchvault/portal)."
          required: false
        RESEARCHVAULT_PORTAL_HOST:
          description: "Optional: backend bind host."
          required: false
        RESEARCHVAULT_PORTAL_PORT:
          description: "Optional: backend bind port."
          required: false
        RESEARCHVAULT_PORTAL_FRONTEND_HOST:
          description: "Optional: frontend bind host."
          required: false
        RESEARCHVAULT_PORTAL_FRONTEND_PORT:
          description: "Optional: frontend bind port."
          required: false
        RESEARCHVAULT_PORTAL_CORS_ORIGINS:
          description: "Optional: comma-separated CORS origins for backend."
          required: false
        RESEARCHVAULT_PORTAL_RELOAD:
          description: "Optional: set to 'true' for backend auto-reload."
          required: false
        RESEARCHVAULT_PORTAL_COOKIE_SECURE:
          description: "Optional: set to 'true' to mark auth cookie Secure."
          required: false
        RESEARCHVAULT_PORTAL_PID_DIR:
          description: "Optional: start_portal.sh PID/log directory."
          required: false
        RESEARCHVAULT_PORTAL_SHOW_TOKEN:
          description: "Optional: set to '1' to print tokenized portal URLs."
          required: false
        RESEARCHVAULT_SEARCH_PROVIDERS:
          description: "Optional: search provider order override."
          required: false
        RESEARCHVAULT_WATCHDOG_INGEST_TOP:
          description: "Optional: watchdog ingest top-k override."
          required: false
        RESEARCHVAULT_VERIFY_INGEST_TOP:
          description: "Optional: verify ingest top-k override."
          required: false
        RESEARCHVAULT_MCP_TRANSPORT:
          description: "Optional: MCP server transport override."
          required: false
        REQUESTS_CA_BUNDLE:
          description: "Optional: custom CA bundle for HTTPS verification."
          required: false
        SSL_CERT_FILE:
          description: "Optional: custom CA certificate file."
          required: false
---

# ResearchVault 🦞

ResearchVault is a local-first research operations toolkit: a CLI for ingestion/search/verification/synthesis plus an optional local portal UI.
It is designed for explicit operator control: manual start, local state, and predictable defaults.

## Quick Reference

| Task | Command / Action | Notes |
|---|---|---|
| Create project | `python scripts/vault.py init --id "ops-demo" --name "Ops Demo" --objective "Track AI agent changes"` | Creates the project in the local SQLite vault. |
| Ingest URL | `python scripts/vault.py scuttle "https://example.com" --id "ops-demo"` | SSRF guard is default-deny. Use `--allow-private-networks` only when intentional. |
| Search | `python scripts/vault.py search --query "agent benchmark updates" --format rich` | Uses configured providers from env; quality depends on provider keys/base URL. |
| Strategy | `python scripts/vault.py strategy --id "ops-demo"` | Produces next-best-action guidance from current project state. |
| Verify | `python scripts/vault.py verify plan --id "ops-demo" && python scripts/vault.py verify run --id "ops-demo" --limit 5` | Plans and executes verification missions from low-confidence findings. |
| Synthesize / Graph | `python scripts/vault.py synthesize --id "ops-demo"` | Builds links between findings/artifacts; inspect graph in the Portal Graph view. |
| Export | `python scripts/vault.py export --id "ops-demo" --format markdown --output ~/.researchvault/ops-demo.md` | Export path must be under `~/.researchvault` (or test temp paths). |
| Start portal | `./start_portal.sh` | Backend defaults to `127.0.0.1:8000`; frontend to `127.0.0.1:5173`. |
| Stop portal | `./start_portal.sh --stop` | Stops backend and frontend processes started by script. |
| Portal status | `./start_portal.sh --status` | Shows process/health status and UI reachability. |

## Trust Model / Security Notes

- Local-first by default: data is stored in a local SQLite DB (default `~/.researchvault/research_vault.db`).
- Portal is local by default: backend/frontend bind loopback addresses unless you explicitly override host vars.
- Portal execution model: the backend runs `scripts.vault` subprocesses; it is a controlled shell over the CLI.
- Portal auth token is required: `start_portal.sh` loads or generates `.portal_auth`, exports `RESEARCHVAULT_PORTAL_TOKEN`, and keeps `.portal_auth` at `chmod 600`.
- SSRF posture is default-deny for local/private/link-local targets; private-network access is explicit opt-in via CLI `--allow-private-networks` (Portal toggle maps to this behavior).
- DB selection is root-scoped by `RESEARCHVAULT_PORTAL_ALLOWED_DB_ROOTS` (default `~/.researchvault,/tmp`).
- Portal does not discover or allow selecting DBs under `~/.openclaw/workspace`.
- Provider secrets are env-only (`BRAVE_API_KEY`, `SERPER_API_KEY`, `SEARXNG_BASE_URL`); Portal does not persist/write secrets and does not inject provider secrets into vault subprocesses.
- `disable-model-invocation: true` enforces no autonomous background side effects without explicit user action.

## Installation (Manual, Local)

Manual install in a local virtual environment (no embedded installer actions):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## CLI Quick Start

```bash
PROJECT_ID="ops-demo"

python scripts/vault.py init \
  --id "$PROJECT_ID" \
  --name "Ops Demo" \
  --objective "Track AI agent changes"

python scripts/vault.py scuttle "https://example.com" --id "$PROJECT_ID"
python scripts/vault.py list
python scripts/vault.py strategy --id "$PROJECT_ID"
```

## Portal (Manual Opt-In)

Start manually:

```bash
./start_portal.sh
```

Defaults:

- Backend: `127.0.0.1:8000`
- Frontend: `127.0.0.1:5173`
- Login pages:
  - `http://127.0.0.1:5173/`
  - `http://localhost:5173/`

Token flow:

- `start_portal.sh` loads existing `.portal_auth` or generates one.
- It exports `RESEARCHVAULT_PORTAL_TOKEN` before backend launch.
- UI login accepts manual token entry or token URL hash: `#token=<token>`.

Operational controls:

```bash
./start_portal.sh --status
./start_portal.sh --stop
```

Operational notes:

- Portal expects local use and local DB roots.
- DB access is constrained by `RESEARCHVAULT_PORTAL_ALLOWED_DB_ROOTS`.
- OpenClaw workspace DB paths are intentionally excluded.
- Portal private-network ingest toggle maps to CLI `--allow-private-networks`.

## Configuration

### Database

- `RESEARCHVAULT_DB`: Override DB file path used by CLI/Portal subprocesses.
- `RESEARCHVAULT_PORTAL_ALLOWED_DB_ROOTS`: Comma-separated absolute roots allowed for Portal DB selection/discovery. Default: `~/.researchvault,/tmp`.
- `RESEARCHVAULT_PORTAL_STATE_DIR`: Portal state location (`state.json`). Default: `~/.researchvault/portal`.

### Portal Networking

- `RESEARCHVAULT_PORTAL_HOST`: Backend bind host. Default: `127.0.0.1`.
- `RESEARCHVAULT_PORTAL_PORT`: Backend bind port. Default: `8000`.
- `RESEARCHVAULT_PORTAL_FRONTEND_HOST`: Frontend bind host. Default: `127.0.0.1`.
- `RESEARCHVAULT_PORTAL_FRONTEND_PORT`: Frontend bind port. Default: `5173`.
- `RESEARCHVAULT_PORTAL_CORS_ORIGINS`: Comma-separated backend CORS origins; `start_portal.sh` sets local frontend origins by default.
- `RESEARCHVAULT_PORTAL_COOKIE_SECURE`: Set `true` to mark auth cookie `Secure` (HTTPS deployments).
- `RESEARCHVAULT_PORTAL_RELOAD`: Backend auto-reload toggle (`true` by default in local dev).

### Providers

- `BRAVE_API_KEY`: Brave Search API key.
- `SERPER_API_KEY`: Serper API key.
- `SEARXNG_BASE_URL`: SearXNG base URL.
- `RESEARCHVAULT_SEARCH_PROVIDERS`: Explicit provider order override.

### TLS / CA

- `REQUESTS_CA_BUNDLE`: Custom CA bundle path for HTTPS verification.
- `SSL_CERT_FILE`: Custom CA certificate file path.

### Advanced / Rare

- `RESEARCHVAULT_PORTAL_PID_DIR`: Portal PID/log directory used by `start_portal.sh`.
- `RESEARCHVAULT_PORTAL_SHOW_TOKEN`: Set `1` to print tokenized portal URLs in terminal output.
- `RESEARCHVAULT_WATCHDOG_INGEST_TOP`: Watchdog ingest top-k override.
- `RESEARCHVAULT_VERIFY_INGEST_TOP`: Verify ingest top-k override.
- `RESEARCHVAULT_MCP_TRANSPORT`: MCP transport override (default CLI transport is `stdio`).

## Troubleshooting

- **Symptom:** Portal login returns `401 Unauthorized`.
  **Cause:** Wrong token or backend missing `RESEARCHVAULT_PORTAL_TOKEN`.
  **Fix:** Restart with `./start_portal.sh`, then use token from `.portal_auth` or `#token=<token>` URL hash.

- **Symptom:** Tokenized URL does not log in.
  **Cause:** Token mismatch, stale cookie/session, or wrong frontend host/port.
  **Fix:** Confirm `.portal_auth`, clear browser cookies for the portal origin, and verify `RESEARCHVAULT_PORTAL_FRONTEND_PORT`/URL.

- **Symptom:** DB rejected or cannot be selected in Portal.
  **Cause:** DB path is outside `RESEARCHVAULT_PORTAL_ALLOWED_DB_ROOTS` or under denied OpenClaw workspace path.
  **Fix:** Move/use a DB under allowed roots (default `~/.researchvault,/tmp`) and retry.

- **Symptom:** `Blocked host` when ingesting `localhost`, `127.0.0.1`, `169.254.*`, or private RFC1918 targets.
  **Cause:** SSRF protection default-deny blocked private/local/link-local addresses.
  **Fix:** Only if intentional, rerun with `--allow-private-networks`.

- **Symptom:** Portal fails to start because port is already in use.
  **Cause:** Existing process is bound to backend/frontend ports.
  **Fix:** Run `./start_portal.sh --stop`, then restart; or change host/port env vars.

- **Symptom:** `vault list` or portal appears empty (`No projects found`).
  **Cause:** You are using a different DB path than expected.
  **Fix:** Check `RESEARCHVAULT_DB`, confirm Portal current DB in diagnostics, and align to the intended file.

- **Symptom:** Provider-backed search is not working.
  **Cause:** Provider env vars are unset or invalid.
  **Fix:** Set `BRAVE_API_KEY` and/or `SERPER_API_KEY` and/or `SEARXNG_BASE_URL`, then rerun search/verify/watchdog.

- **Symptom:** HTTPS certificate verification failures.
  **Cause:** Missing private CA/intermediate trust configuration.
  **Fix:** Set `REQUESTS_CA_BUNDLE` or `SSL_CERT_FILE` to the correct CA file and retry.

## Optional Services (Manual Start)

Manual only; nothing auto-starts:

- MCP Server: `python scripts/services/mcp_server.py`
- Watchdog: `python scripts/services/watchdog.py --once`

## Provenance

- **Maintainer**: lraivisto
- **License**: MIT
- **Issues**: [GitHub Issues](https://github.com/lraivisto/ResearchVault/issues)
- **Security**: See [SECURITY.md](SECURITY.md)
