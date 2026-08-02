"""Execution planner — decomposes objectives into workstream tasks."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from fundfy.config import settings

PLANNING_PROMPT = """You are a business execution planner. Given a founder's objective and business context, decompose it into a list of parallel workstream tasks.

Return a JSON array of task objects, each with:
- "type": one of "market_research", "competitor_analysis", "idea_validation", "financial_reasoning", "document_generation"
- "title": brief task title
- "params": object with parameters for the task handler

Only return the JSON array, no other text."""


class ExecutionPlanner:
    """Plans execution by decomposing objectives into workstream tasks."""

    def __init__(self, llm: Any = None):
        self._llm = llm or ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            temperature=0.3,
        )

    async def plan(self, objective: str, business_context: str = "") -> list[dict[str, Any]]:
        """Decompose an objective into workstream tasks.

        Args:
            objective: The founder's business objective.
            business_context: Additional context about the business.

        Returns:
            List of task dictionaries with type, title, and params.
        """
        messages = [
            SystemMessage(content=PLANNING_PROMPT),
            HumanMessage(content=f"Objective: {objective}\n\nBusiness Context: {business_context}"),
        ]

        response = await self._llm.ainvoke(messages)
        content = response.content.strip()

        # Parse JSON from response
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        tasks = json.loads(content)
        return tasks
