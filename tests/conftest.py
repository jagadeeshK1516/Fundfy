"""Shared test fixtures and configuration."""

import os

# Set test environment before any imports
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_fundfy.db"
os.environ["REDIS_URL"] = ""
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-32bytes!"
os.environ["BACKGROUND_JOBS_ENABLED"] = "false"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["OPENAI_API_KEY"] = "sk-test"

import pytest

from fundfy.auth.jwt import create_access_token


def auth_headers(founder_id: str = "test-founder-1", role: str = "founder") -> dict[str, str]:
    """Generate Authorization headers with a valid test JWT token."""
    token = create_access_token(founder_id, role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_auth_headers():
    """Fixture providing auth headers for test requests."""
    return auth_headers()


@pytest.fixture
def test_founder_id():
    """Fixture providing a test founder ID."""
    return "test-founder-1"


@pytest.fixture(autouse=True)
async def _reset_db():
    """Reset the database before each test that uses auth/DB."""
    from fundfy.db import engine
    from fundfy.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
