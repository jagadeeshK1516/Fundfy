"""OAuth token model for storing encrypted tokens."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from fundfy.models import Base


class OAuthToken(Base):
    """Stores encrypted OAuth tokens for external service integrations."""

    __tablename__ = "oauth_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    founder_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "google"
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    scopes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
