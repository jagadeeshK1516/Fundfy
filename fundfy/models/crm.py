"""CRM models — Contact and Interaction."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from fundfy.models import Base


class Contact(Base):
    """Represents a CRM contact."""

    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    founder_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    company: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String, default="other")  # investor/mentor/partner/other
    pipeline_stage: Mapped[str] = mapped_column(String, default="lead")  # lead/contacted/meeting/proposal/negotiation/closed_won/closed_lost
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Interaction(Base):
    """Represents an interaction with a CRM contact."""

    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contact_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    founder_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, default="note")  # email/meeting/call/note
    summary: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
