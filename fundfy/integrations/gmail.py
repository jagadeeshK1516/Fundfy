"""Gmail integration using Google API."""

import base64
from email.mime.text import MIMEText
from typing import Any


class GmailService:
    """Wraps the Google Gmail API for sending and reading emails."""

    def __init__(self, credentials: Any):
        """Initialize with Google OAuth credentials or access token."""
        from googleapiclient.discovery import build

        self._service = build("gmail", "v1", credentials=credentials)

    def send_email(self, to: str, subject: str, body: str) -> dict:
        """Send an email."""
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = self._service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        return result

    def read_emails(self, query: str = "", max_results: int = 10) -> list[dict]:
        """Read emails matching a query."""
        results = self._service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
        messages = results.get("messages", [])
        emails = []
        for msg in messages:
            detail = self._service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            ).execute()
            headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
            emails.append({
                "id": msg["id"],
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "snippet": detail.get("snippet", ""),
            })
        return emails

    def get_email(self, email_id: str) -> dict:
        """Get a single email by ID."""
        detail = self._service.users().messages().get(
            userId="me", id=email_id, format="full"
        ).execute()
        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        return {
            "id": detail["id"],
            "subject": headers.get("Subject", ""),
            "from": headers.get("From", ""),
            "date": headers.get("Date", ""),
            "snippet": detail.get("snippet", ""),
            "body": detail.get("snippet", ""),
        }

    def create_draft(self, to: str, subject: str, body: str) -> dict:
        """Create an email draft."""
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = self._service.users().drafts().create(
            userId="me", body={"message": {"raw": raw}}
        ).execute()
        return result

    def list_drafts(self) -> list[dict]:
        """List all drafts."""
        results = self._service.users().drafts().list(userId="me").execute()
        return results.get("drafts", [])

    def send_draft(self, draft_id: str) -> dict:
        """Send a draft by ID."""
        result = self._service.users().drafts().send(
            userId="me", body={"id": draft_id}
        ).execute()
        return result
