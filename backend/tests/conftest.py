"""
Test fixtures - using FastAPI TestClient for reliability.
"""
import pytest
import os
import tempfile
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.database import reset_engine, init_db, close_db

# Use temp file for SQLite
_temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
_temp_db.close()
DB_PATH = _temp_db.name

# Override settings BEFORE anything else
settings.DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
settings.DATABASE_URL_SYNC = f"sqlite:///{DB_PATH}"
settings.ENVIRONMENT = "test"


@pytest.fixture(scope="function")
def setup_database():
    """Create tables for each test."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    reset_engine()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    
    yield
    
    loop.run_until_complete(close_db())
    loop.close()
    
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except:
            pass


@pytest.fixture(scope="function")
def client(setup_database):
    """Create test client using FastAPI TestClient."""
    with TestClient(app) as c:
        yield c


def get_token(client):
    """Helper to get auth token."""
    # Register
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "Test@123"
    })
    
    # Login with OAuth2 form
    response = client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "Test@123"
    })
    
    return response.json()["access_token"]
