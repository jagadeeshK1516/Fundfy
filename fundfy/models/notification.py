"""Notification model."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from fundfy.models import Base


class Notification(Base):
    """Represents a notification for a founder."""

    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    founder_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)  # email_reply/meeting_reminder/grant_deadline/job_complete/document_ready
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[str] = mapped_column(Text, default="{}")  # JSON
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
