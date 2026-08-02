"""Email approval model for human-in-the-loop email sending."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from fundfy.models import Base


class EmailApproval(Base):
    """Tracks emails that require founder approval before sending."""

    __tablename__ = "email_approvals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    founder_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    to: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending/approved/rejected/sent
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
