import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session():
    """Database session fixture that automatically rolls back after each test."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
