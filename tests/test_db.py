"""Test database models and initialization."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fundfy.models import Base
from fundfy.models.founder import Founder
from fundfy.models.email_draft import EmailDraft
from fundfy.models.generated_file import GeneratedFile
from fundfy.models.job import BackgroundJob


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


@pytest.mark.asyncio
async def test_founder_with_password_and_role():
    """Founder model supports password_hash and role fields."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        founder = Founder(
            id="test-id-2",
            name="Bob",
            email="bob@example.com",
            password_hash="hashed_value",
            role="admin",
        )
        session.add(founder)
        await session.commit()

    async with session_factory() as session:
        result = await session.get(Founder, "test-id-2")
        assert result.password_hash == "hashed_value"
        assert result.role == "admin"

    await engine.dispose()


@pytest.mark.asyncio
async def test_email_draft_model():
    """EmailDraft model can be created and retrieved."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        founder = Founder(id="f1", name="Founder", email="f@example.com")
        session.add(founder)
        await session.commit()

        draft = EmailDraft(
            id="draft-1",
            founder_id="f1",
            email_type="investor_outreach",
            subject="Hello Investor",
            body="We are building...",
        )
        session.add(draft)
        await session.commit()

    async with session_factory() as session:
        result = await session.get(EmailDraft, "draft-1")
        assert result is not None
        assert result.email_type == "investor_outreach"
        assert result.subject == "Hello Investor"

    await engine.dispose()


@pytest.mark.asyncio
async def test_background_job_model():
    """BackgroundJob model can be created and updated."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        job = BackgroundJob(
            id="job-1",
            job_type="execute_plan",
            status="queued",
            params_json='{"objective": "test"}',
        )
        session.add(job)
        await session.commit()

    async with session_factory() as session:
        result = await session.get(BackgroundJob, "job-1")
        assert result is not None
        assert result.status == "queued"
        result.status = "completed"
        result.result_json = '{"tasks": []}'
        await session.commit()

    async with session_factory() as session:
        result = await session.get(BackgroundJob, "job-1")
        assert result.status == "completed"
        assert result.result_json == '{"tasks": []}'

    await engine.dispose()
