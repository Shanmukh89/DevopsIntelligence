#!/bin/bash

# Start the Celery background worker as a background process (&)
celery -A celery_app worker --loglevel=info &

# Start the FastAPI web service in the foreground
uvicorn app.main:app --host 0.0.0.0 --port 8000
