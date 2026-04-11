"""Pytest fixtures for backend tests."""

from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from pgvector.sqlalchemy import Vector
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from config import clear_settings_cache
from database import Base
import models  # noqa: F401 — register ORM metadata
from models.teams import Team


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_type, compiler, **kw):
    return "TEXT"


@compiles(Vector, "sqlite")
def _compile_vector_sqlite(_type, compiler, **kw):
    return "BLOB"


@pytest.fixture(autouse=True)
def _test_env():
    os.environ.setdefault("ENVIRONMENT", "test")
    clear_settings_cache()
    yield
    clear_settings_cache()


@pytest_asyncio.fixture
async def async_engine():
    """In-memory SQLite shared across connections for FK support."""
    url = "sqlite+aiosqlite://"
    engine = create_async_engine(
        url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncSession:
    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def sample_team(db_session: AsyncSession) -> Team:
    team = Team(name="test-team")
    db_session.add(team)
    await db_session.flush()
    return team


@pytest.fixture
def random_repo_id() -> uuid.UUID:
    return uuid.uuid4()
