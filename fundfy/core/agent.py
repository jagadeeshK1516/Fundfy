"""Core Fundfy AI Agent — conversational chain with RAG retrieval and ReAct tool-use."""

from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from fundfy.config import settings
from fundfy.core.prompts import SYSTEM_PROMPT, CONTEXT_INJECTION_TEMPLATE
from fundfy.core.react_agent import AgentResponse, ReActAgent
from fundfy.memory.engine import MemoryEngine
from fundfy.tools.base import BaseTool

CLASSIFIER_PROMPT = """Determine if this user message requires tool use (web research, document generation, financial analysis, email drafting, workstream creation) or is a simple conversational reply that can be answered with existing context.

Message: {message}

Answer with exactly one word: TOOL_USE or CHAT_ONLY"""


class FundfyAgent:
    """Central AI agent that uses RAG retrieval before every response.

    When tools are available and the message requires them, delegates to the
    ReAct agent for autonomous multi-step execution.
    """

    def __init__(
        self,
        memory_engine: MemoryEngine,
        llm: ChatOpenAI | None = None,
        tools: dict[str, BaseTool] | None = None,
    ):
        self._memory = memory_engine
        self._llm = llm or ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            temperature=0.7,
        )
        self._tools = tools or {}
        self._react_agent: ReActAgent | None = None
        if self._tools:
            self._react_agent = ReActAgent(
                llm=self._llm,
                tools=self._tools,
                memory_engine=self._memory,
            )
        self._conversation_history: dict[str, list[dict[str, str]]] = {}

    async def chat(self, founder_id: str, message: str) -> str:
        """Process a chat message: retrieve context, call LLM, persist exchange.

        If tools are available, classifies the message first. Complex requests
        are delegated to the ReAct agent.

        Args:
            founder_id: The founder's ID.
            message: The user's message.

        Returns:
            The AI response string.
        """
        # If we have a ReAct agent, classify the message
        if self._react_agent:
            classification = await self._classify(message)
            if classification == "TOOL_USE":
                result = await self._react_agent.run(founder_id, message)
                # Persist to conversation history
                self._persist_exchange(founder_id, message, result.response)
                return result.response

        # Default: RAG-only path
        return await self._rag_chat(founder_id, message)

    async def chat_with_metadata(self, founder_id: str, message: str) -> dict[str, Any]:
        """Process a chat message and return enriched response with metadata.

        Returns:
            Dictionary with response text and optional tool_calls, steps, checkpoints, files.
        """
        if self._react_agent:
            classification = await self._classify(message)
            if classification == "TOOL_USE":
                result = await self._react_agent.run(founder_id, message)
                self._persist_exchange(founder_id, message, result.response)
                return {
                    "response": result.response,
                    "tool_calls": result.tool_calls,
                    "steps": result.steps,
                    "checkpoints": result.checkpoints,
                }

        response_text = await self._rag_chat(founder_id, message)
        return {"response": response_text}

    async def execute(self, founder_id: str, objective: str) -> AgentResponse:
        """Execute an objective using the ReAct agent (always uses tool loop).

        Args:
            founder_id: The founder's ID.
            objective: The task/objective to accomplish.

        Returns:
            AgentResponse with full execution trace.
        """
        if not self._react_agent:
            return AgentResponse(
                response="Tool execution is not available. No tools are configured.",
                tool_calls=[],
                steps=0,
                checkpoints=[],
            )
        return await self._react_agent.run(founder_id, objective)

    async def _classify(self, message: str) -> str:
        """Classify whether a message needs tool use or simple chat."""
        try:
            messages = [
                SystemMessage(content="You are a message classifier. Respond with exactly one word."),
                HumanMessage(content=CLASSIFIER_PROMPT.format(message=message)),
            ]
            response = await self._llm.ainvoke(messages)
            text = response.content.strip().upper()
            if "TOOL_USE" in text:
                return "TOOL_USE"
            return "CHAT_ONLY"
        except Exception:
            # If classification fails, default to chat-only
            return "CHAT_ONLY"

    async def _rag_chat(self, founder_id: str, message: str) -> str:
        """RAG-only chat path (original behavior)."""
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

        # Persist exchange
        self._persist_exchange(founder_id, message, response_text)

        return response_text

    def _persist_exchange(self, founder_id: str, message: str, response_text: str) -> None:
        """Persist a conversation exchange to history and memory."""
        if founder_id not in self._conversation_history:
            self._conversation_history[founder_id] = []
        self._conversation_history[founder_id].append({"role": "user", "content": message})
        self._conversation_history[founder_id].append({"role": "assistant", "content": response_text})

        # Persist exchange to memory for future retrieval
        self._memory.ingest(
            f"User: {message}\nAssistant: {response_text}",
            metadata={"source_type": "conversation", "founder_id": founder_id},
        )
