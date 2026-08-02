"""JWT token creation and validation."""

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from pydantic import BaseModel

from fundfy.config import settings


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""

    founder_id: str
    role: str = "founder"
    exp: Optional[float] = None


def create_access_token(founder_id: str, role: str = "founder", expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)

    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "founder_id": founder_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return TokenPayload(
            founder_id=payload["founder_id"],
            role=payload.get("role", "founder"),
            exp=payload.get("exp"),
        )
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")
