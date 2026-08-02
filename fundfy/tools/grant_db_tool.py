"""Grant database tools for the AI agent."""

from typing import Any

from pydantic import BaseModel

from fundfy.integrations.grant_db import GrantDatabase
from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult


class SearchGrantDatabaseArgs(BaseModel):
    """Arguments for search_grant_database tool."""

    industry: str | None = None
    amount_min: float | None = None
    amount_max: float | None = None
    region: str | None = None
    status: str | None = "open"


class TrackGrantApplicationArgs(BaseModel):
    """Arguments for track_grant_application tool."""

    grant_id: str
    founder_id: str
    business_id: str | None = None
    status: str = "discovered"
    notes: str | None = None


class SearchGrantDatabaseTool(BaseTool):
    """Search the grant database with filters."""

    name = "search_grant_database"
    description = "Search grants by industry, amount, deadline, region, and eligibility."
    args_schema = SearchGrantDatabaseArgs

    def __init__(self):
        self._db = GrantDatabase()

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Search grants."""
        args = SearchGrantDatabaseArgs(**kwargs)
        filters = {}
        if args.industry:
            filters["industry"] = args.industry
        if args.amount_min is not None:
            filters["amount_min"] = args.amount_min
        if args.amount_max is not None:
            filters["amount_max"] = args.amount_max
        if args.region:
            filters["region"] = args.region
        if args.status:
            filters["status"] = args.status

        try:
            results = await self._db.search(filters)
            return ToolResult(
                success=True,
                data={"grants": results, "count": len(results)},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Grant search failed: {str(e)}")


class TrackGrantApplicationTool(BaseTool):
    """Track a grant application status."""

    name = "track_grant_application"
    description = "Track or update the status of a grant application."
    args_schema = TrackGrantApplicationArgs

    def __init__(self):
        self._db = GrantDatabase()

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Create or update a grant application tracking record."""
        args = TrackGrantApplicationArgs(**kwargs)

        try:
            result = await self._db.create_application(
                founder_id=args.founder_id,
                grant_id=args.grant_id,
                business_id=args.business_id,
                notes=args.notes,
            )
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to track application: {str(e)}")
