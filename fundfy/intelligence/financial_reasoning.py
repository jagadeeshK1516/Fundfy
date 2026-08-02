"""Financial reasoning handler."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from fundfy.orchestrator.handlers.base import BaseHandler, TaskResult

FINANCIAL_REASONING_PROMPT = """You are a financial analyst specializing in startup economics. Analyze:
1. Revenue model options and recommendations
2. Unit economics (CAC, LTV, LTV/CAC ratio)
3. Pricing strategy recommendations
4. Break-even analysis
5. 3-year financial projections

Business Context: {business}
Additional Context: {context}

Provide your analysis in a structured format with specific numbers where possible."""


class FinancialReasoningHandler(BaseHandler):
    """Handler for financial reasoning workstream tasks."""

    def __init__(self, llm: Any = None, memory_engine: Any = None):
        self._llm = llm
        self._memory = memory_engine

    async def run(self, task: dict[str, Any]) -> TaskResult:
        """Execute financial reasoning analysis."""
        params = task.get("params", {})
        business = params.get("business", "")
        context = params.get("context", "")

        memory_context = ""
        if self._memory:
            docs = self._memory.query(f"financial analysis {business}", k=3)
            memory_context = "\n".join(d.page_content for d in docs)

        prompt = FINANCIAL_REASONING_PROMPT.format(
            business=business,
            context=f"{context}\n{memory_context}",
        )

        messages = [
            SystemMessage(content="You are a financial analyst specializing in startup economics."),
            HumanMessage(content=prompt),
        ]

        response = await self._llm.ainvoke(messages)

        result = {
            "analysis": response.content,
            "business": business,
            "task_type": "financial_reasoning",
        }

        if self._memory:
            self._memory.ingest(
                response.content,
                {"source_type": "financial_reasoning"},
            )

        return TaskResult(
            task_id=task.get("title", "financial_reasoning"),
            task_type="financial_reasoning",
            status="completed",
            result=result,
        )
