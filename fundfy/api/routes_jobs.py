"""Job status API routes."""

from fastapi import APIRouter, HTTPException

from fundfy.worker.manager import BackgroundJobManager

router = APIRouter(prefix="/api", tags=["jobs"])

_job_manager = BackgroundJobManager()


def get_job_manager() -> BackgroundJobManager:
    """Get the job manager instance."""
    return _job_manager


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a background job."""
    manager = get_job_manager()
    status = await manager.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status
