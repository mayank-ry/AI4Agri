import json
from typing import Any, Optional, Callable
import structlog
from app.services.redis_client import get_redis_client

logger = structlog.get_logger(__name__)

async def get_cached_or_fetch(
    key: str, 
    fetch_func: Callable, 
    expire_seconds: int = 3600
) -> Any:
    """
    Cache Strategy: Look-aside caching.
    1. Check Redis for the given key.
    2. If found, deserialize JSON and return (cache hit).
    3. If not found, execute the `fetch_func` to get fresh data (cache miss).
    4. Serialize and store the fresh data in Redis with the specified TTL.
    """
    try:
        redis = await get_redis_client()
        cached_data = await redis.get(key)
        
        if cached_data:
            logger.debug("cache_hit", key=key)
            return json.loads(cached_data)
            
        logger.debug("cache_miss", key=key)
        fresh_data = await fetch_func()
        
        if fresh_data:
            # Save to cache asynchronously
            await redis.set(key, json.dumps(fresh_data), ex=expire_seconds)
            
        return fresh_data
    except Exception as e:
        logger.error("cache_error", error=str(e), key=key)
        # Fallback to fetching fresh data if cache fails
        return await fetch_func()
