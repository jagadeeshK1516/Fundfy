"""Core Fundfy AI Agent — conversational chain with RAG retrieval."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from fundfy.config import settings
from fundfy.core.prompts import SYSTEM_PROMPT, CONTEXT_INJECTION_TEMPLATE
from fundfy.memory.engine import MemoryEngine


class FundfyAgent:
    """Central AI agent that uses RAG retrieval before every response."""

    def __init__(self, memory_engine: MemoryEngine, llm: ChatOpenAI | None = None):
        self._memory = memory_engine
        self._llm = llm or ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            temperature=0.7,
        )
        self._conversation_history: dict[str, list[dict[str, str]]] = {}

    async def chat(self, founder_id: str, message: str) -> str:
        """Process a chat message: retrieve context, call LLM, persist exchange.

        Args:
            founder_id: The founder's ID.
            message: The user's message.

        Returns:
            The AI response string.
        """
        # Retrieve relevant context from memory
        context_docs = self._memory.query(message, filters=None, k=5)
        context_text = "\n\n".join(
            doc.page_content for doc in context_docs
        ) if context_docs else "No relevant context found."

        # Get conversation history
        history = self._conversation_history.get(founder_id, [])
        history_text = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in history[-20:]  # Window of last 20 messages
        )

        # Build prompt
        user_prompt = CONTEXT_INJECTION_TEMPLATE.format(
            context=context_text,
            history=history_text,
            message=message,
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        # Call LLM
        response = await self._llm.ainvoke(messages)
        response_text = response.content

        # Persist to conversation history
        if founder_id not in self._conversation_history:
            self._conversation_history[founder_id] = []
        self._conversation_history[founder_id].append({"role": "user", "content": message})
        self._conversation_history[founder_id].append({"role": "assistant", "content": response_text})

        # Persist exchange to memory for future retrieval
        self._memory.ingest(
            f"User: {message}\nAssistant: {response_text}",
            metadata={"source_type": "conversation", "founder_id": founder_id},
        )

        return response_text
