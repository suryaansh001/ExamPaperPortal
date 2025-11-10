#!/usr/bin/env bash
set -euo pipefail

# Start Node email-service on internal port 4000
echo "Starting Nodemailer email-service on port 4000..."
pushd "$(dirname "$0")/email-service" >/dev/null
npm ci
PORT=4000 node server.js &
EMAIL_SERVICE_PID=$!
popd >/dev/null

# Export URL for backend to call the local email service
export EMAIL_SERVICE_URL="http://localhost:4000"

# Start FastAPI backend on Render's provided PORT (default 10000 locally)
BACKEND_PORT="${PORT:-10000}"
echo "Starting FastAPI backend on port ${BACKEND_PORT}..."
python "$(dirname "$0")/main.py"

# Ensure background process is cleaned up on exit
trap "kill ${EMAIL_SERVICE_PID} 2>/dev/null || true" EXIT

#!/bin/bash
# Railway start script
# This script ensures the uploads directory exists before starting the server

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Start the FastAPI application
# Render requires binding to 0.0.0.0 and using PORT environment variable
uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}

