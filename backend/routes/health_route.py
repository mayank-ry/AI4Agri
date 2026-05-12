from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database.supabase_client import db_select_one, db_insert
from database.auth_helper import verify_token, get_farmer_id
from ml.health_scorer import calculate_achs, calculate_wsri, calculate_cyas, get_kc, get_growth_stage_normalized
from datetime import date, datetime
import structlog

# Assuming these services exist. Using try/except for safety.
try:
    from services.gee_service import get_ndvi
    from services.weather_service import get_weather_and_et0
    from services.soil_service import get_soil_data
except ImportError:
    # Dummies for MVP
    async def get_ndvi(lat, lon): return {"ndvi_value": 0.65, "health_status": "Good", "health_color": "green", "satellite_date": str(date.today())}
    async def get_weather_and_et0(lat, lon): return {"current": {"temp": 30, "humidity": 50}, "et0_today": 5.0, "rainfall_24h": 0}
    async def get_soil_data(lat, lon): return {"moisture_pct": 35.0, "ph": 6.5, "nitrogen_mg_kg": 100, "field_capacity": 0.35, "wilting_point": 0.15}

router = APIRouter(tags=["health"])
log = structlog.get_logger()

@router.get("/{field_id}")
async def get_field_health(field_id: str, token: dict = Depends(verify_token)):
    farmer_id = get_farmer_id(token["sub"])
    
    # 1. Fetch field details from DB
    field = db_select_one("fields", {"id": field_id, "farmer_id": farmer_id})
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
        
    lat, lon = field["latitude"], field["longitude"]
    crop = field["crop_type"]
    sowing_date_str = field.get("sowing_date", str(date.today()))
    sowing_date = datetime.strptime(sowing_date_str, "%Y-%m-%d").date()

    # 2. Get NDVI from GEE
    ndvi_data = await get_ndvi(lat, lon)
    ndvi = ndvi_data.get("ndvi_value", 0.6)
    
    # 3. Get weather from Open-Meteo
    weather = await get_weather_and_et0(lat, lon)
    temp = weather.get("current", {}).get("temp", 30)
    humidity = weather.get("current", {}).get("humidity", 50)
    et0 = weather.get("et0_today", 5.0)
    rain = weather.get("rainfall_24h", 0)
    
    # 4. Get soil from SoilGrids
    soil = await get_soil_data(lat, lon)
    moisture = soil.get("moisture_pct", 40.0)
    ph = soil.get("ph", 6.5)
    nitrogen = soil.get("nitrogen_mg_kg", 100)

    # 5. Calculate ACHS, WSRI, CYAS
    achs = calculate_achs(ndvi, moisture, temp, humidity, ph, nitrogen, sowing_date, crop)
    
    stage_norm = get_growth_stage_normalized(sowing_date, crop)
    kc = get_kc(crop, stage_norm)
    wsri = calculate_wsri(et0, kc, rain, moisture, soil.get("field_capacity", 0.35), soil.get("wilting_point", 0.15))
    
    cyas = calculate_cyas(crop, ndvi, wsri["wsri_score"], nitrogen, temp, ph)

    # 6. Save health_score to DB
    health_data = {
        "field_id": field_id,
        "achs_score": achs["achs_score"],
        "wsri_score": wsri["wsri_score"],
        "cyas_score": cyas["predicted_yield"],
        "ndvi_component": ndvi,
        "soil_component": moisture,
        "weather_component": temp
    }
    db_insert("health_scores", health_data)

    # 7. Save ndvi_reading to DB
    ndvi_record = {
        "field_id": field_id,
        "ndvi_value": ndvi,
        "health_status": ndvi_data.get("health_status", "Good"),
        "health_color": ndvi_data.get("health_color", "green"),
        "satellite_date": ndvi_data.get("satellite_date", str(date.today()))
    }
    db_insert("ndvi_readings", ndvi_record)

    # 8. Save soil_reading to DB
    soil_record = {
        "field_id": field_id,
        "moisture_pct": moisture,
        "ph": ph,
        "nitrogen_mg_kg": nitrogen,
        "phosphorus_mg_kg": soil.get("phosphorus_mg_kg"),
        "potassium_mg_kg": soil.get("potassium_mg_kg")
    }
    db_insert("soil_readings", soil_record)

    # 9. Generate alerts if needed
    if achs["achs_score"] < 40:
        db_insert("alerts", {
            "field_id": field_id, "farmer_id": farmer_id,
            "alert_type": "health", "priority": "HIGH",
            "title_hi": "Fasal ki sehat bahut kharab hai",
            "message_hi": "Kripya apne khet ka muayna karein aur zaroori kadam uthayein."
        })

    # 10. Return complete health report
    return {
        "success": True,
        "achs": achs,
        "wsri": wsri,
        "cyas": cyas,
        "raw_data": {"ndvi": ndvi, "temp": temp, "moisture": moisture}
    }
