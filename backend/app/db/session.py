import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, NullPool

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Determine if we're using SQLite (for local fallback) or PostgreSQL
is_sqlite = settings.get_database_url.startswith("sqlite")

if is_sqlite:
    # SQLite does not support connection pooling the same way PostgreSQL does
    engine = create_engine(
        settings.get_database_url,
        connect_args={"check_same_thread": False},
        poolclass=NullPool
    )
else:
    engine = create_engine(
        settings.get_database_url,
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
