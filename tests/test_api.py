"""Test REST API endpoints."""

import json
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import AIMessage

from fundfy.api.routes_business import _businesses
from fundfy.api.routes_documents import _documents
from fundfy.main import app


class FakeEmbeddings:
    """Deterministic fake embeddings for testing."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t) % 10) / 10.0] * 384 for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text) % 10) / 10.0] * 384


@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="This is a test response from the AI.")
    )
    return llm


@pytest.fixture
async def setup_deps(mock_llm):
    """Setup dependencies with mocked LLM."""
    from fundfy.core.agent import FundfyAgent
    from fundfy.dependencies import init_dependencies
    from fundfy.documents.generator import DocumentGenerator
    from fundfy.memory.engine import MemoryEngine
    from fundfy.orchestrator.dispatcher import Dispatcher
    from fundfy.orchestrator.planner import ExecutionPlanner

    with tempfile.TemporaryDirectory() as tmpdir:
        memory_engine = MemoryEngine(embeddings=FakeEmbeddings(), persist_directory=tmpdir)
        agent = FundfyAgent(memory_engine=memory_engine, llm=mock_llm)
        planner = ExecutionPlanner(llm=mock_llm)
        dispatcher = Dispatcher(handlers={})
        document_generator = DocumentGenerator(llm=mock_llm, memory_engine=memory_engine)

        init_dependencies(
            memory_engine=memory_engine,
            agent=agent,
            planner=planner,
            dispatcher=dispatcher,
            document_generator=document_generator,
            llm=mock_llm,
        )
        yield


@pytest.mark.asyncio
async def test_chat_endpoint(setup_deps):
    """Chat endpoint returns 200 with a response."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/chat", json={
            "founder_id": "founder-1",
            "message": "What market should I enter?"
        })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["founder_id"] == "founder-1"


@pytest.mark.asyncio
async def test_create_business(setup_deps):
    """Business creation endpoint returns 200."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/business", json={
            "founder_id": "founder-1",
            "name": "Test Startup",
            "industry": "SaaS",
            "stage": "seed",
        })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Startup"
    assert data["industry"] == "SaaS"
    assert "id" in data

    # Clean up
    _businesses.clear()


@pytest.mark.asyncio
async def test_document_list_empty(setup_deps):
    """Document listing returns empty list when no docs exist."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/documents", params={"business_id": "biz-1"})
    assert response.status_code == 200
    assert response.json() == []
