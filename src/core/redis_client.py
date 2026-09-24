import logging

import redis.asyncio as redis

from src.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def check_redis_connection() -> bool:
    try:
        await get_redis_client().ping()
        return True
    except Exception:
        logger.exception("Redis connection check failed")
        return False


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
