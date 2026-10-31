from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# Engine setup with pre-ping to ensure connections are healthy before use
engine = create_engine(
    settings.get_database_url(),
    pool_pre_ping=True,
    echo=False,  # Set to True for verbose SQL logs during debugging
)

# Session factory for generating database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session and guarantees closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
