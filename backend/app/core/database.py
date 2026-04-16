from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# If no DB URL is provided, fallback to sqlite for local dev without a DB
SQLALCHEMY_DATABASE_URL = settings.SUPABASE_DB_URL or "sqlite:///./devops_intelligence.db"

# Supabase Postgres usually requires specific connect_args depending on pgBouncer etc.
# But standard PostgreSQL works directly.
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # Use standard postgresql driver for Supabase
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
