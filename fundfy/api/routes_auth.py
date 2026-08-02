"""Authentication API routes."""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from fundfy.auth.jwt import create_access_token, decode_access_token
from fundfy.db import async_session
from fundfy.models.founder import Founder

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    """Registration request."""
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    """Login request."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    founder_id: str


class RefreshRequest(BaseModel):
    """Token refresh request."""
    token: str


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    import bcrypt as _bcrypt
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    import bcrypt as _bcrypt
    return _bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register a new founder."""
    from sqlalchemy import select

    async with async_session() as session:
        # Check if email already exists
        result = await session.execute(
            select(Founder).where(Founder.email == request.email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        # Create founder
        founder = Founder(
            id=str(uuid.uuid4()),
            name=request.name,
            email=request.email,
            password_hash=_hash_password(request.password),
            role="founder",
        )
        session.add(founder)
        await session.commit()

        token = create_access_token(founder.id, founder.role)
        return TokenResponse(access_token=token, founder_id=founder.id)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login with email and password."""
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(
            select(Founder).where(Founder.email == request.email)
        )
        founder = result.scalar_one_or_none()

        if not founder or not founder.password_hash:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not _verify_password(request.password, founder.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(founder.id, founder.role)
        return TokenResponse(access_token=token, founder_id=founder.id)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """Refresh an access token."""
    try:
        payload = decode_access_token(request.token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    new_token = create_access_token(payload.founder_id, payload.role)
    return TokenResponse(access_token=new_token, founder_id=payload.founder_id)
