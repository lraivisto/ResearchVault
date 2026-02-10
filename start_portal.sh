
#!/bin/bash

# Fail fast
set -euo pipefail

# Global PIDs for cleanup
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "🛑 Shutting down Portal..."
    
    # 1. Terminate specific jobs first (allows graceful shutdown logs)
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi

    # 2. Wait for them to actually finish logging/exiting
    # This prevents the prompt from appearing while uvicorn is still printing "Shutting down..."
    wait 2>/dev/null || true
    sleep 1.2
    
    # 3. Final safety net: kill process group (excluding self if possible, but trap - ensures no loop)
    trap - SIGINT SIGTERM EXIT
    kill -- -$$ 2>/dev/null || true
}

# Trap signals
trap cleanup SIGINT SIGTERM EXIT

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# DB resolution:
# - If RESEARCHVAULT_DB is already set, respect it.
# - If exactly one known DB exists, pin to it for consistency.
# - If multiple exist, let the Portal auto-detect and expose a UI selector (no silent overrides).
if [ -z "${RESEARCHVAULT_DB:-}" ]; then
    LEGACY_DB="$HOME/.openclaw/workspace/memory/research_vault.db"
    DEFAULT_DB="$HOME/.researchvault/research_vault.db"
    LEGACY_EXISTS="false"
    DEFAULT_EXISTS="false"
    if [ -f "$LEGACY_DB" ]; then LEGACY_EXISTS="true"; fi
    if [ -f "$DEFAULT_DB" ]; then DEFAULT_EXISTS="true"; fi

    if [ "$LEGACY_EXISTS" = "true" ] && [ "$DEFAULT_EXISTS" = "false" ]; then
        echo "Using legacy workspace database: $LEGACY_DB"
        export RESEARCHVAULT_DB="$LEGACY_DB"
    elif [ "$DEFAULT_EXISTS" = "true" ] && [ "$LEGACY_EXISTS" = "false" ]; then
        echo "Using default database: $DEFAULT_DB"
        export RESEARCHVAULT_DB="$DEFAULT_DB"
    elif [ "$DEFAULT_EXISTS" = "true" ] && [ "$LEGACY_EXISTS" = "true" ]; then
        echo "Multiple vault DBs detected (legacy + default). The Portal will prompt you to choose."
    fi
fi

echo "Starting ResearchVault Portal..."

# Cleanup old runs if they exist
echo "Cleaning up any old portal processes..."
pkill -f "run_portal.py" || true
pkill -f "vite --port 5173" || true

# Auth: backend requires RESEARCHVAULT_PORTAL_TOKEN.
# Mirror OpenClaw: Generate if missing, persist locally.
AUTH_FILE=".portal_auth"
if [ -z "${RESEARCHVAULT_PORTAL_TOKEN:-}" ]; then
    if [ -f "$AUTH_FILE" ]; then
        echo "Loading token from $AUTH_FILE..."
        export RESEARCHVAULT_PORTAL_TOKEN=$(cat "$AUTH_FILE")
    else
        echo "Generating new portal token..."
        # Use python to generate a secure token (works on most systems)
        NEW_TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(24))")
        echo "$NEW_TOKEN" > "$AUTH_FILE"
        chmod 600 "$AUTH_FILE"
        export RESEARCHVAULT_PORTAL_TOKEN="$NEW_TOKEN"
        # Ensure it's ignored by git
        if ! grep -q "$AUTH_FILE" .gitignore 2>/dev/null; then
            echo "$AUTH_FILE" >> .gitignore
        fi
    fi
fi

# Display token for easy access (critical for first-time users)
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  Portal Access Token: $RESEARCHVAULT_PORTAL_TOKEN"
echo ""
echo "  To log in, use this URL (token pre-filled):"
echo "  http://localhost:5173/#token=$RESEARCHVAULT_PORTAL_TOKEN"
echo "══════════════════════════════════════════════════════════"
echo ""

# Search Providers:
# The vault can fall back to best-effort providers (DuckDuckGo/Wikipedia), but API-backed providers
# (Brave/Serper/SearxNG) are recommended for higher quality and consistency.
SEARCH_PROVIDER_OK="false"
if [ -n "${BRAVE_API_KEY:-}" ] || [ -n "${SERPER_API_KEY:-}" ] || [ -n "${SEARXNG_BASE_URL:-}" ]; then
    SEARCH_PROVIDER_OK="true"
else
    SECRETS_FILE="$HOME/.researchvault/portal/secrets.json"
    if [ -f "$SECRETS_FILE" ]; then
        if python3 - "$SECRETS_FILE" <<'PY'
