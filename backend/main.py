import os
import time
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from database.supabase_client import get_db

load_dotenv()
log = structlog.get_logger()

# ── TTL Cache ────────────────────────────────────────────────────────
class TTLCache:
    def __init__(self):
        self._cache = {}

    def set(self, key, value, ttl=3600):
        self._cache[key] = {"value": value, "expires_at": time.time() + ttl}

    def get(self, key):
        item = self._cache.get(key)
        if item and time.time() < item["expires_at"]:
            return item["value"]
        self._cache.pop(key, None)
        return None

cache = TTLCache()

# ── FastAPI App ──────────────────────────────────────────────────────
app = FastAPI(
    title="AI4Agri MVP API",
    version="2.0.0",
    description="Precision Agriculture AI backend — CNN + HuggingFace + Gemini + Supabase",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Scheduler ────────────────────────────────────────────────────────
scheduler = BackgroundScheduler()

def refresh_all_ndvi():
    log.info("scheduler_job_ndvi_refresh_started")
    # Pull active fields from DB and refresh NDVI via GEE
    try:
        db = get_db()
        fields = db.table("fields").select("id,latitude,longitude").eq("is_active", True).execute()
        for field in (fields.data or []):
            cache_key = f"ndvi_{field['latitude']:.3f}_{field['longitude']:.3f}"
            cache.set(cache_key, None, ttl=0)  # Invalidate so next call re-fetches
        log.info("ndvi_cache_invalidated", count=len(fields.data or []))
    except Exception as e:
        log.error("ndvi_refresh_failed", error=str(e))

# ── Startup ──────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    log.info("ai4agri_api_starting", version="2.0.0")

    # 1. Supabase connection check
    try:
        get_db()
        log.info("supabase_connected")
    except Exception as e:
        log.error("supabase_connection_failed", error=str(e))

    # 2. Preload critical ML models (CNN + ViT) in background thread
    try:
        import threading
        from ml.model_manager import preload_all
        t = threading.Thread(target=preload_all, daemon=True)
        t.start()
        log.info("ml_preload_started_background")
    except Exception as e:
        log.error("ml_preload_failed", error=str(e))

    # 3. Scheduler
    scheduler.add_job(refresh_all_ndvi, "interval", hours=6, id="ndvi_refresh")
    scheduler.start()
    log.info("scheduler_started")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown(wait=False)
    log.info("ai4agri_api_shutdown")

# ── Routes ───────────────────────────────────────────────────────────
try:
    from routes import auth, disease, irrigation, chatbot, health_route
    app.include_router(auth.router,         prefix="/api/v1/auth",       tags=["auth"])
    app.include_router(disease.router,      prefix="/api/v1/disease",    tags=["disease"])
    app.include_router(irrigation.router,   prefix="/api/v1/irrigation", tags=["irrigation"])
    app.include_router(chatbot.router,      prefix="/api/v1/chatbot",    tags=["chatbot"])
    app.include_router(health_route.router, prefix="/api/v1/health",     tags=["health"])
    log.info("all_routes_registered")
except ImportError as e:
    log.error("route_import_failed", error=str(e))

# ── Health Check ─────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    from ml.model_manager import get_all_status
    model_statuses = get_all_status()
    ready_count = sum(1 for m in model_statuses if m["status"] == "ready")
    return {
        "status": "ok",
        "version": "2.0.0",
        "models_ready": f"{ready_count}/{len(model_statuses)}",
        "models": model_statuses,
    }
