"""Google Calendar integration."""

from typing import Any


class CalendarService:
    """Wraps the Google Calendar API."""

    def __init__(self, credentials: Any):
        """Initialize with Google OAuth credentials."""
        from googleapiclient.discovery import build

        self._service = build("calendar", "v3", credentials=credentials)

    def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        attendees: list[str] | None = None,
        meet_link: bool = True,
    ) -> dict:
        """Create a calendar event with optional Google Meet link."""
        event_body: dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start, "timeZone": "UTC"},
            "end": {"dateTime": end, "timeZone": "UTC"},
        }
        if attendees:
            event_body["attendees"] = [{"email": a} for a in attendees]
        if meet_link:
            event_body["conferenceData"] = {
                "createRequest": {"requestId": f"fundfy-{summary[:20]}"}
            }

        result = self._service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1 if meet_link else 0,
        ).execute()
        return result

    def list_events(self, time_min: str, time_max: str, max_results: int = 20) -> list[dict]:
        """List calendar events in a time range."""
        results = self._service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        return results.get("items", [])

    def check_availability(self, time_min: str, time_max: str) -> list[dict]:
        """Check free/busy information for a time range."""
        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": "primary"}],
        }
        result = self._service.freebusy().query(body=body).execute()
        busy = result.get("calendars", {}).get("primary", {}).get("busy", [])
        return busy

    def delete_event(self, event_id: str) -> None:
        """Delete a calendar event."""
        self._service.events().delete(
            calendarId="primary", eventId=event_id
        ).execute()