import json, sys
from pathlib import Path

p = Path(sys.argv[1])
try:
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        brave = data.get("brave_api_key")
        serper = data.get("serper_api_key")
        searx = data.get("searxng_base_url")
        if isinstance(brave, str) and brave.strip():
            raise SystemExit(0)
        if isinstance(serper, str) and serper.strip():
            raise SystemExit(0)
        if isinstance(searx, str) and searx.strip():
            raise SystemExit(0)
except Exception:
    pass
raise SystemExit(1)
PY
        then
            SEARCH_PROVIDER_OK="true"
        fi
    fi
fi

if [ "$SEARCH_PROVIDER_OK" != "true" ]; then
    echo ""
    echo "WARNING: No API-backed search provider configured (Brave/Serper/SearxNG)."
    echo "  - The Vault will fall back to best-effort providers (DuckDuckGo/Wikipedia)."
    echo "  - Fix: open Portal -> Diagnostics -> configure Brave (recommended), Serper, or SearxNG."
    echo ""

    if [ "${RESEARCHVAULT_PORTAL_REQUIRE_SEARCH_PROVIDER:-false}" = "true" ] || [ "${RESEARCHVAULT_PORTAL_REQUIRE_BRAVE_API_KEY:-false}" = "true" ]; then
        echo "RESEARCHVAULT_PORTAL_REQUIRE_SEARCH_PROVIDER=true; refusing to start." >&2
        exit 1
    fi
fi

# Portal defaults: turn query-search results into real findings by auto-ingesting top URLs.
# Keep these as env vars so power users can tune it without editing code.
export RESEARCHVAULT_WATCHDOG_INGEST_TOP="${RESEARCHVAULT_WATCHDOG_INGEST_TOP:-2}"
export RESEARCHVAULT_VERIFY_INGEST_TOP="${RESEARCHVAULT_VERIFY_INGEST_TOP:-1}"

# Dev CORS defaults (frontend may be opened as localhost or 127.0.0.1).
export RESEARCHVAULT_PORTAL_CORS_ORIGINS="${RESEARCHVAULT_PORTAL_CORS_ORIGINS:-http://localhost:5173,http://127.0.0.1:5173}"

# 1. Backend Setup
echo "[1/4] Checking Python Dependencies..."
UV_BIN="${UV_BIN:-$HOME/.local/bin/uv}"
if [ ! -x "$UV_BIN" ]; then
    if command -v uv >/dev/null 2>&1; then
        UV_BIN="$(command -v uv)"
    else
        echo "Error: uv not found. Install uv or set UV_BIN." >&2
        exit 1
    fi
fi

echo "Using uv from $UV_BIN"
"$UV_BIN" sync


# 2. Frontend Setup
echo "[2/4] Checking Frontend Dependencies..."
pushd portal/frontend >/dev/null
if [ ! -d "node_modules" ]; then
    echo "Installing missing node_modules..."
    if [ -f package-lock.json ]; then
        npm ci
    else
        npm install
    fi
fi
popd >/dev/null

# 3. Start Backend
echo "[3/4] Launching Backend (FastAPI)..."

# Port conflict check
BACKEND_PORT=8000
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "Warning: Port $BACKEND_PORT is already in use."
    echo "Attempting to identify process..."
    lsof -i :$BACKEND_PORT
    # We won't kill it automatically to be safe, but we'll try to let uvicorn fail or bind.
fi

# Use 'uv run' via full path
"$UV_BIN" run run_portal.py &
BACKEND_PID=$!

# Wait for backend to be ready.
python3 - <<'PY'
import time
import urllib.request

url = "http://127.0.0.1:8000/health"
deadline = time.time() + 20
while time.time() < deadline:
    try:
        with urllib.request.urlopen(url, timeout=1) as r:
            if r.status == 200:
                break
    except Exception:
        time.sleep(0.25)
else:
    print("Warning: backend did not become ready within 20s", flush=True)
PY

# 4. Start Frontend
echo "[4/4] Launching Frontend (Vite)..."
pushd portal/frontend >/dev/null
npm run dev -- --port 5173 &
FRONTEND_PID=$!
popd >/dev/null

# Wait
PORTAL_URL="http://localhost:5173/#token=$RESEARCHVAULT_PORTAL_TOKEN"
echo "Portal is running!"
echo "Backend:  http://localhost:8000/docs"
echo "Frontend: http://localhost:5173"
echo "Direct:   $PORTAL_URL"

# Auto-open if on macOS/Linux with display
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$PORTAL_URL"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$PORTAL_URL"
fi

wait
