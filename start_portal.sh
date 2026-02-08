
#!/bin/bash

# Fail fast; trap will still reap background processes.
set -euo pipefail

# Kill background processes on exit (best-effort; don't spam errors during shutdown).
trap "trap - SIGTERM && kill -- -$$ 2>/dev/null || true" SIGINT SIGTERM EXIT

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "Starting ResearchVault Portal..."

# Auth: backend requires RESEARCHVAULT_PORTAL_TOKEN. We'll generate one if not provided.
if [ -z "${RESEARCHVAULT_PORTAL_TOKEN:-}" ]; then
    RESEARCHVAULT_PORTAL_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
    export RESEARCHVAULT_PORTAL_TOKEN
    echo "Generated RESEARCHVAULT_PORTAL_TOKEN for this session."
fi

# Pass token into the Vite dev server (client reads VITE_* env vars).
export VITE_RESEARCHVAULT_PORTAL_TOKEN="${VITE_RESEARCHVAULT_PORTAL_TOKEN:-$RESEARCHVAULT_PORTAL_TOKEN}"

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
popd >/dev/null

# Wait
echo "Portal is running!"
echo "Backend:  http://localhost:8000/docs"
echo "Frontend: http://localhost:5173"
echo "Token:    $RESEARCHVAULT_PORTAL_TOKEN"
echo "Link:     http://localhost:5173/?token=$RESEARCHVAULT_PORTAL_TOKEN"
wait
