import httpx
import structlog
from typing import Optional

log = structlog.get_logger()
BASE_URL = "https://api.open-meteo.com/v1/forecast"

async def get_weather_and_et0(lat: float, lon: float) -> dict:
    try:
        params = {
            "latitude": lat, 
            "longitude": lon,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "windspeed_10m_max",
                "et0_fao_evapotranspiration"
            ],
            "hourly": ["soil_moisture_0_1cm"],
            "forecast_days": 7,
            "timezone": "Asia/Kolkata"
        }
        
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(BASE_URL, params=params)
            r.raise_for_status()
            data = r.json()
       
        daily = data.get('daily', {})
        if not daily:
            raise ValueError("No daily weather data returned")
            
        et0_today = daily['et0_fao_evapotranspiration'][0] if daily['et0_fao_evapotranspiration'][0] is not None else 4.0
        rain_sum_7d = sum(x or 0 for x in daily['precipitation_sum'])
        rain_48h = sum(x or 0 for x in daily['precipitation_sum'][:2])
        temp_max = daily['temperature_2m_max'][0] if daily['temperature_2m_max'][0] is not None else 30.0
        temp_min = daily['temperature_2m_min'][0] if daily['temperature_2m_min'][0] is not None else 15.0
        temp_avg = (temp_max + temp_min) / 2
       
        forecast = []
        for i in range(min(7, len(daily.get('time', [])))):
            forecast.append({
                'date': daily['time'][i],
                'temp_max': daily['temperature_2m_max'][i],
                'temp_min': daily['temperature_2m_min'][i],
                'rain_mm': daily['precipitation_sum'][i] or 0,
                'et0': daily['et0_fao_evapotranspiration'][i],
                'wind': daily['windspeed_10m_max'][i],
            })
       
        farming_alerts = generate_farming_alerts(
            rain_48h, temp_max, daily['windspeed_10m_max'][0]
        )
       
        return {
            'temp_avg': round(temp_avg, 1),
            'temp_max': round(temp_max, 1),
            'temp_min': round(temp_min, 1),
            'et0_today': round(et0_today, 3),
            'rainfall_7d': round(rain_sum_7d, 1),
            'rainfall_48h_forecast': round(rain_48h, 1),
            'forecast': forecast,
            'farming_alerts_hi': farming_alerts,
        }
    except Exception as e:
        log.error("Weather fetch failed", error=str(e))
        return {
            'temp_avg': 28.0,
            'temp_max': 35.0,
            'temp_min': 20.0,
            'et0_today': 4.5,
            'rainfall_7d': 0.0,
            'rainfall_48h_forecast': 0.0,
            'forecast': [],
            'farming_alerts_hi': ["Mausam theek hai — kheti ke liye acha samay"]
        }

def generate_farming_alerts(rain_48h, temp_max, wind) -> list:
    alerts = []
    if rain_48h > 10:
        alerts.append(f"Agle 2 din mein {rain_48h:.0f}mm barish — spray rokein")
    if temp_max > 40:
        alerts.append("Bahut garmi hai — extra irrigation zaruri hai")
    if wind and wind > 25:
        alerts.append("Tej hawa hai — spray postpone karein")
    if not alerts:
        alerts.append("Mausam theek hai — kheti ke liye acha samay")
    return alerts
