"""
Auditr — Automated DevOps Intelligence Platform
FastAPI Backend Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import webhooks, features
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Automated DevOps Intelligence Platform",
    version=settings.VERSION,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://devops-intelligence.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(webhooks.router)
app.include_router(features.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "auditr-api"}
