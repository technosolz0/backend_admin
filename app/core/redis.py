import json
import logging
import os
from typing import Optional, Any
import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection pool on application startup."""
    global redis_client
    try:
        redis_client = aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✅ Redis connected successfully.")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        redis_client = None


async def close_redis() -> None:
    """Close Redis connection pool on application shutdown."""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed.")


async def is_redis_connected() -> bool:
    """Check if Redis connection is active."""
    if not redis_client:
        return False
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False



async def get_cache(key: str) -> Optional[Any]:
    """Retrieve and JSON-deserialize cached value for key."""
    if not redis_client:
        return None
    try:
        data = await redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.warning(f"Redis get error for key '{key}': {e}")
        return None


async def set_cache(key: str, value: Any, ttl_seconds: int = 300) -> bool:
    """Serialize and store key-value pair in Redis with expiration (TTL)."""
    if not redis_client:
        return False
    try:
        serialized = json.dumps(value, default=str)
        await redis_client.set(key, serialized, ex=ttl_seconds)
        return True
    except Exception as e:
        logger.warning(f"Redis set error for key '{key}': {e}")
        return False


async def delete_cache(key: str) -> bool:
    """Delete a specific cache key."""
    if not redis_client:
        return False
    try:
        await redis_client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Redis delete error for key '{key}': {e}")
        return False


async def delete_cache_pattern(pattern: str) -> None:
    """Invalidate all keys matching a wildcard pattern (e.g. 'categories:*')."""
    if not redis_client:
        return
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching '{pattern}'")
    except Exception as e:
        logger.warning(f"Redis delete pattern error for '{pattern}': {e}")
