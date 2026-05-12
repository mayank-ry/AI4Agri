import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog
from app.core.config import settings
from app.services.cache import get_cached_or_fetch

logger = structlog.get_logger(__name__)

class WeatherServiceError(Exception):
    pass

class WeatherService:
    BASE_URL = "https://api.openweathermap.org/data/3.0/onecall"
    
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        if not self.api_key:
            logger.warning("OPENWEATHER_API_KEY is not set")
            
        # Optimize for async calls using a shared connection pool
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True
    )
    async def _fetch_from_api(self, lat: float, lon: float, exclude: str = "minutely,alerts") -> dict:
        """
        Fetch data from OpenWeather API with retry logic.
        Retries up to 3 times with exponential backoff on network errors or timeouts.
        """
        if not self.api_key:
            raise WeatherServiceError("OpenWeather API key is missing")

        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "exclude": exclude,
            "units": "metric"  # AI4Agri defaults to metric system
        }

        try:
            logger.info("fetching_weather_api", lat=lat, lon=lon)
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("weather_api_http_error", status_code=e.response.status_code, text=e.response.text)
            raise WeatherServiceError(f"HTTP error {e.response.status_code} from OpenWeather")
        except httpx.RequestError as e:
            logger.error("weather_api_request_error", error=str(e))
            raise

    async def get_village_weather(self, lat: float, lon: float) -> dict:
        """
        Get current weather for a specific coordinate (village-level precision).
        Results are cached for 30 minutes to reduce API usage and improve latency.
        """
        # Round coords slightly to optimize cache hits for nearby village points
        cache_key = f"weather:current:{round(lat, 3)}:{round(lon, 3)}"
        
        async def fetcher():
            data = await self._fetch_from_api(lat, lon, exclude="minutely,hourly,daily,alerts")
            return {
                "lat": data["lat"],
                "lon": data["lon"],
                "current": {
                    "temp": data["current"]["temp"],
                    "feels_like": data["current"]["feels_like"],
                    "humidity": data["current"]["humidity"],
                    "wind_speed": data["current"]["wind_speed"],
                    "conditions": data["current"]["weather"]
                }
            }
            
        # Cache for 1800 seconds (30 minutes)
        return await get_cached_or_fetch(cache_key, fetcher, expire_seconds=1800)

    async def get_forecast(self, lat: float, lon: float) -> dict:
        """
        Get 8-day daily forecast.
        Results are cached for 3 hours since daily forecasts change less frequently.
        """
        cache_key = f"weather:forecast:{round(lat, 3)}:{round(lon, 3)}"
        
        async def fetcher():
            data = await self._fetch_from_api(lat, lon, exclude="current,minutely,hourly,alerts")
            
            daily_forecast = []
            for day in data.get("daily", []):
                daily_forecast.append({
                    "temp": day["temp"]["day"],
                    "feels_like": day["feels_like"]["day"],
                    "humidity": day["humidity"],
                    "wind_speed": day["wind_speed"],
                    "conditions": day["weather"]
                })
                
            return {
                "lat": data["lat"],
                "lon": data["lon"],
                "daily": daily_forecast
            }
            
        # Cache for 10800 seconds (3 hours)
        return await get_cached_or_fetch(cache_key, fetcher, expire_seconds=10800)

weather_service = WeatherService()
