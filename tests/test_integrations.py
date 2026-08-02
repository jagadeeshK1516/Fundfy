"""Tests for integrations — Gmail, Calendar, Drive services (mocked)."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from fundfy.integrations.gmail import GmailService
from fundfy.integrations.calendar import CalendarService
from fundfy.integrations.drive import DriveService


class TestGmailService:
    """Tests for GmailService with mocked Google API."""

    def setup_method(self):
        """Set up mock credentials and service."""
        self.mock_credentials = MagicMock()
        with patch("googleapiclient.discovery.build") as mock_build:
            self.mock_service = MagicMock()
            mock_build.return_value = self.mock_service
            self.gmail = GmailService(self.mock_credentials)

    def test_send_email(self):
        """Test sending an email."""
        self.mock_service.users().messages().send().execute.return_value = {
            "id": "msg-123",
            "labelIds": ["SENT"],
        }
        result = self.gmail.send_email("test@example.com", "Hello", "Body text")
        assert result["id"] == "msg-123"

    def test_read_emails(self):
        """Test reading emails."""
        self.mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg-1"}, {"id": "msg-2"}]
        }
        self.mock_service.users().messages().get().execute.return_value = {
            "id": "msg-1",
            "snippet": "Hello there",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test"},
                    {"name": "From", "value": "sender@test.com"},
                    {"name": "Date", "value": "2024-01-01"},
                ]
            },
        }
        emails = self.gmail.read_emails(query="is:unread", max_results=5)
        assert len(emails) == 2

    def test_create_draft(self):
        """Test creating a draft."""
        self.mock_service.users().drafts().create().execute.return_value = {
            "id": "draft-123",
            "message": {"id": "msg-456"},
        }
        result = self.gmail.create_draft("test@example.com", "Draft", "Draft body")
        assert result["id"] == "draft-123"

    def test_list_drafts(self):
        """Test listing drafts."""
        self.mock_service.users().drafts().list().execute.return_value = {
            "drafts": [{"id": "draft-1"}, {"id": "draft-2"}]
        }
        result = self.gmail.list_drafts()
        assert len(result) == 2

    def test_send_draft(self):
        """Test sending a draft."""
        self.mock_service.users().drafts().send().execute.return_value = {
            "id": "msg-sent-1",
        }
        result = self.gmail.send_draft("draft-123")
        assert result["id"] == "msg-sent-1"


class TestCalendarService:
    """Tests for CalendarService with mocked Google API."""

    def setup_method(self):
        """Set up mock credentials and service."""
        self.mock_credentials = MagicMock()
        with patch("googleapiclient.discovery.build") as mock_build:
            self.mock_service = MagicMock()
            mock_build.return_value = self.mock_service
            self.calendar = CalendarService(self.mock_credentials)

    def test_create_event(self):
        """Test creating a calendar event."""
        self.mock_service.events().insert().execute.return_value = {
            "id": "event-123",
            "htmlLink": "https://calendar.google.com/event/123",
            "hangoutLink": "https://meet.google.com/abc-def",
        }
        result = self.calendar.create_event(
            summary="Team Standup",
            start="2024-01-15T09:00:00Z",
            end="2024-01-15T09:30:00Z",
            attendees=["alice@test.com"],
            meet_link=True,
        )
        assert result["id"] == "event-123"
        assert "hangoutLink" in result

    def test_list_events(self):
        """Test listing calendar events."""
        self.mock_service.events().list().execute.return_value = {
            "items": [
                {"id": "event-1", "summary": "Meeting A"},
                {"id": "event-2", "summary": "Meeting B"},
            ]
        }
        events = self.calendar.list_events(
            time_min="2024-01-01T00:00:00Z",
            time_max="2024-01-31T23:59:59Z",
        )
        assert len(events) == 2

    def test_check_availability(self):
        """Test checking availability."""
        self.mock_service.freebusy().query().execute.return_value = {
            "calendars": {
                "primary": {
                    "busy": [
                        {"start": "2024-01-15T09:00:00Z", "end": "2024-01-15T10:00:00Z"}
                    ]
                }
            }
        }
        busy = self.calendar.check_availability(
            "2024-01-15T00:00:00Z", "2024-01-15T23:59:59Z"
        )
        assert len(busy) == 1

    def test_delete_event(self):
        """Test deleting a calendar event."""
        self.mock_service.events().delete().execute.return_value = None
        self.calendar.delete_event("event-123")
        self.mock_service.events().delete.assert_called()


class TestDriveService:
    """Tests for DriveService with mocked Google API."""

    def setup_method(self):
        """Set up mock credentials and service."""
        self.mock_credentials = MagicMock()
        with patch("googleapiclient.discovery.build") as mock_build:
            self.mock_service = MagicMock()
            mock_build.return_value = self.mock_service
            self.drive = DriveService(self.mock_credentials)

    def test_create_folder(self):
        """Test creating a folder."""
        # Mock finding the Fundfy folder
        self.mock_service.files().list().execute.return_value = {
            "files": [{"id": "fundfy-folder-id", "name": "Fundfy"}]
        }
        self.mock_service.files().create().execute.return_value = {"id": "new-folder-id"}

        result = self.drive.create_folder("Documents")
        assert result == "new-folder-id"

    def test_list_files(self):
        """Test listing files."""
        self.mock_service.files().list().execute.return_value = {
            "files": [
                {"id": "file-1", "name": "plan.pdf"},
                {"id": "file-2", "name": "deck.pptx"},
            ]
        }
        files = self.drive.list_files("folder-123")
        assert len(files) == 2

    def test_get_share_link(self):
        """Test getting a share link."""
        self.mock_service.permissions().create().execute.return_value = {}
        self.mock_service.files().get().execute.return_value = {
            "webViewLink": "https://drive.google.com/file/d/123/view"
        }
        link = self.drive.get_share_link("file-123")
        assert "drive.google.com" in link
