"""Tests for all agent tools."""

import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from fundfy.tools.schemas import ToolResult


class FakeEmbeddings:
    """Deterministic fake embeddings for testing."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t) % 10) / 10.0] * 384 for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text) % 10) / 10.0] * 384


# --- Web Search Tool Tests ---


@pytest.mark.asyncio
async def test_web_search_tool_success():
    """Web search returns results when API key is configured."""
    from fundfy.tools.web_search import WebSearchTool

    mock_results = {
        "results": [
            {"title": "Result 1", "url": "https://example.com/1", "content": "Content 1"},
            {"title": "Result 2", "url": "https://example.com/2", "content": "Content 2"},
        ]
    }

    with patch("tavily.TavilyClient") as MockClient:
        mock_client = MagicMock()
        mock_client.search.return_value = mock_results
        MockClient.return_value = mock_client

        tool = WebSearchTool(api_key="test-key")
        result = await tool.execute(query="AI startups", max_results=2)

    assert result.success is True
    assert len(result.data) == 2
    assert result.data[0]["title"] == "Result 1"


@pytest.mark.asyncio
async def test_web_search_tool_no_api_key():
    """Web search returns graceful error when no API key."""
    from fundfy.tools.web_search import WebSearchTool

    tool = WebSearchTool(api_key="")
    result = await tool.execute(query="test query")

    assert result.success is False
    assert "TAVILY_API_KEY" in result.error


@pytest.mark.asyncio
async def test_web_search_tool_api_error():
    """Web search handles API errors gracefully."""
    from fundfy.tools.web_search import WebSearchTool

    with patch("tavily.TavilyClient") as MockClient:
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("API rate limit")
        MockClient.return_value = mock_client

        tool = WebSearchTool(api_key="test-key")
        result = await tool.execute(query="test")

    assert result.success is False
    assert "rate limit" in result.error


# --- Web Scrape Tool Tests ---


@pytest.mark.asyncio
async def test_web_scrape_tool_success():
    """Web scrape extracts content from HTML."""
    from fundfy.tools.web_scrape import WebScrapeTool
    import httpx

    html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <script>alert('hi')</script>
            <main><p>Main content here.</p></main>
        </body>
    </html>
    """

    mock_response = httpx.Response(200, text=html, request=httpx.Request("GET", "https://example.com"))

    with patch("fundfy.tools.web_scrape.httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client_instance

        tool = WebScrapeTool()
        result = await tool.execute(url="https://example.com")

    assert result.success is True
    assert "Main content here" in result.data["content"]
    assert result.data["title"] == "Test Page"


@pytest.mark.asyncio
async def test_web_scrape_tool_error():
    """Web scrape handles connection errors."""
    from fundfy.tools.web_scrape import WebScrapeTool

    with patch("fundfy.tools.web_scrape.httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client_instance

        tool = WebScrapeTool()
        result = await tool.execute(url="https://unreachable.com")

    assert result.success is False
    assert "Connection refused" in result.error


# --- Memory Tools Tests ---


@pytest.mark.asyncio
async def test_memory_tools():
    """Memory tools save and query content."""
    from fundfy.memory.engine import MemoryEngine
    from fundfy.tools.memory_tools import QueryMemoryTool, SaveToMemoryTool

    with tempfile.TemporaryDirectory() as tmpdir:
        memory = MemoryEngine(embeddings=FakeEmbeddings(), persist_directory=tmpdir)

        # Test save
        save_tool = SaveToMemoryTool(memory_engine=memory)
        result = await save_tool.execute(content="The market size is $5B", metadata={"source": "research"})
        assert result.success is True
        assert result.data["content_length"] == len("The market size is $5B")

        # Test query
        query_tool = QueryMemoryTool(memory_engine=memory)
        result = await query_tool.execute(query="market size", k=3)
        assert result.success is True
        assert len(result.data) > 0
        assert "market size" in result.data[0]["content"].lower() or "$5B" in result.data[0]["content"]


# --- Document Tool Tests ---


@pytest.mark.asyncio
async def test_generate_document_tool():
    """Document tool generates and exports a file."""
    from fundfy.documents.generator import DocumentGenerator
    from fundfy.tools.document_tool import GenerateDocumentTool

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("fundfy.tools.exporters.settings") as mock_settings:
            mock_settings.generated_files_dir = tmpdir

            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="# Business Plan\n\nThis is the plan."))

            generator = DocumentGenerator(llm=mock_llm)
            tool = GenerateDocumentTool(document_generator=generator)

            result = await tool.execute(
                doc_type="business_plan",
                business_id="biz-1",
                content="## Executive Summary\n\nGreat business.",
                format="markdown",
            )

    assert result.success is True
    assert result.data["format"] == "markdown"
    assert result.data["file_name"].endswith(".md")


@pytest.mark.asyncio
async def test_generate_document_tool_invalid_format():
    """Document tool rejects invalid format."""
    from fundfy.documents.generator import DocumentGenerator
    from fundfy.tools.document_tool import GenerateDocumentTool

    generator = DocumentGenerator(llm=AsyncMock())
    tool = GenerateDocumentTool(document_generator=generator)

    result = await tool.execute(
        doc_type="business_plan",
        business_id="biz-1",
        content="test",
        format="html",
    )

    assert result.success is False
    assert "Unsupported format" in result.error


# --- Workstream Tools Tests ---


