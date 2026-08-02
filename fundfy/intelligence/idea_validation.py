"""Idea validation handler."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from fundfy.orchestrator.handlers.base import BaseHandler, TaskResult

IDEA_VALIDATION_PROMPT = """You are a startup advisor specializing in idea validation. Evaluate the following business idea:
1. Feasibility assessment (technical, market, financial)
2. Key risks and mitigation strategies
3. Opportunities and potential upside
4. Recommended next steps for validation
5. Overall viability score (1-10) with justification

Idea: {idea}
Additional Context: {context}

Provide your analysis in a structured format."""


class IdeaValidationHandler(BaseHandler):
    """Handler for idea validation workstream tasks."""

    def __init__(self, llm: Any = None, memory_engine: Any = None):
        self._llm = llm
        self._memory = memory_engine

    async def run(self, task: dict[str, Any]) -> TaskResult:
        """Execute idea validation analysis."""
        params = task.get("params", {})
        idea = params.get("idea", "")
        context = params.get("context", "")

        memory_context = ""
        if self._memory:
            docs = self._memory.query(f"idea validation {idea}", k=3)
            memory_context = "\n".join(d.page_content for d in docs)

        prompt = IDEA_VALIDATION_PROMPT.format(
            idea=idea,
            context=f"{context}\n{memory_context}",
        )

        messages = [
            SystemMessage(content="You are a startup advisor specializing in idea validation."),
            HumanMessage(content=prompt),
        ]

        response = await self._llm.ainvoke(messages)

        result = {
            "analysis": response.content,
            "idea": idea,
            "task_type": "idea_validation",
        }

        if self._memory:
            self._memory.ingest(
                response.content,
                {"source_type": "idea_validation"},
            )

        return TaskResult(
            task_id=task.get("title", "idea_validation"),
            task_type="idea_validation",
            status="completed",
            result=result,
        )
