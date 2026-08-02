"""Test Business Memory Engine."""

import tempfile
from unittest.mock import patch

import pytest

from fundfy.memory.engine import MemoryEngine


class FakeEmbeddings:
    """Deterministic fake embeddings for testing."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return deterministic embeddings based on text length."""
        return [[float(len(t) % 10) / 10.0] * 384 for t in texts]

    def embed_query(self, text: str) -> list[float]:
        """Return deterministic embedding for a query."""
        return [float(len(text) % 10) / 10.0] * 384


@pytest.mark.asyncio
async def test_ingest_and_query():
    """Ingest 3 texts and query to find the relevant one."""
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = MemoryEngine(embeddings=FakeEmbeddings(), persist_directory=tmpdir)

        engine.ingest("The SaaS market is growing at 20% annually.", {"source_type": "research"})
        engine.ingest("Our competitor Acme Corp has 50 enterprise clients.", {"source_type": "competitor"})
        engine.ingest("Revenue projections show $2M ARR by Q4.", {"source_type": "financial"})

        results = engine.query("What is the market growth rate?", k=3)

        assert len(results) > 0
        # All results should be Document objects with page_content
        assert all(hasattr(r, "page_content") for r in results)


@pytest.mark.asyncio
async def test_ingest_document():
    """Ingest a document by ID and verify metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = MemoryEngine(embeddings=FakeEmbeddings(), persist_directory=tmpdir)

        ids = engine.ingest_document("doc-123", "Business plan content here.", {"business_id": "biz-1"})

        assert len(ids) > 0

        results = engine.query("business plan", k=1)
        assert len(results) > 0
        assert results[0].metadata.get("doc_id") == "doc-123"
