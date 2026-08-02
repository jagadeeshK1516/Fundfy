"""Email drafting tool — uses LLM to compose professional emails."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult

# Module-level store for email drafts
_email_drafts: list[dict[str, Any]] = []

EMAIL_SYSTEM_PROMPTS = {
    "investor_outreach": "You are an expert at writing compelling investor outreach emails for startups. Write a professional, concise email that captures attention and clearly communicates value.",
    "grant_cover_letter": "You are an expert at writing grant cover letters. Write a professional cover letter that highlights the applicant's qualifications and alignment with the grant's objectives.",
    "introduction_request": "You are an expert at writing professional introduction request emails. Write a warm, respectful email requesting an introduction.",
    "follow_up": "You are an expert at writing professional follow-up emails. Write a polite, value-adding follow-up that moves the conversation forward.",
}


class DraftEmailArgs(BaseModel):
    """Arguments for draft_email tool."""

    email_type: str
    recipient_context: str
    business_context: str


class DraftEmailTool(BaseTool):
    """Draft a professional email using AI."""

    name = "draft_email"
    description = "Draft a professional email (investor_outreach, grant_cover_letter, introduction_request, or follow_up). Provide recipient and business context."
    args_schema = DraftEmailArgs

    def __init__(self, llm: Any):
        self._llm = llm

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Draft an email."""
        args = DraftEmailArgs(**kwargs)

        if args.email_type not in EMAIL_SYSTEM_PROMPTS:
            return ToolResult(
                success=False,
                error=f"Unknown email type: {args.email_type}. Use one of: {list(EMAIL_SYSTEM_PROMPTS.keys())}",
            )

        try:
            system_prompt = EMAIL_SYSTEM_PROMPTS[args.email_type]
            user_prompt = (
                f"Write an email of type '{args.email_type}'.\n\n"
                f"Recipient context: {args.recipient_context}\n\n"
                f"Business context: {args.business_context}\n\n"
                "Format the response as:\nSubject: <subject line>\n\n<email body>"
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await self._llm.ainvoke(messages)
            content = response.content

            # Parse subject and body
            subject = ""
            body = content
            if "Subject:" in content:
                parts = content.split("\n", 1)
                if parts[0].startswith("Subject:"):
                    subject = parts[0].replace("Subject:", "").strip()
                    body = parts[1].strip() if len(parts) > 1 else ""

            draft = {
                "subject": subject,
                "body": body,
                "email_type": args.email_type,
                "recipient_context": args.recipient_context,
            }
            _email_drafts.append(draft)

            return ToolResult(success=True, data=draft)
        except Exception as e:
            return ToolResult(success=False, error=f"Email drafting failed: {str(e)}")
