"""Market research handler."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from fundfy.orchestrator.handlers.base import BaseHandler, TaskResult

MARKET_RESEARCH_PROMPT = """You are a market research analyst. Analyze the following market and provide:
1. Total Addressable Market (TAM)
2. Serviceable Addressable Market (SAM)
3. Serviceable Obtainable Market (SOM)
4. Key market trends
5. Growth rate and projections

Industry: {industry}
Additional Context: {context}

Provide your analysis in a structured format."""


class MarketResearchHandler(BaseHandler):
    """Handler for market research workstream tasks."""

    def __init__(self, llm: Any = None, memory_engine: Any = None):
        self._llm = llm
        self._memory = memory_engine

    async def run(self, task: dict[str, Any]) -> TaskResult:
        """Execute market research analysis."""
        params = task.get("params", {})
        industry = params.get("industry", "general")
        context = params.get("context", "")

        # Retrieve relevant memory context
        memory_context = ""
        if self._memory:
            docs = self._memory.query(f"market research {industry}", k=3)
            memory_context = "\n".join(d.page_content for d in docs)

        prompt = MARKET_RESEARCH_PROMPT.format(
            industry=industry,
            context=f"{context}\n{memory_context}",
        )

        messages = [
            SystemMessage(content="You are a market research analyst."),
            HumanMessage(content=prompt),
        ]

        response = await self._llm.ainvoke(messages)

        result = {
            "analysis": response.content,
            "industry": industry,
            "task_type": "market_research",
        }

        # Ingest results back into memory
        if self._memory:
            self._memory.ingest(
                response.content,
                {"source_type": "market_research", "industry": industry},
            )

        return TaskResult(
            task_id=task.get("title", "market_research"),
            task_type="market_research",
            status="completed",
            result=result,
        )
