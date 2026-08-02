"""Integration test — end-to-end flow with mocked LLM."""

import json
import tempfile
from unittest.mock import AsyncMock

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
async def setup_integration():
    """Setup full integration dependencies with mocked LLM."""
    from fundfy.core.agent import FundfyAgent
    from fundfy.dependencies import init_dependencies
    from fundfy.documents.generator import DocumentGenerator
    from fundfy.memory.engine import MemoryEngine
    from fundfy.orchestrator.dispatcher import Dispatcher
    from fundfy.orchestrator.handlers.registry import create_handlers
    from fundfy.orchestrator.planner import ExecutionPlanner

    mock_llm = AsyncMock()

    # The LLM returns different responses based on call count
    call_count = {"n": 0}

    async def dynamic_response(messages):
        call_count["n"] += 1
        n = call_count["n"]
        if n == 1:
            # Chat response
            return AIMessage(content="Welcome! I can help you build your business.")
        elif n == 2:
            # Planner response
            return AIMessage(content=json.dumps([
                {"type": "market_research", "title": "Analyze market", "params": {"industry": "SaaS"}},
            ]))
        else:
            return AIMessage(content="Analysis complete: SaaS market is $150B.")

    mock_llm.ainvoke = AsyncMock(side_effect=dynamic_response)

    with tempfile.TemporaryDirectory() as tmpdir:
        memory_engine = MemoryEngine(embeddings=FakeEmbeddings(), persist_directory=tmpdir)
        agent = FundfyAgent(memory_engine=memory_engine, llm=mock_llm)
        planner = ExecutionPlanner(llm=mock_llm)
        handlers = create_handlers(llm=mock_llm, memory_engine=memory_engine)
        dispatcher = Dispatcher(handlers=handlers)
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

    # Clean up
    _businesses.clear()
    _documents.clear()


@pytest.mark.asyncio
async def test_full_flow(setup_integration):
    """End-to-end: create business, chat, trigger execution, verify workstream."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Create a business
        biz_response = await client.post("/api/business", json={
            "founder_id": "founder-1",
            "name": "AI CRM Startup",
            "industry": "SaaS",
            "stage": "seed",
        })
        assert biz_response.status_code == 200
        business_id = biz_response.json()["id"]

        # Step 2: Send a chat message
        chat_response = await client.post("/api/chat", json={
            "founder_id": "founder-1",
            "message": "Help me analyze the SaaS market",
        })
        assert chat_response.status_code == 200
        assert chat_response.json()["response"] != ""

        # Step 3: Trigger execution
        exec_response = await client.post("/api/execute", json={
            "business_id": business_id,
            "objective": "Validate my SaaS CRM idea",
            "context": "B2B focused",
        })
        assert exec_response.status_code == 200
        exec_data = exec_response.json()
        assert exec_data["status"] == "completed"
        assert len(exec_data["tasks"]) > 0

        # Step 4: Verify workstreams
        ws_response = await client.get(f"/api/workstreams/{business_id}")
        assert ws_response.status_code == 200
        workstreams = ws_response.json()
        assert len(workstreams) > 0
        assert workstreams[0]["type"] == "market_research"
