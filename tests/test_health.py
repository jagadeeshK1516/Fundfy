"""Test health and readiness endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from fundfy.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Health endpoint returns 200 with component statuses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]
    assert "chromadb" in data["components"]


@pytest.mark.asyncio
async def test_readiness_endpoint():
    """Readiness endpoint returns 200 when DB is healthy."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
