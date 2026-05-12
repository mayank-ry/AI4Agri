from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.services.redis_client import get_redis_client
import redis.asyncio as redis
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis_conn: redis.Redis = Depends(get_redis_client)
):
    """
    Health check endpoint.
    Verifies that the API, Database, and Redis are all responding.
    """
    health_status = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown"
    }
    
    # Check Database
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "healthy"
    except Exception as e:
        logger.error("healthcheck_db_failed", error=str(e))
        health_status["database"] = "unhealthy"

    # Check Redis
    try:
        await redis_conn.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        logger.error("healthcheck_redis_failed", error=str(e))
        health_status["redis"] = "unhealthy"

    return health_status
