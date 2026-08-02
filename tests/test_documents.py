"""Test Document Generation Engine."""

from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage

from fundfy.documents.generator import DocumentGenerator
from fundfy.documents.handlers import DocumentGenerationHandler


@pytest.mark.asyncio
async def test_document_generator_creates_business_plan():
    """DocumentGenerator creates a business plan with correct structure."""
    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="# Business Plan\n\n## Executive Summary\nThis is a comprehensive plan...")
    )

    generator = DocumentGenerator(llm=mock_llm)
    doc = await generator.generate("business_plan", "biz-1", "A B2B SaaS startup in fintech")

    assert doc["doc_type"] == "business_plan"
    assert doc["title"] == "Business Plan"
    assert doc["content"] != ""
    assert doc["business_id"] == "biz-1"
    mock_llm.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_document_generator_unknown_type():
    """DocumentGenerator raises ValueError for unknown doc type."""
    mock_llm = AsyncMock()
    generator = DocumentGenerator(llm=mock_llm)

    with pytest.raises(ValueError, match="Unknown document type"):
        await generator.generate("unknown_type", "biz-1")


@pytest.mark.asyncio
async def test_document_generation_handler():
    """DocumentGenerationHandler delegates to generator and returns result."""
    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="# PRD\n\n## Product Overview\nDetailed PRD content...")
    )

    handler = DocumentGenerationHandler(llm=mock_llm)
    task = {
        "type": "document_generation",
        "title": "Generate PRD",
        "params": {"doc_type": "prd", "business_id": "biz-2", "context": "AI platform"},
    }

    result = await handler.run(task)

    assert result.status == "completed"
    assert result.result["doc_type"] == "prd"
    assert result.result["content"] != ""
