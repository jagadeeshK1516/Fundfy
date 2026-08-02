"""Tests for the notification service."""

import pytest

from fundfy.integrations.notifications import NotificationService


@pytest.fixture
def notification_service():
    """Create a NotificationService instance."""
    return NotificationService()


class TestNotificationService:
    """Tests for notification pub/sub."""

    async def test_publish_notification(self, notification_service):
        """Test publishing a notification."""
        result = await notification_service.publish(
            founder_id="test-founder-1",
            type="document_ready",
            title="Document Ready",
            body="Your pitch deck has been generated.",
            data={"document_id": "doc-123"},
        )
        assert result["type"] == "document_ready"
        assert result["title"] == "Document Ready"
        assert result["read"] is False
        assert result["data"]["document_id"] == "doc-123"
        assert result["id"] is not None

    async def test_list_recent_notifications(self, notification_service):
        """Test listing recent notifications."""
        await notification_service.publish(
            founder_id="test-founder-1",
            type="job_complete",
            title="Job Complete",
            body="Your analysis is ready.",
        )
        await notification_service.publish(
            founder_id="test-founder-1",
            type="email_reply",
            title="Email Reply",
            body="You have a new email reply.",
        )

        notifications = await notification_service.list_recent("test-founder-1")
        assert len(notifications) == 2

    async def test_mark_as_read(self, notification_service):
        """Test marking a notification as read."""
        notif = await notification_service.publish(
            founder_id="test-founder-1",
            type="meeting_reminder",
            title="Meeting in 15 mins",
            body="Team standup is starting soon.",
        )
        success = await notification_service.mark_as_read(notif["id"])
        assert success is True

    async def test_mark_nonexistent_as_read(self, notification_service):
        """Test marking a nonexistent notification as read."""
        success = await notification_service.mark_as_read("nonexistent-id")
        assert success is False

    async def test_notifications_filtered_by_founder(self, notification_service):
        """Test that notifications are filtered by founder_id."""
        await notification_service.publish(
            founder_id="founder-A",
            type="document_ready",
            title="For A",
            body="Doc for A",
        )
        await notification_service.publish(
            founder_id="founder-B",
            type="document_ready",
            title="For B",
            body="Doc for B",
        )

        a_notifs = await notification_service.list_recent("founder-A")
        b_notifs = await notification_service.list_recent("founder-B")
        assert len(a_notifs) == 1
        assert a_notifs[0]["title"] == "For A"
        assert len(b_notifs) == 1
        assert b_notifs[0]["title"] == "For B"
