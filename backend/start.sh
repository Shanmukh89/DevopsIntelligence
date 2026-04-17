#!/bin/bash

# Start the Celery background worker as a background process (&)
celery -A celery_app worker --loglevel=info &

# Start the FastAPI web service in the foreground (Render passes $PORT dynamically)
PORT="${PORT:-8000}"
uvicorn app.main:app --host 0.0.0.0 --port $PORT
