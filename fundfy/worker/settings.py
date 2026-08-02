"""ARQ worker settings."""

from arq.connections import RedisSettings

from fundfy.config import settings
from fundfy.worker.tasks import task_execute_plan, task_generate_document


def _parse_redis_settings() -> RedisSettings:
    """Parse REDIS_URL into ARQ RedisSettings."""
    if not settings.redis_url:
        return RedisSettings()

    # Parse redis://host:port/db
    url = settings.redis_url
    if url.startswith("redis://"):
        url = url[8:]

    parts = url.split("/")
    host_port = parts[0]
    database = int(parts[1]) if len(parts) > 1 else 0

    if ":" in host_port:
        host, port = host_port.rsplit(":", 1)
        port = int(port)
    else:
        host = host_port
        port = 6379

    return RedisSettings(host=host, port=port, database=database)


class WorkerSettings:
    """ARQ WorkerSettings class."""

    functions = [task_execute_plan, task_generate_document]
    redis_settings = _parse_redis_settings()
    job_timeout = settings.worker_job_timeout
    max_tries = settings.worker_max_retries
    retry_jobs = True
