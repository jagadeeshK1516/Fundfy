"""Test Founder Communication module."""

from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage

from fundfy.communication.modes import ConversationMode
from fundfy.communication.session import CommunicationSession


@pytest.mark.asyncio
async def test_mock_interview_session():
    """Mock interview session returns interviewer-style follow-up."""
    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(
            content="That's interesting. Can you tell me more about your customer acquisition strategy? What's your current CAC and how do you plan to reduce it?"
        )
    )

    session = CommunicationSession(
        founder_id="founder-1",
        mode=ConversationMode.MOCK_INTERVIEW,
        llm=mock_llm,
    )

    response = await session.send_message("We're building an AI-powered CRM for SMBs.")

    assert "?" in response  # Should contain a follow-up question
    assert len(response) > 0
    mock_llm.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_mode_switching():
    """Session correctly switches between modes."""
    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="Great, let's practice your pitch.")
    )

    session = CommunicationSession(
        founder_id="founder-1",
        mode=ConversationMode.CHAT,
        llm=mock_llm,
    )

    assert session.mode == ConversationMode.CHAT
    session.switch_mode(ConversationMode.PITCH_PRACTICE)
    assert session.mode == ConversationMode.PITCH_PRACTICE


@pytest.mark.asyncio
async def test_conversation_history_maintained():
    """Session maintains conversation history."""
    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="Hello! How can I help?")
    )

    session = CommunicationSession(
        founder_id="founder-1",
        mode=ConversationMode.CHAT,
        llm=mock_llm,
    )

    await session.send_message("Hi there")
    history = session.get_history()

    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hi there"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hello! How can I help?"
