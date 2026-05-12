from fastapi import APIRouter
from app.api.endpoints import health, insights, ai

api_router = APIRouter()

# Include all endpoint routers here
api_router.include_router(health.router, tags=["health"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
