"""Document generation handler for the orchestrator."""

from typing import Any

from fundfy.documents.generator import DocumentGenerator
from fundfy.orchestrator.handlers.base import BaseHandler, TaskResult


class DocumentGenerationHandler(BaseHandler):
    """Handler that delegates document generation to DocumentGenerator."""

    def __init__(self, llm: Any = None, memory_engine: Any = None):
        self._generator = DocumentGenerator(llm=llm, memory_engine=memory_engine)

    async def run(self, task: dict[str, Any]) -> TaskResult:
        """Execute document generation."""
        params = task.get("params", {})
        doc_type = params.get("doc_type", "business_plan")
        business_id = params.get("business_id", "unknown")
        context = params.get("context", "")

        try:
            doc = await self._generator.generate(doc_type, business_id, context)
            return TaskResult(
                task_id=task.get("title", "document_generation"),
                task_type="document_generation",
                status="completed",
                result=doc,
            )
        except Exception as e:
            return TaskResult(
                task_id=task.get("title", "document_generation"),
                task_type="document_generation",
                status="failed",
                error=str(e),
            )
