"""Competitor analysis handler."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from fundfy.orchestrator.handlers.base import BaseHandler, TaskResult

COMPETITOR_ANALYSIS_PROMPT = """You are a competitive intelligence analyst. Analyze the competitive landscape for:
1. Key competitors and their market positioning
2. Strengths and weaknesses of each competitor
3. Market gaps and opportunities
4. Competitive advantages to develop
5. Recommended positioning strategy

Market/Industry: {market}
Additional Context: {context}

Provide your analysis in a structured format."""


class CompetitorAnalysisHandler(BaseHandler):
    """Handler for competitor analysis workstream tasks."""

    def __init__(self, llm: Any = None, memory_engine: Any = None):
        self._llm = llm
        self._memory = memory_engine

    async def run(self, task: dict[str, Any]) -> TaskResult:
        """Execute competitor analysis."""
        params = task.get("params", {})
        market = params.get("market", "general")
        context = params.get("context", "")

        memory_context = ""
        if self._memory:
            docs = self._memory.query(f"competitor analysis {market}", k=3)
            memory_context = "\n".join(d.page_content for d in docs)

        prompt = COMPETITOR_ANALYSIS_PROMPT.format(
            market=market,
            context=f"{context}\n{memory_context}",
        )

        messages = [
            SystemMessage(content="You are a competitive intelligence analyst."),
            HumanMessage(content=prompt),
        ]

        response = await self._llm.ainvoke(messages)

        result = {
            "analysis": response.content,
            "market": market,
            "task_type": "competitor_analysis",
        }

        if self._memory:
            self._memory.ingest(
                response.content,
                {"source_type": "competitor_analysis", "market": market},
            )

        return TaskResult(
            task_id=task.get("title", "competitor_analysis"),
            task_type="competitor_analysis",
            status="completed",
            result=result,
        )
