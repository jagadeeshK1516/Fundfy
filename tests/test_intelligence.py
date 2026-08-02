"""Test Intelligence Layer handlers."""

from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage

from fundfy.intelligence.market_research import MarketResearchHandler
from fundfy.intelligence.competitor_analysis import CompetitorAnalysisHandler
from fundfy.intelligence.idea_validation import IdeaValidationHandler
from fundfy.intelligence.financial_reasoning import FinancialReasoningHandler


@pytest.fixture
def mock_llm():
    """Create a mock LLM that returns structured analysis."""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="## Analysis\n\nDetailed findings here.")
    )
    return llm


@pytest.mark.asyncio
async def test_market_research_handler(mock_llm):
    """Market research handler returns structured output."""
    handler = MarketResearchHandler(llm=mock_llm)
    task = {"type": "market_research", "title": "SaaS Market Analysis", "params": {"industry": "SaaS"}}

    result = await handler.run(task)

    assert result.status == "completed"
    assert result.task_type == "market_research"
    assert "analysis" in result.result
    assert result.result["industry"] == "SaaS"
    mock_llm.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_competitor_analysis_handler(mock_llm):
    """Competitor analysis handler returns structured output."""
    handler = CompetitorAnalysisHandler(llm=mock_llm)
    task = {"type": "competitor_analysis", "title": "CRM Competitors", "params": {"market": "CRM"}}

    result = await handler.run(task)

    assert result.status == "completed"
    assert result.task_type == "competitor_analysis"
    assert "analysis" in result.result
    assert result.result["market"] == "CRM"


@pytest.mark.asyncio
async def test_idea_validation_handler(mock_llm):
    """Idea validation handler returns structured output."""
    handler = IdeaValidationHandler(llm=mock_llm)
    task = {"type": "idea_validation", "title": "Validate Idea", "params": {"idea": "AI-powered CRM"}}

    result = await handler.run(task)

    assert result.status == "completed"
    assert result.task_type == "idea_validation"
    assert "analysis" in result.result
    assert result.result["idea"] == "AI-powered CRM"


@pytest.mark.asyncio
async def test_financial_reasoning_handler(mock_llm):
    """Financial reasoning handler returns structured output."""
    handler = FinancialReasoningHandler(llm=mock_llm)
    task = {"type": "financial_reasoning", "title": "Unit Economics", "params": {"business": "SaaS CRM"}}

    result = await handler.run(task)

    assert result.status == "completed"
    assert result.task_type == "financial_reasoning"
    assert "analysis" in result.result
    assert result.result["business"] == "SaaS CRM"
