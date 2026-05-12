from fastapi import APIRouter, HTTPException, Query
from app.services.weather import weather_service, WeatherServiceError
from app.schemas.weather import CurrentWeatherResponse, ForecastResponse
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/current", response_model=CurrentWeatherResponse)
async def get_current_weather(
    lat: float = Query(..., description="Latitude of the village/field"),
    lon: float = Query(..., description="Longitude of the village/field")
):
    """
    Get current weather for a specific location.
    Integrates the WeatherService with Redis caching.
    """
    try:
        data = await weather_service.get_village_weather(lat, lon)
        return data
    except WeatherServiceError as e:
        logger.error("weather_endpoint_error", error=str(e))
        raise HTTPException(status_code=502, detail="Failed to fetch weather data")

@router.get("/forecast", response_model=ForecastResponse)
async def get_weather_forecast(
    lat: float = Query(..., description="Latitude of the village/field"),
    lon: float = Query(..., description="Longitude of the village/field")
):
    """
    Get 8-day weather forecast for a specific location.
    """
    try:
        data = await weather_service.get_forecast(lat, lon)
        return data
    except WeatherServiceError as e:
        logger.error("forecast_endpoint_error", error=str(e))
        raise HTTPException(status_code=502, detail="Failed to fetch forecast data")
