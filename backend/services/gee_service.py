import ee
import os
import structlog
from datetime import datetime, timedelta

log = structlog.get_logger()
_initialized = False

GEE_SERVICE_ACCOUNT = os.getenv("GEE_SERVICE_ACCOUNT", "PASTE_YOUR_GEE_SERVICE_ACCOUNT_EMAIL_HERE")
GEE_KEY_FILE = os.getenv("GEE_KEY_FILE", "test_keys/gee_key.json")

def init_gee():
    global _initialized
    if _initialized: 
        return
    try:
        credentials = ee.ServiceAccountCredentials(GEE_SERVICE_ACCOUNT, GEE_KEY_FILE)
        ee.Initialize(credentials)
        _initialized = True
        log.info("GEE initialized successfully")
    except Exception as e:
        log.error("GEE init failed", error=str(e))

def get_ndvi(lat: float, lon: float) -> dict:
    init_gee()
    try:
        point = ee.Geometry.Point([lon, lat])
        end = datetime.now()
        start = end - timedelta(days=30)
        
        collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(point)
            .filterDate(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            .sort('CLOUDY_PIXEL_PERCENTAGE'))
            
        image = collection.first()
        ndvi = image.normalizedDifference(['B8','B4'])
        
        value = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point, 
            scale=10
        ).getInfo()
        
        ndvi_val = value.get('nd', 0.45)
        if ndvi_val is None:
            ndvi_val = 0.45
            
        return classify_ndvi(float(ndvi_val))
    except Exception as e:
        log.error("GEE NDVI failed", error=str(e))
        return classify_ndvi(0.45)  # fallback

def classify_ndvi(val: float) -> dict:
    if val > 0.6:
        return {
            'ndvi_value': val,
            'health_status': 'Healthy',
            'health_color': '#22c55e',
            'message_hi': 'Fasal swasth hai ✅'
        }
    elif val > 0.4:
        return {
            'ndvi_value': val,
            'health_status': 'Moderate',
            'health_color': '#eab308',
            'message_hi': 'Fasal ko thodi dhyan chahiye ⚠️'
        }
    elif val > 0.2:
        return {
            'ndvi_value': val,
            'health_status': 'Stressed',
            'health_color': '#f97316',
            'message_hi': 'Fasal par tanaav hai 🟠'
        }
    else:
        return {
            'ndvi_value': val,
            'health_status': 'Critical',
            'health_color': '#ef4444',
            'message_hi': 'Turant dhyan den! 🔴'
        }
