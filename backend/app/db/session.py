import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, NullPool

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Determine if we're using SQLite (for isolated test fallback) or PostgreSQL
db_url = settings.get_database_url
is_sqlite = db_url.startswith("sqlite")

if is_sqlite:
    # SQLite configuration for tests
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
else:
    engine = create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connected() -> tuple[bool, str]:
    """Check database connectivity without exposing secrets."""
    from sqlalchemy import text
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "connected"
    except Exception as e:
        logger.error("Database health check failed", extra={"error": str(e)})
        return False, "disconnected"

