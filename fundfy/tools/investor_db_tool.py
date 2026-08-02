"""Investor database tool for the AI agent."""

from typing import Any

from pydantic import BaseModel

from fundfy.integrations.investor_db import InvestorDatabase
from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult


class SearchInvestorDatabaseArgs(BaseModel):
    """Arguments for search_investor_database tool."""

    stage: str | None = None
    industry: str | None = None
    check_size_min: float | None = None
    check_size_max: float | None = None
    location: str | None = None


class SearchInvestorDatabaseTool(BaseTool):
    """Search the built-in investor database with filters."""

    name = "search_investor_database"
    description = "Search the investor database by stage, industry, check size, and location."
    args_schema = SearchInvestorDatabaseArgs

    def __init__(self):
        self._db = InvestorDatabase()

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Search investors."""
        args = SearchInvestorDatabaseArgs(**kwargs)
        filters = {}
        if args.stage:
            filters["stage"] = args.stage
        if args.industry:
            filters["industry"] = args.industry
        if args.check_size_min is not None:
            filters["check_size_min"] = args.check_size_min
        if args.check_size_max is not None:
            filters["check_size_max"] = args.check_size_max
        if args.location:
            filters["location"] = args.location

        try:
            results = await self._db.search(filters)
            return ToolResult(
                success=True,
                data={"investors": results, "count": len(results)},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Investor search failed: {str(e)}")
