#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "Installing frontend dependencies..."
(cd frontend && npm install)

echo "Installing realtime service dependencies..."
(cd services/realtime && npm install)

if command -v python3 >/dev/null 2>&1; then
  echo "Creating Python venv and installing backend deps..."
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install -r backend/requirements.txt
fi

echo "Done. Copy .env.example to .env if you have not already."
