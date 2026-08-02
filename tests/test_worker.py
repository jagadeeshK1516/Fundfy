"""Test background worker infrastructure."""

import pytest
from unittest.mock import AsyncMock, patch

from fundfy.worker.manager import BackgroundJobManager


@pytest.mark.asyncio
async def test_job_manager_enqueue_execution():
    """Job manager creates a job record for execution."""
    from fundfy.db import init_db
    await init_db()

    manager = BackgroundJobManager()
    job_id = await manager.enqueue_execution("biz-1", "Validate idea", "B2B SaaS")

    assert job_id is not None
    assert len(job_id) > 0

    # Check status
    status = await manager.get_job_status(job_id)
    assert status is not None
    assert status["job_type"] == "execute_plan"
    assert status["status"] == "queued"


@pytest.mark.asyncio
async def test_job_manager_enqueue_document():
    """Job manager creates a job record for document generation."""
    from fundfy.db import init_db
    await init_db()

    manager = BackgroundJobManager()
    job_id = await manager.enqueue_document_generation("biz-1", "business_plan", "AI startup")

    assert job_id is not None

    status = await manager.get_job_status(job_id)
    assert status is not None
    assert status["job_type"] == "generate_document"
    assert status["status"] == "queued"


@pytest.mark.asyncio
async def test_job_manager_nonexistent_job():
    """Job manager returns None for non-existent job."""
    from fundfy.db import init_db
    await init_db()

    manager = BackgroundJobManager()
    status = await manager.get_job_status("nonexistent-id")
    assert status is None
