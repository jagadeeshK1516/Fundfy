"""Business model."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from fundfy.models import Base


class Business(Base):
    """Represents a business entity tied to a founder."""

    __tablename__ = "businesses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    founder_id: Mapped[str] = mapped_column(String, ForeignKey("founders.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    industry: Mapped[str] = mapped_column(String, nullable=True)
    stage: Mapped[str] = mapped_column(String, nullable=True)
    goals_json: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
