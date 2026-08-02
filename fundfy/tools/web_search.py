"""Web search tool using Tavily API."""

from typing import Any

from pydantic import BaseModel

from fundfy.config import settings
from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult


class WebSearchArgs(BaseModel):
    """Arguments for web search tool."""

    query: str
    max_results: int = 5


class WebSearchTool(BaseTool):
    """Search the web using Tavily API."""

    name = "web_search"
    description = "Search the web for information. Returns a list of results with title, url, and content snippet."
    args_schema = WebSearchArgs

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or settings.tavily_api_key

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute a web search query."""
        args = WebSearchArgs(**kwargs)

        if not self._api_key:
            return ToolResult(
                success=False,
                error="TAVILY_API_KEY not configured. Web search is unavailable.",
            )

        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self._api_key)
            response = client.search(query=args.query, max_results=args.max_results)

            results = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                }
                for r in response.get("results", [])
            ]

            return ToolResult(success=True, data=results)
        except Exception as e:
            return ToolResult(success=False, error=f"Web search failed: {str(e)}")
