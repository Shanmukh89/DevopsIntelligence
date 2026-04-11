# Auditr

Monorepo for the Auditr platform: FastAPI backend, Next.js frontend, Celery workers, realtime (Socket.IO), and supporting infrastructure.

## Repository layout

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI application |
| `frontend/` | Next.js (App Router) |
| `services/celery/` | Celery worker image (uses `backend/app`) |
| `services/realtime/` | Socket.IO server (`/ws` path) |
| `services/embeddings/` | Placeholder for embedding / batch jobs |
| `infrastructure/nginx/` | Nginx reverse proxy image (TLS dev certs baked in) |
| `scripts/` | Setup helpers, migrations, seeds |

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- (Optional) Node.js 22+ and Python 3.12+ for local development outside Docker

## Quick start (Docker)

1. Copy environment template and adjust secrets:

   ```bash
   cp .env.example .env
   ```

2. Start the stack:

   ```bash
   docker compose up --build
   ```

3. Endpoints (via Nginx on **80** / **443** with self-signed cert):

   - App UI: `http://localhost/` (proxied to Next.js on 3000)
   - API: `http://localhost/api/` (proxied to FastAPI on 8000), e.g. `http://localhost/api/health`
   - Socket.IO: `http://localhost/ws` (proxied to realtime on 3001)

Direct ports (bypassing Nginx):

- Next.js: `http://localhost:3000`
- FastAPI: `http://localhost:8000` (e.g. `/api/health`, `/health`)
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- ClickHouse HTTP: `localhost:8123`

## Services in `docker-compose.yml`

- **postgres** — PostgreSQL 15
- **redis** — Redis 7
- **clickhouse** — ClickHouse 24
- **backend** — FastAPI
- **frontend** — Next.js dev server (`Dockerfile.dev`, source bind-mounted)
- **realtime** — Socket.IO on port 3001, path `/ws`
- **celery** — Celery worker
- **nginx** — Routes `/api/*` → backend, `/ws` → realtime, `/*` → frontend; CORS for localhost origins

## Scripts

- `scripts/setup.ps1` / `scripts/setup.sh` — install frontend deps (and optional venv for backend)
- `scripts/migrate.sh` — placeholder for Alembic / DB migrations
- `scripts/seed.sh` — placeholder for seed data

## Development without Docker

Use `scripts/setup` to install dependencies, run Postgres/Redis/ClickHouse via Docker only, and start `uvicorn` / `npm run dev` locally. Align `DATABASE_URL` and `REDIS_URL` in `.env` with your local services.

## License

Proprietary / TBD.
