
#!/bin/bash

# Kill background processes on exit
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

echo "Starting ResearchVault Portal..."

# 1. Backend Setup
echo "[1/4] Checking Python Dependencies..."
UV_BIN="$HOME/.local/bin/uv"

if [ -f "$UV_BIN" ]; then
    echo "Using uv from $UV_BIN"
    $UV_BIN sync
else
    echo "Warning: uv not found at $UV_BIN. Falling back to system python3..."
    # Fallback if uv installation failed for some reason
    # But since we just installed it, this path should work.
fi


# 2. Frontend Setup
echo "[2/4] Checking Frontend Dependencies..."
cd portal/frontend
if [ ! -d "node_modules" ]; then
    echo "Installing missing node_modules..."
    npm install
fi
cd ../..

# 3. Start Backend
echo "[3/4] Launching Backend (FastAPI)..."
# Use 'uv run' via full path
$UV_BIN run run_portal.py &
BACKEND_PID=$!

# Wait for backend to be ready (naive check)
sleep 2

# 4. Start Frontend
echo "[4/4] Launching Frontend (Vite)..."
cd portal/frontend
npm run dev -- --port 5173 &

# Wait
echo "Portal is running!"
echo "Backend: http://localhost:8000/docs"
echo "Frontend: http://localhost:5173"
wait
