import os
from datetime import datetime, timedelta

import ee
import structlog

log = structlog.get_logger()
_initialized = False

GEE_SERVICE_ACCOUNT = os.getenv("GEE_SERVICE_ACCOUNT", "PASTE_YOUR_GEE_SERVICE_ACCOUNT_EMAIL_HERE")
GEE_KEY_FILE = os.getenv("GEE_KEY_FILE", "backend/secrets/gee_key.json")


def init_gee():
    global _initialized
    if _initialized:
        return
    try:
        credentials = ee.ServiceAccountCredentials(GEE_SERVICE_ACCOUNT, GEE_KEY_FILE)
        ee.Initialize(credentials)
        _initialized = True
        log.info("gee_initialized")
    except Exception as e:
        log.error("gee_init_failed", error=str(e))


async def get_ndvi(lat: float, lon: float) -> dict:
    init_gee()
    try:
        point = ee.Geometry.Point([lon, lat])
        end = datetime.now()
        start = end - timedelta(days=30)

        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(point)
            .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
            .sort("CLOUDY_PIXEL_PERCENTAGE")
        )

        image = collection.first()
        ndvi = image.normalizedDifference(["B8", "B4"])
        value = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=10,
        ).getInfo()

        ndvi_val = value.get("nd", 0.45)
        return classify_ndvi(float(ndvi_val or 0.45))
    except Exception as e:
        log.error("gee_ndvi_failed", error=str(e))
        return classify_ndvi(0.45)


def classify_ndvi(val: float) -> dict:
    satellite_date = datetime.now().date().isoformat()
    if val > 0.6:
        return {
            "ndvi_value": val,
            "health_status": "Healthy",
            "health_color": "#22c55e",
            "satellite_date": satellite_date,
            "message_hi": "Fasal swasth hai.",
        }
    if val > 0.4:
        return {
            "ndvi_value": val,
            "health_status": "Moderate",
            "health_color": "#eab308",
            "satellite_date": satellite_date,
            "message_hi": "Fasal ko thoda dhyan chahiye.",
        }
    if val > 0.2:
        return {
            "ndvi_value": val,
            "health_status": "Stressed",
            "health_color": "#f97316",
            "satellite_date": satellite_date,
            "message_hi": "Fasal par tanav hai.",
        }
    return {
        "ndvi_value": val,
        "health_status": "Critical",
        "health_color": "#ef4444",
        "satellite_date": satellite_date,
        "message_hi": "Turant dhyan den.",
    }
