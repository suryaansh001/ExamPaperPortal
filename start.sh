#!/usr/bin/env bash
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Start FastAPI backend on Railway's provided PORT (default 8000 locally)
BACKEND_PORT="${PORT:-8000}"
echo "Starting FastAPI backend on port ${BACKEND_PORT}..."

# Start uvicorn (this will block until the server stops)
exec uvicorn main:app --host 0.0.0.0 --port "${BACKEND_PORT}"

