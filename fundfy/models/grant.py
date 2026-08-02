"""Grant model for the grant database."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from fundfy.models import Base


class Grant(Base):
    """Represents a grant opportunity."""

    __tablename__ = "grants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    amount_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    amount_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    deadline: Mapped[str | None] = mapped_column(String, nullable=True)
    eligibility_criteria: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    industry_focus: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    application_url: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    region: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="open")  # open/closed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
