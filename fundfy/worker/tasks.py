"""ARQ task definitions for long-running operations."""

import json
import structlog

logger = structlog.stdlib.get_logger(__name__)


async def task_execute_plan(ctx: dict, job_id: str, business_id: str, objective: str, context: str = "") -> dict:
    """Execute a plan asynchronously via the orchestrator."""
    logger.info("task_execute_plan.start", job_id=job_id, business_id=business_id)

    try:
        from fundfy.dependencies import get_orchestrator
        planner, dispatcher = get_orchestrator()

        tasks = await planner.plan(objective, context)
        results = await dispatcher.execute(tasks)

        result_data = {
            "business_id": business_id,
            "tasks": [
                {
                    "type": t.get("type", "unknown"),
                    "status": r.status,
                    "result": r.result,
                }
                for t, r in zip(tasks, results)
            ],
            "status": "completed",
        }

        # Update job status in DB
        await _update_job_status(job_id, "completed", result_json=json.dumps(result_data))
        return result_data

    except Exception as e:
        logger.error("task_execute_plan.failed", job_id=job_id, error=str(e))
        await _update_job_status(job_id, "failed", error=str(e))
        raise


async def task_generate_document(ctx: dict, job_id: str, business_id: str, doc_type: str, context: str = "") -> dict:
    """Generate a document asynchronously."""
    logger.info("task_generate_document.start", job_id=job_id, business_id=business_id)

    try:
        from fundfy.dependencies import get_document_generator
        generator = get_document_generator()

        result = await generator.generate(doc_type, business_id, context)
        result_data = {
            "business_id": result["business_id"],
            "doc_type": result["doc_type"],
            "title": result["title"],
            "content": result["content"],
        }

        await _update_job_status(job_id, "completed", result_json=json.dumps(result_data))
        return result_data

    except Exception as e:
        logger.error("task_generate_document.failed", job_id=job_id, error=str(e))
        await _update_job_status(job_id, "failed", error=str(e))
        raise


async def _update_job_status(job_id: str, status: str, result_json: str | None = None, error: str | None = None):
    """Update job status in the database."""
    try:
        from fundfy.db import async_session
        from fundfy.models.job import BackgroundJob

        async with async_session() as session:
            job = await session.get(BackgroundJob, job_id)
            if job:
                job.status = status
                if result_json:
                    job.result_json = result_json
                if error:
                    job.error = error
                await session.commit()
    except Exception as e:
        logger.error("job_status_update_failed", job_id=job_id, error=str(e))
