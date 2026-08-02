"""Conversation modes for founder communication."""

from enum import Enum


class ConversationMode(str, Enum):
    """Available conversation modes."""

    CHAT = "chat"
    MOCK_INTERVIEW = "mock_interview"
    PITCH_PRACTICE = "pitch_practice"
    QA_REHEARSAL = "qa_rehearsal"
