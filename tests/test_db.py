"""Test database models and initialization."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fundfy.models import Base
from fundfy.models.founder import Founder


@pytest.mark.asyncio
async def test_create_founder_roundtrip():
    """Create an in-memory SQLite DB, insert a founder, and verify retrieval."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        founder = Founder(id="test-id-1", name="Alice", email="alice@example.com")
        session.add(founder)
        await session.commit()

    async with session_factory() as session:
        result = await session.get(Founder, "test-id-1")
        assert result is not None
        assert result.name == "Alice"
        assert result.email == "alice@example.com"

    await engine.dispose()
