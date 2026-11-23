"""Unit tests for weather service caching, parsing, and degraded fallback.
"""
from unittest.mock import patch, MagicMock
from services.weather_service import fetch_weather_and_forecast, _WEATHER_CACHE


def test_weather_caching():
    """Verify that consecutive calls within TTL reuse cached weather results."""
    # Clear cache for isolated test
    _WEATHER_CACHE.clear()

    # Call with specific coordinates
    w1, f1, warnings1 = fetch_weather_and_forecast(lat=13.34, lon=74.74)
    assert w1.temperature_c is not None
    assert w1.humidity_pct is not None

    # Second call should read from cache
    w2, f2, warnings2 = fetch_weather_and_forecast(lat=13.34, lon=74.74)
    assert w1.fetched_at == w2.fetched_at


def test_weather_fallback_on_network_failure():
    """Verify that network exception triggers safe fallback and warning without 500 error."""
    _WEATHER_CACHE.clear()

    with patch("httpx.Client.get", side_effect=Exception("Connection timed out")):
        w, f, warnings = fetch_weather_and_forecast(lat=99.99, lon=99.99)
        assert w.source == "fallback-default"
        assert any("weather unavailable" in warn for warn in warnings)
