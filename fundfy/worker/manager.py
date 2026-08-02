"""Background job manager — enqueues jobs and tracks status."""

import json
import uuid

import structlog

from fundfy.config import settings
from fundfy.models.job import BackgroundJob

logger = structlog.stdlib.get_logger(__name__)


class BackgroundJobManager:
    """Manages background job enqueueing and status tracking."""

    async def enqueue_execution(self, business_id: str, objective: str, context: str = "") -> str:
        """Enqueue an execution plan job. Returns job_id."""
        job_id = str(uuid.uuid4())
        await self._create_job_record(job_id, "execute_plan", {
            "business_id": business_id,
            "objective": objective,
            "context": context,
        })

        if settings.redis_url:
            try:
                from arq import create_pool
                from fundfy.worker.settings import _parse_redis_settings
                pool = await create_pool(_parse_redis_settings())
                await pool.enqueue_job(
                    "task_execute_plan",
                    job_id, business_id, objective, context,
                )
                await pool.close()
            except Exception as e:
                logger.error("enqueue_failed", job_id=job_id, error=str(e))
                await self._update_status(job_id, "failed", error=str(e))

        return job_id

    async def enqueue_document_generation(self, business_id: str, doc_type: str, context: str = "") -> str:
        """Enqueue a document generation job. Returns job_id."""
        job_id = str(uuid.uuid4())
        await self._create_job_record(job_id, "generate_document", {
            "business_id": business_id,
            "doc_type": doc_type,
            "context": context,
        })

        if settings.redis_url:
            try:
                from arq import create_pool
                from fundfy.worker.settings import _parse_redis_settings
                pool = await create_pool(_parse_redis_settings())
                await pool.enqueue_job(
                    "task_generate_document",
                    job_id, business_id, doc_type, context,
                )
                await pool.close()
            except Exception as e:
                logger.error("enqueue_failed", job_id=job_id, error=str(e))
                await self._update_status(job_id, "failed", error=str(e))

        return job_id

    async def get_job_status(self, job_id: str) -> dict | None:
        """Get the status of a job by ID."""
        from fundfy.db import async_session

        async with async_session() as session:
            job = await session.get(BackgroundJob, job_id)
            if not job:
                return None
            return {
                "id": job.id,
                "job_type": job.job_type,
                "status": job.status,
                "result": json.loads(job.result_json) if job.result_json else None,
                "error": job.error,
                "created_at": job.created_at.isoformat() if job.created_at else None,
            }

    async def _create_job_record(self, job_id: str, job_type: str, params: dict) -> None:
        """Create a job record in the database."""
        from fundfy.db import async_session

        async with async_session() as session:
            job = BackgroundJob(
                id=job_id,
                job_type=job_type,
                status="queued",
                params_json=json.dumps(params),
            )
            session.add(job)
            await session.commit()

    async def _update_status(self, job_id: str, status: str, error: str | None = None) -> None:
        """Update a job's status."""
        from fundfy.db import async_session

        async with async_session() as session:
            job = await session.get(BackgroundJob, job_id)
            if job:
                job.status = status
                if error:
                    job.error = error
                await session.commit()
