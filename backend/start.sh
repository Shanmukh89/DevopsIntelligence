#!/bin/bash
set -e

PORT="${PORT:-8000}"

# --- Celery background worker ---
# Use 'solo' pool (single-threaded, no prefork) to minimise memory on free-tier.
# Delay 5s so Uvicorn can bind the port before Celery saturates the CPU/memory.
(sleep 5 && celery -A celery_app worker \
    --pool=solo \
    --concurrency=1 \
    --loglevel=info \
    --without-heartbeat \
    --without-mingle) &
CELERY_PID=$!

# Clean up Celery on shutdown so Render gets a clean exit.
cleanup() {
    echo "Shutting down Celery worker (PID $CELERY_PID)..."
    kill "$CELERY_PID" 2>/dev/null || true
    wait "$CELERY_PID" 2>/dev/null || true
}
trap cleanup SIGTERM SIGINT EXIT

# --- FastAPI web service (foreground, PID 1 via exec) ---
# Render health-checks the port; Uvicorn must be the main process.
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
