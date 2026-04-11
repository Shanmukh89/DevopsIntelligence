"""Auditr FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from auth_core import JWTAuthMiddleware
from config import get_settings
from database import Base, engine
from logging_config import setup_logging
from middleware.http import RequestLoggingMiddleware
import models  # noqa: F401 — register ORM mappers
from routers import auth, integrations, repositories, webhooks

logger = logging.getLogger(__name__)


async def _init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup; log lifecycle."""
    settings = get_settings()
    await _init_db()
    logger.info(
        "startup_complete",
        extra={"environment": settings.environment, "action_taken": "app_ready"},
    )
    yield
    logger.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings)

    app = FastAPI(
        title="Auditr API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(JWTAuthMiddleware)

    app.include_router(auth.router)
    app.include_router(integrations.router)
    app.include_router(repositories.router)
    app.include_router(webhooks.router)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        body = getattr(exc, "body", None)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), **({"body": body} if body is not None else {})},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "unhandled_error",
            extra={"path": request.url.path, "action_taken": "error_alert"},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/health")
    async def api_health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
