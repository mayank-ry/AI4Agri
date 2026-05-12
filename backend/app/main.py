from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import global_exception_handler
from app.core.middleware import ResponseEnvelopeMiddleware
from app.api.router import api_router
from app.services.redis_client import init_redis, close_redis
from app.services.scheduler import start_scheduler, stop_scheduler

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events (startup and shutdown).
    """
    # Startup setup
    setup_logging()
    logger.info("app_starting")
    
    await init_redis()
    start_scheduler()
    
    yield # Application runs here
    
    # Shutdown cleanup
    logger.info("app_shutting_down")
    stop_scheduler()
    await close_redis()

def create_app() -> FastAPI:
    """
    Application factory to create and configure the FastAPI instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan
    )

    # Global Exception Handler
    app.add_exception_handler(Exception, global_exception_handler)

    # Middleware
    app.add_middleware(ResponseEnvelopeMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # Update for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API Routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app

app = create_app()
