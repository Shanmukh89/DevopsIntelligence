# Auditr (DevopsIntelligence)

An AI-powered DevOps intelligence platform that deeply understands your repositories.

Auditr is a full-stack application that connects to your GitHub repositories, builds an intelligent code review graph, and serves as an AI-powered engineering assistant. It is designed for developers and engineering teams who need instant codebase Q&A, automated pull request reviews, code clone detection, and cloud cost estimations.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [System Architecture](#system-architecture)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [Deployment](#deployment)

## Features

**One-Click GitHub Integration**
Install the GitHub App from the dashboard, and the system automatically ingests your repositories, syncs pull requests, and sets up webhook listeners for live updates. No manual data pulling required.

**RAG-Powered Codebase Q&A**
User queries are embedded using OpenAI's models and matched against the knowledge graph via pgvector cosine similarity. Ask questions like "Where is the authentication handled?" and get source-grounded responses in a persistent, interactive chat interface.

**Advanced Code Clone Detection**
Utilizes AST (Abstract Syntax Tree) parsing and vector embeddings alongside Trafilatura to detect semantic code clones across massive codebases, highlighting opportunities for refactoring.

**Cloud Cost Estimations**
Analyzes infrastructure configurations to provide AWS cost estimations and anomaly detection, helping teams proactively manage their cloud spend directly from the dashboard.

**Multi-Repo Knowledge Graph**
Each repository operates in an isolated graph structure inside PostgreSQL. Knowledge chunks are tagged, allowing users to ask questions across "All Repositories" or dive deep into a specific selected repository without cross-contamination.

**Background Job Queue**
Heavy operations like repository ingestion, embedding generation, and background syncs are offloaded to a Celery worker backed by Redis. The frontend reacts dynamically to sync statuses.

**Authentication and User Profiles**
Supabase Auth handles secure user registration (Google, GitHub, Email), login, and session management. Row Level Security (RLS) policies ensure that users only access their own synced repositories and intelligence data.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React 19, Tailwind CSS 4 |
| UI Components | Lucide React, Shadcn (customized) |
| Backend API | Python 3.10, FastAPI, Uvicorn |
| Job Queue | Celery with Redis |
| Database | Supabase (PostgreSQL + pgvector) |
| Search & Logs | ClickHouse |
| Distributed Tracing | Jaeger |
| Embeddings / LLM | OpenAI & Anthropic Integrations |
| Authentication | Supabase Auth with Row Level Security |

## Project Structure

```
DevopsIntelligence/
├── backend/
│   ├── app/                   # FastAPI application core
│   │   ├── main.py            # API entry point
│   │   ├── models/            # SQLAlchemy / Pydantic models
│   │   └── services/          # Business logic (Slack, AI, Cloud Costs)
│   ├── celery_app.py          # Celery worker definitions
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Backend container configuration
│   └── .env                   # Local backend secrets
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js App Router (Dashboard, Auth, QA)
│   │   ├── components/        # Reusable UI primitives and layouts
│   │   └── lib/               # Supabase clients and utility functions
│   ├── package.json           # Frontend dependencies
│   ├── Dockerfile             # Frontend container configuration
│   └── .env.local             # Local frontend secrets
├── docs/                      # PRD and Design Requirement documents
├── docker-compose.yml         # Full infrastructure stack orchestration
├── supabase_schema.sql        # Unified PostgreSQL schema and RLS policies
└── .env                       # Root environment variables for Docker Compose
```

## System Architecture

```text
User opens Dashboard
        |
        v
  ┌─────────────┐       ┌───────────────┐       ┌──────────────────┐
  │  Frontend    │──────>│  FastAPI      │──────>│  Celery Queue    │
  │  (Next.js)   │  POST │  /api/routes  │  add  │  (Redis)         │
  └─────────────┘       │               │       └────────┬─────────┘
                        └───────────────┘                │
                                                         v
                                              ┌──────────────────┐
                                              │  Celery Worker   │
                                              │  (celery_app.py) │
                                              └────────┬─────────┘
                                                       │
                                          Process Repos / Run LLMs
                                                       │
                                                       v
                                              ┌──────────────────┐
                                              │  Supabase        │
                                              │  (PostgreSQL +   │
                                              │   pgvector)      │
                                              └──────────────────┘
                                                       ^
                                                       │
                                            Semantic Vector Search
                                                       │
  ┌─────────────┐       ┌───────────────┐       ┌──────┴───────────┐
  │  Frontend    │<──────│  FastAPI      │<──────│  AI Services    │
  │  Chat UI     │  SSE  │  /code-qa     │  RAG  │  (OpenAI models)│
  └─────────────┘       └───────────────┘       └──────────────────┘
```

## Getting Started

### Prerequisites

| Requirement | Details |
|---|---|
| Node.js | Version 20 or higher |
| Python | Version 3.10 or higher |
| Docker | Docker Desktop required to run the full stack |
| Supabase | A project with the pgvector extension enabled |
| OpenAI API Key | Access to embedding and generation models |

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/your-username/DevopsIntelligence.git
cd DevopsIntelligence
```

2. **Configure the databases**
Run `supabase_schema.sql` in your Supabase SQL Editor. This will create all the required tables (profiles, repositories, github_installations, etc.) and Row Level Security (RLS) policies.

3. **Create root environment variables**
Ensure you have a `.env` file at the root of the project to feed credentials to Docker.

## Environment Variables

### Root (`.env`)

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Required | OpenAI API key for embeddings and chat generation |
| `ANTHROPIC_API_KEY` | Optional | Anthropic fallback key |
| `GITHUB_APP_PRIVATE_KEY`| Required | Private `.pem` key contents for GitHub App integration |
| `SLACK_BOT_TOKEN` | Optional | Token for Slack alert routing |

## Running the Application

The fastest and most consistent way to run the entire Auditr stack (Frontend, Backend, Postgres, Redis, ClickHouse, and Jaeger) is via Docker Compose.

**Run Everything:**
```bash
docker-compose up --build
```
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Jaeger Tracing**: http://localhost:16686

### Alternative: Local Development Mode (Hot-Reload)
If you prefer running the servers natively to get instant code hot-reloading:

1. **Start Background Infrastructure (Docker):**
```bash
docker-compose up -d postgres redis clickhouse
```

2. **Start Backend (Python):**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. **Start Frontend (Next.js):**
```bash
cd frontend
npm install
npm run dev
```

## Deployment

**Frontend:** Deploy the `frontend/` directory to Vercel or Netlify. Make sure to define the `NEXT_PUBLIC_API_URL` environment variable to point to your live backend.

**Backend & Workers:** Deploy the `backend/` directory to Render, Railway, or AWS ECS. You will need two separate processes running:
1. Web Service running `uvicorn app.main:app`
2. Background Worker running `celery -A celery_app worker`

**Databases:** Use hosted Supabase for PostgreSQL/Auth. Use Upstash or a similar managed provider for Redis, and a managed service or dedicated container deployment for ClickHouse.
