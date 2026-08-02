"""Google OAuth2 integration — consent URL, token exchange, refresh, and encryption."""

import uuid
from datetime import datetime, timedelta

from cryptography.fernet import Fernet
from sqlalchemy import select, delete

from fundfy.config import settings
from fundfy.db import async_session
from fundfy.models.oauth_token import OAuthToken

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
]


def _get_fernet() -> Fernet:
    """Get a Fernet instance for encryption/decryption."""
    key = settings.encryption_key or Fernet.generate_key().decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(token: str) -> str:
    """Encrypt a token string."""
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt an encrypted token string."""
    return _get_fernet().decrypt(encrypted_token.encode()).decode()


def generate_consent_url(state: str | None = None) -> str:
    """Generate Google OAuth consent URL."""
    from urllib.parse import urlencode

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    if state:
        params["state"] = state
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


async def exchange_code_for_tokens(code: str, founder_id: str) -> dict:
    """Exchange an authorization code for tokens and store them encrypted."""
    import httpx

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token", "")
    expires_in = token_data.get("expires_in", 3600)

    # Store encrypted tokens
    async with async_session() as session:
        # Remove existing tokens for this provider
        await session.execute(
            delete(OAuthToken).where(
                OAuthToken.founder_id == founder_id,
                OAuthToken.provider == "google",
            )
        )

        oauth_token = OAuthToken(
            id=str(uuid.uuid4()),
            founder_id=founder_id,
            provider="google",
            access_token_encrypted=encrypt_token(access_token),
            refresh_token_encrypted=encrypt_token(refresh_token) if refresh_token else None,
            scopes=" ".join(SCOPES),
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
        )
        session.add(oauth_token)
        await session.commit()

    return {"status": "connected", "scopes": SCOPES}


async def refresh_access_token(founder_id: str) -> str | None:
    """Refresh the access token using the refresh token."""
    import httpx

    async with async_session() as session:
        result = await session.execute(
            select(OAuthToken).where(
                OAuthToken.founder_id == founder_id,
                OAuthToken.provider == "google",
            )
        )
        token_record = result.scalar_one_or_none()
        if not token_record or not token_record.refresh_token_encrypted:
            return None

        refresh_token = decrypt_token(token_record.refresh_token_encrypted)

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()

    new_access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", 3600)

    # Update stored token
    async with async_session() as session:
        result = await session.execute(
            select(OAuthToken).where(
                OAuthToken.founder_id == founder_id,
                OAuthToken.provider == "google",
            )
        )
        token_record = result.scalar_one_or_none()
        if token_record:
            token_record.access_token_encrypted = encrypt_token(new_access_token)
            token_record.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            await session.commit()

    return new_access_token


async def get_access_token(founder_id: str) -> str | None:
    """Get a valid access token, refreshing if expired."""
    async with async_session() as session:
        result = await session.execute(
            select(OAuthToken).where(
                OAuthToken.founder_id == founder_id,
                OAuthToken.provider == "google",
            )
        )
        token_record = result.scalar_one_or_none()
        if not token_record:
            return None

        # Check expiration
        if token_record.expires_at and token_record.expires_at < datetime.utcnow():
            return await refresh_access_token(founder_id)

        return decrypt_token(token_record.access_token_encrypted)


async def get_connection_status(founder_id: str) -> dict:
    """Check if Google is connected for a founder."""
    async with async_session() as session:
        result = await session.execute(
            select(OAuthToken).where(
                OAuthToken.founder_id == founder_id,
                OAuthToken.provider == "google",
            )
        )
        token_record = result.scalar_one_or_none()
        if not token_record:
            return {"connected": False}
        return {
            "connected": True,
            "scopes": token_record.scopes.split(" ") if token_record.scopes else [],
            "expires_at": token_record.expires_at.isoformat() if token_record.expires_at else None,
        }


async def disconnect(founder_id: str) -> bool:
    """Revoke tokens and remove from DB."""
    async with async_session() as session:
        result = await session.execute(
            select(OAuthToken).where(
                OAuthToken.founder_id == founder_id,
                OAuthToken.provider == "google",
            )
        )
        token_record = result.scalar_one_or_none()
        if not token_record:
            return False

        # Try to revoke at Google (best-effort)
        try:
            import httpx
            access_token = decrypt_token(token_record.access_token_encrypted)
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": access_token},
                )
        except Exception:
            pass  # Best-effort revocation

        await session.execute(
            delete(OAuthToken).where(
                OAuthToken.founder_id == founder_id,
                OAuthToken.provider == "google",
            )
        )
        await session.commit()
    return True
