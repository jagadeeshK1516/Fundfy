"""Memory tools — save to and query the vector memory store."""

from typing import Any

from pydantic import BaseModel

from fundfy.memory.engine import MemoryEngine
from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult


class SaveToMemoryArgs(BaseModel):
    """Arguments for save_to_memory tool."""

    content: str
    metadata: dict[str, Any] | None = None


class QueryMemoryArgs(BaseModel):
    """Arguments for query_memory tool."""

    query: str
    k: int = 5


class SaveToMemoryTool(BaseTool):
    """Save information to the business memory for future retrieval."""

    name = "save_to_memory"
    description = "Save content to the business memory store for future retrieval. Use this to persist research findings, decisions, or important information."
    args_schema = SaveToMemoryArgs

    def __init__(self, memory_engine: MemoryEngine):
        self._memory = memory_engine

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Save content to memory."""
        args = SaveToMemoryArgs(**kwargs)
        try:
            ids = self._memory.ingest(args.content, args.metadata)
            return ToolResult(
                success=True,
                data={"saved_ids": ids, "content_length": len(args.content)},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to save to memory: {str(e)}")


class QueryMemoryTool(BaseTool):
    """Query the business memory for relevant information."""

    name = "query_memory"
    description = "Search the business memory for relevant information. Returns previously stored content matching the query."
    args_schema = QueryMemoryArgs

    def __init__(self, memory_engine: MemoryEngine):
        self._memory = memory_engine

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Query memory for relevant documents."""
        args = QueryMemoryArgs(**kwargs)
        try:
            docs = self._memory.query(args.query, k=args.k)
            results = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                }
                for doc in docs
            ]
            return ToolResult(success=True, data=results)
        except Exception as e:
            return ToolResult(success=False, error=f"Memory query failed: {str(e)}")
