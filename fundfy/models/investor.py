"""Investor model for the investor database."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from fundfy.models import Base


class Investor(Base):
    """Represents an investor profile in the database."""

    __tablename__ = "investors"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    firm: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String, nullable=True)
    focus_areas: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    stage_preference: Mapped[str | None] = mapped_column(String, nullable=True)
    check_size_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_size_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    portfolio_companies: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