@pytest.mark.asyncio
async def test_workstream_tools():
    """Workstream tools create and update workstreams."""
    from fundfy.tools.workstream_tools import (
        CreateWorkstreamTool,
        UpdateWorkstreamTool,
        _tool_workstreams,
    )

    _tool_workstreams.clear()

    create_tool = CreateWorkstreamTool()
    result = await create_tool.execute(
        business_id="biz-1",
        title="Launch Plan",
        steps=["Research market", "Build MVP", "Launch"],
    )

    assert result.success is True
    ws_id = result.data["id"]
    assert result.data["title"] == "Launch Plan"
    assert len(result.data["steps"]) == 3

    # Update a step
    update_tool = UpdateWorkstreamTool()
    result = await update_tool.execute(
        workstream_id=ws_id,
        step_index=0,
        status="completed",
        result_summary="Found 5 competitors",
    )

    assert result.success is True
    assert result.data["steps"][0]["status"] == "completed"
    assert result.data["steps"][0]["result_summary"] == "Found 5 competitors"

    _tool_workstreams.clear()


@pytest.mark.asyncio
async def test_workstream_update_not_found():
    """Workstream update fails for non-existent workstream."""
    from fundfy.tools.workstream_tools import UpdateWorkstreamTool, _tool_workstreams

    _tool_workstreams.clear()

    tool = UpdateWorkstreamTool()
    result = await tool.execute(
        workstream_id="nonexistent",
        step_index=0,
        status="completed",
    )

    assert result.success is False
    assert "not found" in result.error


# --- Email Tool Tests ---


@pytest.mark.asyncio
async def test_draft_email_tool():
    """Email tool drafts an email via LLM."""
    from fundfy.tools.email_tool import DraftEmailTool, _email_drafts

    _email_drafts.clear()

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="Subject: Partnership Opportunity\n\nDear Investor, we are building...")
    )

    tool = DraftEmailTool(llm=mock_llm)
    result = await tool.execute(
        email_type="investor_outreach",
        recipient_context="VC partner at Sequoia focusing on SaaS",
        business_context="AI-powered CRM, $1M ARR",
    )

    assert result.success is True
    assert result.data["subject"] == "Partnership Opportunity"
    assert "Investor" in result.data["body"]
    assert result.data["email_type"] == "investor_outreach"

    _email_drafts.clear()


@pytest.mark.asyncio
async def test_draft_email_tool_invalid_type():
    """Email tool rejects invalid email types."""
    from fundfy.tools.email_tool import DraftEmailTool

    mock_llm = AsyncMock()
    tool = DraftEmailTool(llm=mock_llm)
    result = await tool.execute(
        email_type="spam",
        recipient_context="test",
        business_context="test",
    )

    assert result.success is False
    assert "Unknown email type" in result.error


# --- Financial Tool Tests ---


@pytest.mark.asyncio
async def test_analyze_financials_tool():
    """Financial tool performs analysis via LLM."""
    from fundfy.tools.financial_tool import AnalyzeFinancialsTool

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="Unit economics: CAC=$50, LTV=$500, LTV/CAC=10x")
    )

    tool = AnalyzeFinancialsTool(llm=mock_llm)
    result = await tool.execute(
        business_context="AI CRM with 100 customers at $50/mo",
        analysis_type="unit_economics",
    )

    assert result.success is True
    assert "CAC" in result.data["analysis"]
    assert result.data["analysis_type"] == "unit_economics"


# --- Research Tools Tests ---


@pytest.mark.asyncio
async def test_search_grants_tool():
    """Search grants tool combines web search + LLM extraction."""
    from fundfy.tools.research_tools import SearchGrantsTool
    from fundfy.tools.web_search import WebSearchTool

    mock_web_search = AsyncMock(spec=WebSearchTool)
    mock_web_search.execute = AsyncMock(return_value=ToolResult(
        success=True,
        data=[
            {"title": "SBIR Grant", "url": "https://sbir.gov", "content": "Small business innovation research grant up to $250K"},
        ],
    ))

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content='[{"name": "SBIR", "organization": "NSF", "amount": "$250K", "deadline": "March 2024", "eligibility": "US small businesses", "url": "https://sbir.gov", "description": "Innovation research"}]')
    )

    tool = SearchGrantsTool(llm=mock_llm, web_search_tool=mock_web_search)
    result = await tool.execute(query="AI technology", industry="SaaS")

    assert result.success is True
    assert len(result.data) == 1
    assert result.data[0]["name"] == "SBIR"


@pytest.mark.asyncio
async def test_search_investors_tool():
    """Search investors tool combines web search + LLM extraction."""
    from fundfy.tools.research_tools import SearchInvestorsTool
    from fundfy.tools.web_search import WebSearchTool

    mock_web_search = AsyncMock(spec=WebSearchTool)
    mock_web_search.execute = AsyncMock(return_value=ToolResult(
        success=True,
        data=[
            {"title": "Sequoia Capital", "url": "https://sequoia.com", "content": "Leading VC firm investing in seed to growth stage startups"},
        ],
    ))

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content='[{"name": "Sequoia Capital", "firm": "Sequoia", "focus_areas": ["SaaS", "AI"], "stage_preference": "seed to growth", "typical_check_size": "$500K-$5M", "website": "https://sequoia.com"}]')
    )

    tool = SearchInvestorsTool(llm=mock_llm, web_search_tool=mock_web_search)
    result = await tool.execute(query="SaaS investors", stage="seed", industry="AI")

    assert result.success is True
    assert len(result.data) == 1
    assert result.data[0]["name"] == "Sequoia Capital"


# --- Tool Base Class Tests ---


def test_tool_to_openai_function():
    """BaseTool generates correct OpenAI function schema."""
    from fundfy.tools.web_search import WebSearchTool

    tool = WebSearchTool(api_key="test")
    schema = tool.to_openai_function()

    assert schema["name"] == "web_search"
    assert "query" in schema["parameters"]["properties"]
    assert "description" in schema
