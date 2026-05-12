from pydantic import BaseModel
from typing import List, Optional

class WeatherCondition(BaseModel):
    main: str
    description: str
    icon: str

class WeatherData(BaseModel):
    temp: float
    feels_like: float
    humidity: int
    wind_speed: float
    conditions: List[WeatherCondition]
    
class CurrentWeatherResponse(BaseModel):
    lat: float
    lon: float
    current: WeatherData

class ForecastResponse(BaseModel):
    lat: float
    lon: float
    daily: List[WeatherData]
