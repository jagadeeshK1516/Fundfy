"""Health check and readiness endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from fundfy.config import settings

router = APIRouter(tags=["health"])


async def _check_database() -> dict:
    """Check PostgreSQL/SQLite connectivity."""
    try:
        from fundfy.db import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _check_redis() -> dict:
    """Check Redis connectivity."""
    if not settings.redis_url:
        return {"status": "not_configured"}
    try:
        from fundfy.redis import get_redis
        redis = get_redis()
        result = await redis.ping()
        if result:
            return {"status": "healthy"}
        return {"status": "unhealthy", "error": "ping failed"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _check_chromadb() -> dict:
    """Check ChromaDB connectivity."""
    if not settings.chroma_server_url:
        return {"status": "local"}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.chroma_server_url}/api/v1/heartbeat")
            if resp.status_code == 200:
                return {"status": "healthy"}
            return {"status": "unhealthy", "error": f"status {resp.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.get("/health")
async def health():
    """Health check — always returns 200 with component statuses."""
    db_status = await _check_database()
    redis_status = await _check_redis()
    chromadb_status = await _check_chromadb()

    return {
        "status": "healthy",
        "components": {
            "database": db_status,
            "redis": redis_status,
            "chromadb": chromadb_status,
        },
    }


@router.get("/ready")
async def readiness():
    """Readiness probe — returns 503 if any critical component is down."""
    db_status = await _check_database()
    redis_status = await _check_redis()

    # Database must be healthy
    if db_status.get("status") != "healthy":
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "database unhealthy"},
        )

    # Redis must be healthy (if configured)
    if settings.redis_url and redis_status.get("status") != "healthy":
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "redis unhealthy"},
        )

    return {"status": "ready"}
