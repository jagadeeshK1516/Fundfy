"""Workstream tools — create and update workstreams."""

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult

# Module-level store for workstreams created by tools
_tool_workstreams: dict[str, dict[str, Any]] = {}


class CreateWorkstreamArgs(BaseModel):
    """Arguments for create_workstream tool."""

    business_id: str
    title: str
    steps: list[str]


class UpdateWorkstreamArgs(BaseModel):
    """Arguments for update_workstream tool."""

    workstream_id: str
    step_index: int
    status: str
    result_summary: str | None = None


class CreateWorkstreamTool(BaseTool):
    """Create a new workstream with a set of steps to execute."""

    name = "create_workstream"
    description = "Create a new workstream (project plan) with ordered steps. Returns the workstream ID for tracking."
    args_schema = CreateWorkstreamArgs

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Create a new workstream."""
        args = CreateWorkstreamArgs(**kwargs)
        try:
            workstream_id = str(uuid.uuid4())
            workstream = {
                "id": workstream_id,
                "business_id": args.business_id,
                "title": args.title,
                "steps": [
                    {"index": i, "description": step, "status": "pending"}
                    for i, step in enumerate(args.steps)
                ],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            _tool_workstreams[workstream_id] = workstream
            return ToolResult(success=True, data=workstream)
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to create workstream: {str(e)}")


class UpdateWorkstreamTool(BaseTool):
    """Update the status of a workstream step."""

    name = "update_workstream"
    description = "Update the status of a specific step in a workstream. Use to mark steps as in_progress, completed, or failed."
    args_schema = UpdateWorkstreamArgs

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Update a workstream step status."""
        args = UpdateWorkstreamArgs(**kwargs)
        try:
            workstream = _tool_workstreams.get(args.workstream_id)
            if not workstream:
                return ToolResult(success=False, error=f"Workstream {args.workstream_id} not found.")

            steps = workstream["steps"]
            if args.step_index < 0 or args.step_index >= len(steps):
                return ToolResult(success=False, error=f"Step index {args.step_index} out of range.")

            steps[args.step_index]["status"] = args.status
            if args.result_summary:
                steps[args.step_index]["result_summary"] = args.result_summary

            return ToolResult(success=True, data=workstream)
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to update workstream: {str(e)}")
