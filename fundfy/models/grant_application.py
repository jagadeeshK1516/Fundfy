"""Grant application tracking model."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from fundfy.models import Base


class GrantApplication(Base):
    """Tracks a founder's grant application status."""

    __tablename__ = "grant_applications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    founder_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    grant_id: Mapped[str] = mapped_column(String, nullable=False)
    business_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="discovered")  # discovered/applying/submitted/approved/rejected
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
