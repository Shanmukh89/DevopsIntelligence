import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Ensure backend package root is on sys.path when running `python -m alembic` from /backend
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from config import get_settings  # noqa: E402
from database import Base  # noqa: E402

import models  # noqa: F401, E402 — register metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

_settings = get_settings()
_db_url = _settings.database_url
if _db_url.startswith("postgresql+asyncpg://"):
    _sync_url = _db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
elif _db_url.startswith("sqlite+aiosqlite://"):
    _sync_url = _db_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
else:
    _sync_url = _db_url

config.set_main_option("sqlalchemy.url", _sync_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
