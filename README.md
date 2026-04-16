# Auditr 

An AI-powered DevOps intelligence platform that deeply understands your repositories.

Auditr is a full-stack application that connects to your GitHub repositories, builds an intelligent code review graph, and serves as an AI-powered engineering assistant. It is designed for developers and engineering teams who need instant codebase Q&A, automated pull request reviews, code clone detection, and cloud cost estimations.

## Live Demo

[View Live Application](https://devops-intelligence.vercel.app/) 

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
│   └── .env                   # Local backend secrets
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js App Router (Dashboard, Auth, QA)
│   │   ├── components/        # Reusable UI primitives and layouts
│   │   └── lib/               # Supabase clients and utility functions
│   ├── package.json           # Frontend dependencies
│   └── .env.local             # Local frontend secrets
├── docs/                      # PRD and Design Requirement documents
└── supabase_schema.sql        # Unified PostgreSQL schema and RLS policies
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

## Running the Application Locally

Since infrastructure components are handled via cloud providers, you can run the core components directly on your system without Docker.

**1. Start Backend (Python):**
To launch the FastAPI service handling AI generation and routing:
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\activate
# On Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**2. Start Celery Worker (Background Thread):**
If you need to process AI queues locally, run this in a second terminal inside the backend folder:
```bash
cd backend
# Activate virtual environment again
celery -A celery_app worker
```

**3. Start Frontend (Next.js):**
In a third terminal window:
```bash
cd frontend
npm install
npm run dev
```

The frontend will be accessible at http://localhost:3000, connecting locally to your Python backend running at http://localhost:8000.

## Deployment

This project can be deployed entirely for **$0/month** by decoupling the services across generous free tiers:

**1. Database & Cache:**
- **PostgreSQL**: Create a free project on [Supabase](https://supabase.com) (Includes `pgvector` natively).
- **Redis**: Create a free Serverless Redis instance on [Upstash](https://upstash.com) (10k requests/day).

**2. Frontend:**
- Deploy the `frontend/` directory to **Vercel** (100% Free). 
- **Important**: Set `NEXT_PUBLIC_API_URL` to point to your live backend URL in Vercel's Environment Variables.

**3. Backend & Background Worker:**
- Deploy the `backend/` directory to **Fly.io** or **Koyeb** (Generous free tiers).
- You will need to spin up two separate processes:
  1. Web Service: `uvicorn app.main:app`
  2. Celery Worker: `celery -A celery_app worker`
- Feed the `DATABASE_URL` (from Supabase) and `REDIS_URL` (from Upstash) into their environment variables.

*(Note: ClickHouse and Jaeger tracing are excluded in this free-tier deployment strategy to eliminate costs).*

### Updating the GitHub App (No more ngrok!)
When testing locally, you had to use `ngrok` to expose your local PC to GitHub. In production, you **no longer need ngrok**. 

Once your backend is deployed live, go to your GitHub App Settings at `github.com` and update your **Webhook URL** to point to your live backend domain:
`https://<your-live-backend-url>/api/github/webhook`
