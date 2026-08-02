"""Communication session — extends agent behavior with conversation modes."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from fundfy.communication.modes import ConversationMode
from fundfy.communication.prompts import MODE_PROMPTS
from fundfy.config import settings
from fundfy.memory.engine import MemoryEngine


class CommunicationSession:
    """Manages a communication session with mode-specific behavior."""

    def __init__(
        self,
        founder_id: str,
        mode: ConversationMode = ConversationMode.CHAT,
        llm: Any = None,
        memory_engine: MemoryEngine | None = None,
    ):
        self.founder_id = founder_id
        self.mode = mode
        self._llm = llm or ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            temperature=0.7,
        )
        self._memory = memory_engine
        self._history: list[dict[str, str]] = []

    def switch_mode(self, mode: ConversationMode):
        """Switch the conversation mode."""
        self.mode = mode
        self._history = []  # Reset history on mode switch

    async def send_message(self, message: str) -> str:
        """Send a message in the current conversation mode.

        Args:
            message: The user's message.

        Returns:
            The AI response string.
        """
        # Get mode-specific system prompt
        system_prompt = MODE_PROMPTS.get(self.mode.value, MODE_PROMPTS["chat"])

        # Retrieve context from memory
        context_text = ""
        if self._memory:
            docs = self._memory.query(message, k=3)
            context_text = "\n".join(d.page_content for d in docs)

        # Build conversation history
        history_text = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in self._history[-20:]
        )

        # Construct prompt
        user_content = ""
        if context_text:
            user_content += f"## Business Context\n{context_text}\n\n"
        if history_text:
            user_content += f"## Conversation History\n{history_text}\n\n"
        user_content += f"## Founder's Message\n{message}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ]

        response = await self._llm.ainvoke(messages)
        response_text = response.content

        # Persist to history
        self._history.append({"role": "user", "content": message})
        self._history.append({"role": "assistant", "content": response_text})

        return response_text

    def get_history(self) -> list[dict[str, str]]:
        """Return the conversation history."""
        return self._history.copy()
