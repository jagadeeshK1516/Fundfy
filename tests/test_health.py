"""Test health endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from fundfy.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Health endpoint returns 200 with status healthy."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
