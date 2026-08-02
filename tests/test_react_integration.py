"""Integration test — end-to-end ReAct agent path through the API."""

import json
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import AIMessage

from fundfy.main import app


class FakeEmbeddings:
    """Deterministic fake embeddings for testing."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t) % 10) / 10.0] * 384 for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text) % 10) / 10.0] * 384


@pytest.fixture
async def setup_react_integration():
    """Setup integration deps with mocked LLM that triggers TOOL_USE path."""
    from fundfy.core.agent import FundfyAgent
    from fundfy.dependencies import init_dependencies
    from fundfy.documents.generator import DocumentGenerator
    from fundfy.memory.engine import MemoryEngine
    from fundfy.orchestrator.dispatcher import Dispatcher
    from fundfy.orchestrator.handlers.registry import create_handlers
    from fundfy.orchestrator.planner import ExecutionPlanner
    from fundfy.tools.registry import create_tool_registry

    call_count = {"n": 0}

    async def dynamic_response(messages, **kwargs):
        call_count["n"] += 1
        n = call_count["n"]
        if n == 1:
            # Classifier: route to TOOL_USE
            return AIMessage(content="TOOL_USE")
        else:
            # Final answer from ReAct agent (no function call)
            return AIMessage(content="Based on my research, the CRM market is worth $50B with key players Salesforce, HubSpot, and Zoho.")

    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(side_effect=dynamic_response)
    # When bind is called (for function schemas), return itself so ainvoke works
    mock_llm.bind = MagicMock(return_value=mock_llm)

    with tempfile.TemporaryDirectory() as tmpdir:
        memory_engine = MemoryEngine(embeddings=FakeEmbeddings(), persist_directory=tmpdir)
        document_generator = DocumentGenerator(llm=mock_llm, memory_engine=memory_engine)

        # Create tool registry with mocked web search
        with patch("fundfy.tools.web_search.settings") as mock_settings:
            mock_settings.tavily_api_key = ""  # No Tavily key, tools will gracefully degrade

            tool_registry = create_tool_registry(
                llm=mock_llm,
                memory_engine=memory_engine,
                document_generator=document_generator,
            )

        agent = FundfyAgent(memory_engine=memory_engine, llm=mock_llm, tools=tool_registry)
        planner = ExecutionPlanner(llm=mock_llm)
        handlers = create_handlers(llm=mock_llm, memory_engine=memory_engine)
        dispatcher = Dispatcher(handlers=handlers)

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
async def test_react_chat_endpoint(setup_react_integration):
    """Chat endpoint uses ReAct path when classifier returns TOOL_USE."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/chat", json={
            "founder_id": "founder-1",
            "message": "Research my competitors in the CRM space",
        })

    assert response.status_code == 200
    data = response.json()
    assert data["response"] != ""
    assert "CRM" in data["response"] or "research" in data["response"].lower()
    assert data["founder_id"] == "founder-1"


@pytest.fixture
async def setup_react_with_tools():
    """Setup integration with mock LLM that actually calls tools."""
    from fundfy.core.agent import FundfyAgent
    from fundfy.dependencies import init_dependencies
    from fundfy.documents.generator import DocumentGenerator
    from fundfy.memory.engine import MemoryEngine
    from fundfy.orchestrator.dispatcher import Dispatcher
    from fundfy.orchestrator.planner import ExecutionPlanner

    call_count = {"n": 0}

    def make_function_call_response(name, arguments):
        return AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "name": name,
                    "arguments": json.dumps(arguments),
                }
            },
        )

    async def dynamic_response(messages, **kwargs):
        call_count["n"] += 1
        n = call_count["n"]
        if n == 1:
            # Classifier: route to TOOL_USE
            return AIMessage(content="TOOL_USE")
        elif n == 2:
            # ReAct: first call web_search
            return make_function_call_response("web_search", {"query": "CRM competitors"})
        else:
            # ReAct: final answer
            return AIMessage(content="Based on my research, the CRM market has key players including Salesforce and HubSpot.")

    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(side_effect=dynamic_response)
    mock_llm.bind = MagicMock(return_value=mock_llm)

    with tempfile.TemporaryDirectory() as tmpdir:
        memory_engine = MemoryEngine(embeddings=FakeEmbeddings(), persist_directory=tmpdir)
        document_generator = DocumentGenerator(llm=mock_llm, memory_engine=memory_engine)

        # Mock the Tavily client
        with patch("tavily.TavilyClient") as MockTavily:
            mock_tavily_client = MagicMock()
            mock_tavily_client.search.return_value = {
                "results": [
                    {"title": "CRM Market Report", "url": "https://example.com", "content": "Salesforce leads with 23% market share."},
                ]
            }
            MockTavily.return_value = mock_tavily_client

            from fundfy.tools.registry import create_tool_registry
            with patch("fundfy.tools.web_search.settings") as mock_settings:
                mock_settings.tavily_api_key = "test-key"
                tool_registry = create_tool_registry(
                    llm=mock_llm,
                    memory_engine=memory_engine,
                    document_generator=document_generator,
                )

        agent = FundfyAgent(memory_engine=memory_engine, llm=mock_llm, tools=tool_registry)
        planner = ExecutionPlanner(llm=mock_llm)
        dispatcher = Dispatcher(handlers={})

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
async def test_react_with_tool_calls(setup_react_with_tools):
    """Full integration: chat triggers tool use, results include tool_calls and checkpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/chat", json={
            "founder_id": "founder-1",
            "message": "Research my competitors in the CRM space",
        })

    assert response.status_code == 200
    data = response.json()
    assert data["response"] != ""
    assert data["tool_calls"] is not None
    assert len(data["tool_calls"]) >= 1
    assert data["tool_calls"][0]["tool"] == "web_search"
    assert data["checkpoints"] is not None
    assert len(data["checkpoints"]) >= 1
    assert data["steps"] is not None
    assert data["steps"] >= 2


@pytest.mark.asyncio
async def test_file_download_endpoint():
    """File download endpoint serves generated files."""
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        test_file = os.path.join(tmpdir, "test-doc.md")
        with open(test_file, "w") as f:
            f.write("# Test Document\n\nContent here.")

        with patch("fundfy.api.routes_files.settings") as mock_settings:
            mock_settings.generated_files_dir = tmpdir

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Download by full filename
                response = await client.get("/api/files/test-doc.md")
                assert response.status_code == 200
                assert "Test Document" in response.text

                # Download by stem (without extension)
                response = await client.get("/api/files/test-doc")
                assert response.status_code == 200

                # List files
                response = await client.get("/api/files")
                assert response.status_code == 200
                files = response.json()
                assert len(files) == 1
                assert files[0]["file_name"] == "test-doc.md"

                # 404 for non-existent file
                response = await client.get("/api/files/nonexistent")
                assert response.status_code == 404
