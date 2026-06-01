import json

import redis.asyncio as aioredis
from app.core.settings import settings

redis_client: aioredis.Redis | None = None


async def init_redis() -> None:
    """Initialize Redis connection on app startup."""
    global redis_client

    redis_client = aioredis.from_url(
        settings.REDIS_URL.get_secret_value(),
        encoding="utf-8",
        decode_responses=True,
        ssl_cert_reqs=None,
    )


async def close_redis() -> None:
    """Close Redis connection on app shutdown."""
    global redis_client
    if redis_client:
        await redis_client.aclose()


async def get_redis() -> aioredis.Redis:
    """Get the Redis client."""
    if redis_client is None:
        raise RuntimeError("Redis is not initialized. Call init_redis() first.")

    return redis_client


async def set_cache(key: str, value: dict, ttl: int = 3600) -> None:
    """Store a dictionary in Redis as JSON"""
    redis = await get_redis()
    await redis.set(key, json.dumps(value), ex=ttl)


async def get_cache(key: str) -> dict | None:
    """Retrieve a dictionary from Redis"""
    redis = await get_redis()
    data = await redis.get(key)

    if data is None:
        return None

    return json.loads(data)


async def delete_cache(key: str) -> None:
    """Delete a key from Redis"""
    redis = await get_redis()
    await redis.delete(key)
