"""Weather service interacting with Open-Meteo API with caching, retry, and fallback.
"""
import time
import logging
from typing import Tuple, List, Optional, Dict, Any
from datetime import datetime, timezone
import httpx

from config import settings
from schemas import WeatherData, WeatherForecastDay

logger = logging.getLogger(__name__)

# Cache structure: Dict[Tuple[float, float], Dict[str, Any]]
# Key is (round(lat, 2), round(lon, 2))
# Value: {"weather": WeatherData, "forecast": List[WeatherForecastDay], "timestamp": float}
_WEATHER_CACHE: Dict[Tuple[float, float], Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 600.0  # 10 minutes


def _get_cache_key(lat: float, lon: float) -> Tuple[float, float]:
    """Return rounded coordinates for cache indexing."""
    return (round(float(lat), 2), round(float(lon), 2))


def fetch_weather_and_forecast(
    lat: float = 13.3409,
    lon: float = 74.7421
) -> Tuple[WeatherData, List[WeatherForecastDay], List[str]]:
    """Fetch current weather and 3-day forecast from Open-Meteo API with caching and fallback.

    Args:
        lat: Latitude of location.
        lon: Longitude of location.

    Returns:
        Tuple of (WeatherData, List[WeatherForecastDay], List[warnings]).
    """
    cache_key = _get_cache_key(lat, lon)
    now = time.time()
    warnings: List[str] = []

    # Check cache for fresh entry (< 10 minutes)
    cached = _WEATHER_CACHE.get(cache_key)
    if cached and (now - cached["timestamp"] < CACHE_TTL_SECONDS):
        logger.info(f"Serving weather from cache for {cache_key}")
        return cached["weather"], cached["forecast"], warnings

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m",
        "hourly": "precipitation_probability,precipitation",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto",
        "forecast_days": 4
    }

    # 5s timeout, 1 retry (2 attempts total)
    max_attempts = 2
    response_data: Optional[Dict[str, Any]] = None

    for attempt in range(1, max_attempts + 1):
        try:
            with httpx.Client(timeout=settings.open_meteo_timeout) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                response_data = resp.json()
                break
        except Exception as e:
            logger.warning(f"Open-Meteo request attempt {attempt} failed: {e}")
            if attempt < max_attempts:
                time.sleep(0.5)

    if response_data:
        try:
            current = response_data.get("current", {})
            temp_c = float(current.get("temperature_2m", 25.0))
            humidity = float(current.get("relative_humidity_2m", 65.0))

            # Next 24 hours precipitation probability (max) and precipitation sum
            hourly = response_data.get("hourly", {})
            hourly_rain_prob = hourly.get("precipitation_probability", [])[:24]
            rain_prob_pct = float(max(hourly_rain_prob)) if hourly_rain_prob else 20.0

            hourly_precip = hourly.get("precipitation", [])[:24]
            precip_mm = float(sum(hourly_precip)) if hourly_precip else 0.0

            fetched_at = datetime.now(timezone.utc).isoformat()
            weather = WeatherData(
                temperature_c=round(temp_c, 1),
                humidity_pct=round(humidity, 1),
                rain_probability_pct=round(rain_prob_pct, 1),
                precipitation_mm_24h=round(precip_mm, 1),
                source="open-meteo",
                fetched_at=fetched_at
            )

            # Daily forecast (next 3 days, skipping index 0 which is today)
            daily = response_data.get("daily", {})
            dates = daily.get("time", [])[1:4]
            max_temps = daily.get("temperature_2m_max", [])[1:4]
            min_temps = daily.get("temperature_2m_min", [])[1:4]
            rain_probs = daily.get("precipitation_probability_max", [])[1:4]

            forecast: List[WeatherForecastDay] = []
            for i in range(len(dates)):
                forecast.append(
                    WeatherForecastDay(
                        date=str(dates[i]),
                        temperature_max_c=float(max_temps[i]) if i < len(max_temps) else 30.0,
                        temperature_min_c=float(min_temps[i]) if i < len(min_temps) else 22.0,
                        precipitation_probability_max=float(rain_probs[i]) if i < len(rain_probs) else 30.0
                    )
                )

            # Save in cache
            _WEATHER_CACHE[cache_key] = {
                "weather": weather,
                "forecast": forecast,
                "timestamp": now
            }
            return weather, forecast, warnings
        except Exception as parse_err:
            logger.error(f"Error parsing Open-Meteo payload: {parse_err}")

    # Fallback path if network / API completely fails
    if cached:
        warnings.append("Live weather service unavailable; using stale cached weather data.")
        return cached["weather"], cached["forecast"], warnings

    warnings.append("weather unavailable; risk computed from image only")
    fallback_weather = WeatherData(
        temperature_c=25.0,
        humidity_pct=65.0,
        rain_probability_pct=20.0,
        precipitation_mm_24h=0.0,
        source="fallback-default",
        fetched_at=datetime.now(timezone.utc).isoformat()
    )
    fallback_forecast: List[WeatherForecastDay] = []
    return fallback_weather, fallback_forecast, warnings
