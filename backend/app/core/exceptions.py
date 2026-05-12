from fastapi import Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch all unhandled exceptions globally, log them, and return a standardized
    API response. This prevents leaking internal server details to the client.
    """
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error occurred.",
            "data": None
        }
    )
