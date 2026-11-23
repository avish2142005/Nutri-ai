"""Weather API route providing current weather and 3-day forecast summary.
"""
from fastapi import APIRouter, Query
from schemas import WeatherForecastResponse
from services.weather_service import fetch_weather_and_forecast

router = APIRouter(prefix="/api", tags=["Weather"])


@router.get(
    "/weather",
    response_model=WeatherForecastResponse,
    summary="Get current weather and 3-day forecast summary"
)
def get_weather(
    lat: float = Query(default=13.3409, description="Latitude (default: Udupi, 13.3409)"),
    lon: float = Query(default=74.7421, description="Longitude (default: Udupi, 74.7421)")
):
    """Returns real-time weather observations and forecast from Open-Meteo API."""
    current, forecast, warnings = fetch_weather_and_forecast(lat=lat, lon=lon)
    return WeatherForecastResponse(
        current=current,
        forecast=forecast,
        warnings=warnings
    )
