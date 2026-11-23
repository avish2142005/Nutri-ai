#!/usr/bin/env bash
# ==============================================================================
# KrishiNetra Linux / macOS Production Startup Script
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=============================================================================="
echo "          Starting KrishiNetra Production Server"
echo "=============================================================================="

# 1. Check Python virtual environment
if [ ! -d "farmai/backend/.venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv farmai/backend/.venv
    source farmai/backend/.venv/bin/activate
    pip install --upgrade pip
    pip install -r farmai/backend/requirements.txt
else
    source farmai/backend/.venv/bin/activate
fi

# 2. Check Frontend Build
if [ ! -f "farmai/frontend/dist/index.html" ]; then
    echo "Compiling frontend assets..."
    cd farmai/frontend
    npm ci
    npm run build
    cd "$DIR"
fi

# 3. Launch Production Server
echo "Launching KrishiNetra Production Server on http://0.0.0.0:8000 ..."
cd farmai/backend
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
