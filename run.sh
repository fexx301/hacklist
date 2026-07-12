#!/usr/bin/env bash
# Start Hacklist: FastAPI backend (port 8001) + Next.js frontend (port 3000/3001).
# Ctrl+C stops both.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON=".venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    echo "No virtualenv found. Set it up first:"
    echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi
if [ ! -d frontend/node_modules ]; then
    echo "Frontend dependencies missing. Install them first:"
    echo "  cd frontend && npm install"
    exit 1
fi

"$PYTHON" -m uvicorn api:app --host 127.0.0.1 --port 8001 &
BACKEND_PID=$!
trap 'kill "$BACKEND_PID" 2>/dev/null' EXIT

# No --port flag: Next picks 3000, or 3001 if 3000 is busy — both are CORS-allowed.
cd frontend && npx next dev
