"""Research tools — composite tools using web_search + LLM extraction."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult
from fundfy.tools.web_search import WebSearchTool


class SearchGrantsArgs(BaseModel):
    """Arguments for search_grants tool."""

    query: str
    industry: str | None = None


class SearchInvestorsArgs(BaseModel):
    """Arguments for search_investors tool."""

    query: str
    stage: str | None = None
    industry: str | None = None


GRANTS_EXTRACTION_PROMPT = """Extract grant opportunities from the following search results.
Return a JSON array of grant objects with these fields:
- name: grant name
- organization: granting organization
- amount: funding amount if mentioned
- deadline: application deadline if mentioned
- eligibility: eligibility criteria
- url: link to the grant
- description: brief description

Search results:
{results}

Return ONLY valid JSON array. If no grants found, return [].
"""

INVESTORS_EXTRACTION_PROMPT = """Extract investor profiles from the following search results.
Return a JSON array of investor objects with these fields:
- name: investor name
- firm: firm name
- focus_areas: list of focus areas/industries
- stage_preference: preferred investment stage
- typical_check_size: typical investment amount
- website: link to firm

Search results:
{results}

Return ONLY valid JSON array. If no investors found, return [].
"""


class SearchGrantsTool(BaseTool):
    """Search for grant opportunities relevant to the business."""

    name = "search_grants"
    description = "Search for grant opportunities for startups. Provide a query and optional industry. Returns structured grant information."
    args_schema = SearchGrantsArgs

    def __init__(self, llm: Any, web_search_tool: WebSearchTool):
        self._llm = llm
        self._web_search = web_search_tool

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Search for grants and extract structured data."""
        args = SearchGrantsArgs(**kwargs)

        try:
            search_query = f"grants for {args.query} startups"
            if args.industry:
                search_query += f" {args.industry}"

            search_result = await self._web_search.execute(query=search_query, max_results=5)
            if not search_result.success:
                return ToolResult(success=False, error=f"Web search failed: {search_result.error}")

            # Format results for extraction
            results_text = "\n\n".join(
                f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content']}"
                for r in (search_result.data or [])
            )

            if not results_text:
                return ToolResult(success=True, data=[])

            # Use LLM to extract structured data
            messages = [
                SystemMessage(content="You are a structured data extraction assistant. Extract information exactly as requested."),
                HumanMessage(content=GRANTS_EXTRACTION_PROMPT.format(results=results_text)),
            ]

            response = await self._llm.ainvoke(messages)

            import json
            try:
                grants = json.loads(response.content)
            except json.JSONDecodeError:
                grants = []

            return ToolResult(success=True, data=grants)
        except Exception as e:
            return ToolResult(success=False, error=f"Grant search failed: {str(e)}")


class SearchInvestorsTool(BaseTool):
    """Search for investors relevant to the business."""

    name = "search_investors"
    description = "Search for investors interested in specific industries and stages. Returns structured investor profiles."
    args_schema = SearchInvestorsArgs

    def __init__(self, llm: Any, web_search_tool: WebSearchTool):
        self._llm = llm
        self._web_search = web_search_tool

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Search for investors and extract structured data."""
        args = SearchInvestorsArgs(**kwargs)

        try:
            search_query = f"investors {args.query}"
            if args.stage:
                search_query += f" {args.stage} stage"
            if args.industry:
                search_query += f" {args.industry}"

            search_result = await self._web_search.execute(query=search_query, max_results=5)
            if not search_result.success:
                return ToolResult(success=False, error=f"Web search failed: {search_result.error}")

            # Format results for extraction
            results_text = "\n\n".join(
                f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content']}"
                for r in (search_result.data or [])
            )

            if not results_text:
                return ToolResult(success=True, data=[])

            # Use LLM to extract structured data
            messages = [
                SystemMessage(content="You are a structured data extraction assistant. Extract information exactly as requested."),
                HumanMessage(content=INVESTORS_EXTRACTION_PROMPT.format(results=results_text)),
            ]

            response = await self._llm.ainvoke(messages)

            import json
            try:
                investors = json.loads(response.content)
            except json.JSONDecodeError:
                investors = []

            return ToolResult(success=True, data=investors)
        except Exception as e:
            return ToolResult(success=False, error=f"Investor search failed: {str(e)}")
