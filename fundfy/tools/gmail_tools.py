"""Gmail tools for the AI agent."""

import uuid
from typing import Any

from pydantic import BaseModel

from fundfy.db import async_session
from fundfy.models.email_approval import EmailApproval
from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult


class SendEmailArgs(BaseModel):
    """Arguments for send_email tool."""

    to: str
    subject: str
    body: str
    founder_id: str


class ReadEmailsArgs(BaseModel):
    """Arguments for read_emails tool."""

    query: str = ""
    max_results: int = 10
    founder_id: str


class SendEmailTool(BaseTool):
    """Creates an email draft and marks it PENDING_APPROVAL (never auto-sends)."""

    name = "send_email"
    description = "Draft an email and queue it for founder approval. Never sends automatically."
    args_schema = SendEmailArgs

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Create a pending email approval."""
        args = SendEmailArgs(**kwargs)

        async with async_session() as session:
            approval = EmailApproval(
                id=str(uuid.uuid4()),
                founder_id=args.founder_id,
                to=args.to,
                subject=args.subject,
                body=args.body,
                status="pending",
            )
            session.add(approval)
            await session.commit()

        return ToolResult(
            success=True,
            data={
                "approval_id": approval.id,
                "status": "pending",
                "message": f"Email to {args.to} queued for approval. Subject: {args.subject}",
            },
        )


class ReadEmailsTool(BaseTool):
    """Fetches recent emails matching a query via Gmail API."""

    name = "read_emails"
    description = "Read recent emails from Gmail matching a query filter."
    args_schema = ReadEmailsArgs

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Read emails using Gmail API."""
        args = ReadEmailsArgs(**kwargs)

        try:
            from fundfy.integrations.google_auth import get_access_token
            from google.oauth2.credentials import Credentials

            access_token = await get_access_token(args.founder_id)
            if not access_token:
                return ToolResult(
                    success=False,
                    error="Google account not connected. Please connect via Integrations settings.",
                )

            credentials = Credentials(token=access_token)
            from fundfy.integrations.gmail import GmailService

            gmail = GmailService(credentials)
            emails = gmail.read_emails(query=args.query, max_results=args.max_results)

            return ToolResult(success=True, data={"emails": emails, "count": len(emails)})
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to read emails: {str(e)}")
