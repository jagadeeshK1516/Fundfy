"""Google Calendar tools for the AI agent."""

from typing import Any

from pydantic import BaseModel

from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult


class ScheduleMeetingArgs(BaseModel):
    """Arguments for schedule_meeting tool."""

    summary: str
    start: str  # ISO format
    end: str  # ISO format
    attendees: list[str] = []
    meet_link: bool = True
    founder_id: str


class CheckAvailabilityArgs(BaseModel):
    """Arguments for check_availability tool."""

    time_min: str  # ISO format
    time_max: str  # ISO format
    founder_id: str


class ListUpcomingMeetingsArgs(BaseModel):
    """Arguments for list_upcoming_meetings tool."""

    max_results: int = 10
    founder_id: str


class ScheduleMeetingTool(BaseTool):
    """Creates a calendar event with optional Google Meet link."""

    name = "schedule_meeting"
    description = "Schedule a meeting on Google Calendar with optional Google Meet link and attendees."
    args_schema = ScheduleMeetingArgs

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Create a calendar event."""
        args = ScheduleMeetingArgs(**kwargs)

        try:
            from fundfy.integrations.google_auth import get_access_token
            from google.oauth2.credentials import Credentials
            from fundfy.integrations.calendar import CalendarService

            access_token = await get_access_token(args.founder_id)
            if not access_token:
                return ToolResult(
                    success=False,
                    error="Google account not connected. Please connect via Integrations settings.",
                )

            credentials = Credentials(token=access_token)
            calendar = CalendarService(credentials)
            event = calendar.create_event(
                summary=args.summary,
                start=args.start,
                end=args.end,
                attendees=args.attendees,
                meet_link=args.meet_link,
            )

            return ToolResult(
                success=True,
                data={
                    "event_id": event.get("id"),
                    "html_link": event.get("htmlLink"),
                    "meet_link": event.get("hangoutLink", ""),
                    "summary": args.summary,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to schedule meeting: {str(e)}")


class CheckAvailabilityTool(BaseTool):
    """Checks Google Calendar free/busy to find available time slots."""

    name = "check_availability"
    description = "Check Google Calendar availability / free-busy for a time range."
    args_schema = CheckAvailabilityArgs

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Check availability."""
        args = CheckAvailabilityArgs(**kwargs)

        try:
            from fundfy.integrations.google_auth import get_access_token
            from google.oauth2.credentials import Credentials
            from fundfy.integrations.calendar import CalendarService

            access_token = await get_access_token(args.founder_id)
            if not access_token:
                return ToolResult(
                    success=False,
                    error="Google account not connected.",
                )

            credentials = Credentials(token=access_token)
            calendar = CalendarService(credentials)
            busy_slots = calendar.check_availability(args.time_min, args.time_max)

            return ToolResult(
                success=True,
                data={"busy_slots": busy_slots, "time_min": args.time_min, "time_max": args.time_max},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to check availability: {str(e)}")


class ListUpcomingMeetingsTool(BaseTool):
    """Fetches upcoming calendar events."""

    name = "list_upcoming_meetings"
    description = "List upcoming meetings from Google Calendar."
    args_schema = ListUpcomingMeetingsArgs

    async def execute(self, **kwargs: Any) -> ToolResult:
        """List upcoming events."""
        args = ListUpcomingMeetingsArgs(**kwargs)

        try:
            from datetime import datetime, timedelta

            from fundfy.integrations.google_auth import get_access_token
            from google.oauth2.credentials import Credentials
            from fundfy.integrations.calendar import CalendarService

            access_token = await get_access_token(args.founder_id)
            if not access_token:
                return ToolResult(
                    success=False,
                    error="Google account not connected.",
                )

            credentials = Credentials(token=access_token)
            calendar = CalendarService(credentials)
            now = datetime.utcnow().isoformat() + "Z"
            future = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
            events = calendar.list_events(time_min=now, time_max=future, max_results=args.max_results)

            return ToolResult(success=True, data={"events": events, "count": len(events)})
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to list meetings: {str(e)}")
