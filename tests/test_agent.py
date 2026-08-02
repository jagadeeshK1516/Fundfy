"""Test Core AI Agent."""

import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage

from fundfy.core.agent import FundfyAgent
from fundfy.memory.engine import MemoryEngine


class FakeEmbeddings:
    """Deterministic fake embeddings for testing."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t) % 10) / 10.0] * 384 for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text) % 10) / 10.0] * 384


@pytest.mark.asyncio
async def test_agent_chat_returns_response():
    """Agent returns a response string incorporating retrieved context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = MemoryEngine(embeddings=FakeEmbeddings(), persist_directory=tmpdir)
        memory.ingest("The TAM for our market is $5B.", {"source_type": "research"})

        # Mock LLM
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AIMessage(content="Based on the $5B TAM, here's my recommendation...")
        )

        agent = FundfyAgent(memory_engine=memory, llm=mock_llm)
        response = await agent.chat("founder-1", "What is our market size?")

        assert response == "Based on the $5B TAM, here's my recommendation..."
        mock_llm.ainvoke.assert_called_once()

        # Verify the prompt includes context
        call_args = mock_llm.ainvoke.call_args[0][0]
        # Should have system message and human message
        assert len(call_args) == 2
        # The human message should contain context from memory
        assert "TAM" in call_args[1].content or "$5B" in call_args[1].content


@pytest.mark.asyncio
async def test_agent_persists_conversation_history():
    """Agent stores conversation history for the founder."""
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = MemoryEngine(embeddings=FakeEmbeddings(), persist_directory=tmpdir)

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AIMessage(content="Hello, founder!")
        )

        agent = FundfyAgent(memory_engine=memory, llm=mock_llm)
        await agent.chat("founder-1", "Hello")

        assert len(agent._conversation_history["founder-1"]) == 2
        assert agent._conversation_history["founder-1"][0]["role"] == "user"
        assert agent._conversation_history["founder-1"][1]["role"] == "assistant"
