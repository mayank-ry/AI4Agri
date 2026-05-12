import redis.asyncio as redis
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

# Global Redis client instance
redis_client: redis.Redis | None = None

async def init_redis():
    """Initialize the async Redis client."""
    global redis_client
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("redis_connected")
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        # Depending on requirements, we might not want to raise here if Redis is optional,
        # but for a complete scaffold, we assume Redis is required.
        raise

async def close_redis():
    """Close the Redis client connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("redis_disconnected")

async def get_redis_client() -> redis.Redis:
    """Dependency to get the Redis client instance."""
    if redis_client is None:
        raise ConnectionError("Redis client is not initialized")
    return redis_client
