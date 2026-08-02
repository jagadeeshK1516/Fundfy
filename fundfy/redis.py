"""Redis client module with async support."""

import json
from typing import Any

from fundfy.config import settings

_redis_pool = None


class NoOpRedis:
    """No-op Redis stub for when Redis is not configured."""

    async def get(self, key: str) -> None:
        return None

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        pass

    async def delete(self, key: str) -> None:
        pass

    async def ping(self) -> bool:
        return False

    async def incr(self, key: str) -> int:
        return 0

    async def expire(self, key: str, seconds: int) -> None:
        pass

    async def ttl(self, key: str) -> int:
        return -2

    async def close(self) -> None:
        pass


async def init_redis():
    """Initialize the Redis connection pool."""
    global _redis_pool
    if settings.redis_url:
        import redis.asyncio as aioredis
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    else:
        _redis_pool = NoOpRedis()


async def close_redis():
    """Close the Redis connection pool."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None


def get_redis():
    """Get the Redis client instance."""
    if _redis_pool is None:
        return NoOpRedis()
    return _redis_pool


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set a cache value with TTL."""
    client = get_redis()
    serialized = json.dumps(value) if not isinstance(value, str) else value
    await client.set(key, serialized, ex=ttl)


async def cache_get(key: str) -> Any | None:
    """Get a cache value."""
    client = get_redis()
    result = await client.get(key)
    if result is None:
        return None
    try:
        return json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return result


async def cache_delete(key: str) -> None:
    """Delete a cache value."""
    client = get_redis()
    await client.delete(key)
