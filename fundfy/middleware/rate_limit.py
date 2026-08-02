"""Redis-based sliding-window rate limiting middleware."""

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from fundfy.config import settings

logger = structlog.stdlib.get_logger(__name__)

# Per-route rate limits (requests per minute)
ROUTE_LIMITS: dict[str, int] = {
    "/api/chat": 60,
    "/api/documents/generate": 10,
    "/api/execute": 5,
}
DEFAULT_LIMIT = 120


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter backed by Redis."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not settings.rate_limit_enabled:
            return await call_next(request)

        # Only rate-limit API routes
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)

        from fundfy.redis import get_redis

        redis = get_redis()

        try:
            # Determine identifier
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                identifier = f"auth:{auth_header[7:20]}"
            else:
                identifier = f"ip:{request.client.host if request.client else 'unknown'}"

            # Determine limit for this route
            limit = DEFAULT_LIMIT
            for route_prefix, route_limit in ROUTE_LIMITS.items():
                if path.startswith(route_prefix):
                    limit = route_limit
                    break

            # Sliding window counter
            window_key = f"ratelimit:{identifier}:{path}:{int(time.time()) // 60}"
            current = await redis.incr(window_key)
            if current == 1:
                await redis.expire(window_key, 60)

            if current > limit:
                retry_after = 60 - (int(time.time()) % 60)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={"Retry-After": str(retry_after)},
                )
        except Exception:
            # Fail-open: if Redis is down, allow the request
            logger.warning("rate_limit_redis_error", path=path)

        return await call_next(request)
