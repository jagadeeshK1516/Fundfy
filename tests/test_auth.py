"""Test JWT authentication."""

import pytest
from httpx import ASGITransport, AsyncClient

from fundfy.auth.jwt import create_access_token, decode_access_token
from fundfy.main import app


@pytest.mark.asyncio
async def test_create_and_decode_token():
    """Token creation and decoding roundtrip."""
    token = create_access_token("founder-1", "founder")
    payload = decode_access_token(token)
    assert payload.founder_id == "founder-1"
    assert payload.role == "founder"


@pytest.mark.asyncio
async def test_decode_invalid_token():
    """Invalid token raises ValueError."""
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token("not-a-valid-token")


@pytest.mark.asyncio
async def test_register_and_login():
    """Registration and login flow works end-to-end."""
    from fundfy.db import init_db
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register
        reg_response = await client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        })
        assert reg_response.status_code == 200
        reg_data = reg_response.json()
        assert "access_token" in reg_data
        assert reg_data["founder_id"] != ""

        # Login
        login_response = await client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "securepassword123",
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data

        # Invalid login
        bad_response = await client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        assert bad_response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_registration():
    """Duplicate email registration returns 409."""
    from fundfy.db import init_db
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register first time
        await client.post("/api/auth/register", json={
            "name": "User A",
            "email": "dupe@example.com",
            "password": "password123",
        })

        # Register same email again
        response = await client.post("/api/auth/register", json={
            "name": "User B",
            "email": "dupe@example.com",
            "password": "password456",
        })
        assert response.status_code == 409


@pytest.mark.asyncio
async def test_refresh_token():
    """Token refresh returns a new valid token."""
    token = create_access_token("founder-1", "founder")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/refresh", json={
            "token": token,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["founder_id"] == "founder-1"
