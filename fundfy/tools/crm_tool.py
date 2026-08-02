"""CRM tools for the AI agent."""

from typing import Any

from pydantic import BaseModel

from fundfy.integrations.crm import CRMService
from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult


class AddContactArgs(BaseModel):
    """Arguments for add_contact tool."""

    founder_id: str
    name: str
    email: str | None = None
    company: str | None = None
    role: str | None = None
    type: str = "other"
    notes: str | None = None


class UpdateContactArgs(BaseModel):
    """Arguments for update_contact tool."""

    contact_id: str
    pipeline_stage: str | None = None
    notes: str | None = None
    email: str | None = None
    company: str | None = None


class LogInteractionArgs(BaseModel):
    """Arguments for log_interaction tool."""

    contact_id: str
    founder_id: str
    type: str = "note"  # email/meeting/call/note
    summary: str
    details: str | None = None


class GetPipelineArgs(BaseModel):
    """Arguments for get_pipeline tool."""

    founder_id: str


class AddContactTool(BaseTool):
    """Add a new contact to the CRM."""

    name = "add_contact"
    description = "Add a new contact to the CRM pipeline."
    args_schema = AddContactArgs

    def __init__(self):
        self._crm = CRMService()

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Add a contact."""
        args = AddContactArgs(**kwargs)
        try:
            result = await self._crm.add_contact(
                founder_id=args.founder_id,
                data={
                    "name": args.name,
                    "email": args.email,
                    "company": args.company,
                    "role": args.role,
                    "type": args.type,
                    "notes": args.notes,
                },
            )
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to add contact: {str(e)}")


class UpdateContactTool(BaseTool):
    """Update a CRM contact."""

    name = "update_contact"
    description = "Update an existing CRM contact's info or pipeline stage."
    args_schema = UpdateContactArgs

    def __init__(self):
        self._crm = CRMService()

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Update a contact."""
        args = UpdateContactArgs(**kwargs)
        data = {}
        if args.pipeline_stage:
            data["pipeline_stage"] = args.pipeline_stage
        if args.notes:
            data["notes"] = args.notes
        if args.email:
            data["email"] = args.email
        if args.company:
            data["company"] = args.company

        try:
            result = await self._crm.update_contact(args.contact_id, data)
            if result is None:
                return ToolResult(success=False, error="Contact not found.")
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to update contact: {str(e)}")


class LogInteractionTool(BaseTool):
    """Log an interaction with a CRM contact."""

    name = "log_interaction"
    description = "Log an interaction (email, meeting, call, note) with a CRM contact."
    args_schema = LogInteractionArgs

    def __init__(self):
        self._crm = CRMService()

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Log an interaction."""
        args = LogInteractionArgs(**kwargs)
        try:
            result = await self._crm.log_interaction(
                contact_id=args.contact_id,
                founder_id=args.founder_id,
                data={
                    "type": args.type,
                    "summary": args.summary,
                    "details": args.details,
                },
            )
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to log interaction: {str(e)}")


class GetPipelineTool(BaseTool):
    """Get the CRM pipeline summary."""

    name = "get_pipeline"
    description = "Get the CRM pipeline summary with contact counts per stage."
    args_schema = GetPipelineArgs

    def __init__(self):
        self._crm = CRMService()

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Get pipeline summary."""
        args = GetPipelineArgs(**kwargs)
        try:
            result = await self._crm.get_pipeline_summary(args.founder_id)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to get pipeline: {str(e)}")
