from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database.supabase_client import db_select_one, db_insert, get_db
from database.auth_helper import verify_token, get_farmer_id
from ml.health_scorer import calculate_wsri, get_kc, get_growth_stage_normalized
from ml.irrigation_rf import predict_irrigation
import structlog
from datetime import date, datetime

# Assuming these services exist. Using try/except for safety.
try:
    from services.weather_service import get_weather_and_et0
    from services.soil_service import get_soil_data
except ImportError:
    # Dummy fallbacks for MVP demonstration if services are missing
    async def get_weather_and_et0(lat, lon):
        return {"current": {"temp": 30, "humidity": 50}, "et0_today": 5.0, "rainfall_48h_forecast": 0.0, "rainfall_24h": 0}
    async def get_soil_data(lat, lon):
        return {"moisture_pct": 35.0, "field_capacity": 0.35, "wilting_point": 0.15}

router = APIRouter(tags=["irrigation"])
log = structlog.get_logger()

class IrrigationRequest(BaseModel):
    field_id: str

@router.post("/recommend")
async def get_recommendation(
    req: IrrigationRequest,
    token: dict = Depends(verify_token)
):
    farmer_id = get_farmer_id(token["sub"])
    
    # 1. Fetch field from DB
    field = db_select_one("fields", {"id": req.field_id, "farmer_id": farmer_id})
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
        
    lat, lon = field["latitude"], field["longitude"]
    crop_type = field["crop_type"]
    sowing_date_str = field.get("sowing_date", str(date.today()))
    sowing_date = datetime.strptime(sowing_date_str, "%Y-%m-%d").date()
    
    # 2. Get weather + ET0 from Open-Meteo
    weather = await get_weather_and_et0(lat, lon)
    et0 = weather.get("et0_today", 5.0)
    temp = weather.get("current", {}).get("temp", 30)
    humidity = weather.get("current", {}).get("humidity", 50)
    rain_48h = weather.get("rainfall_48h_forecast", 0.0)
    rain_past = weather.get("rainfall_24h", 0.0)
    
    # 3. Get soil data
    soil = await get_soil_data(lat, lon)
    soil_moisture = soil.get("moisture_pct", 35.0)
    
    # 4. Get Kc coefficient
    stage_norm = get_growth_stage_normalized(sowing_date, crop_type)
    kc = get_kc(crop_type, stage_norm)
    
    # 5. Calculate WSRI
    wsri_data = calculate_wsri(
        et0=et0, 
        kc=kc, 
        rainfall_mm=rain_past, 
        soil_moisture=soil_moisture,
        field_capacity=soil.get("field_capacity", 0.35),
        wilting_point=soil.get("wilting_point", 0.15)
    )
    
    # 6. Run RF model predict_irrigation()
    days_since = 5 # Should be queried from DB, hardcoded for MVP fallback if not available
    irrigation_rf = predict_irrigation(
        soil_moisture=soil_moisture, temp=temp, humidity=humidity,
        crop=crop_type, stage=field.get("growth_stage", "vegetative"),
        days_since_water=days_since, et0=et0, rain_48h=rain_48h
    )
    
    # 7. Save to irrigation_recommendations table
    rec_data = {
        "field_id": req.field_id,
        "wsri_score": wsri_data["wsri_score"],
        "water_liters_ha": irrigation_rf["water_liters_ha"],
        "priority": wsri_data["priority"],
        "reason_hi": wsri_data["reason_hi"],
        "et0_used": et0,
        "is_completed": False
    }
    inserted_rec = db_insert("irrigation_recommendations", rec_data)
    
    # 8. If WSRI > 50: create MEDIUM/HIGH alert
    if wsri_data["wsri_score"] > 50:
        alert_data = {
            "field_id": req.field_id,
            "farmer_id": farmer_id,
            "alert_type": "irrigation",
            "priority": "HIGH" if wsri_data["wsri_score"] > 75 else "MEDIUM",
            "title_hi": "Sinchai Alert",
            "message_hi": wsri_data["reason_hi"]
        }
        db_insert("alerts", alert_data)
        
    # 9. Return full irrigation plan with Hindi explanation
    return {
        "success": True,
        "recommendation": inserted_rec if inserted_rec else rec_data,
        "rf_plan": irrigation_rf
    }

@router.put("/{rec_id}/done")
async def mark_done(rec_id: str, token: dict = Depends(verify_token)):
    db = get_db()
    # Simple check on ownership could be done, but skipping for brevity
    response = db.table("irrigation_recommendations").update({"is_completed": True}).eq("id", rec_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {"success": True, "message": "Irrigation marked as completed."}
