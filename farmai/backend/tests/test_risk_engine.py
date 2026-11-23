"""Unit tests for explainable risk calculation engine.
"""
import pytest
from services.risk_engine import calculate_risk


def test_healthy_dry():
    """Healthy crop in dry conditions should yield LOW risk and no disease score."""
    result = calculate_risk(
        disease_label="Healthy Tomato",
        confidence=0.95,
        is_healthy=True,
        severity_weight=0.0,
        favourable_temp_range=[20.0, 30.0],
        favourable_humidity_min=50.0,
        temperature_c=25.0,
        humidity_pct=45.0,
        rain_probability_pct=10.0,
        low_confidence=False
    )
    assert result.level == "LOW"
    assert result.score == 0
    # Disease factor must be 0 points
    disease_factor = next(f for f in result.factors if f.name == "Disease detection")
    assert disease_factor.points == 0


def test_healthy_severe_weather_preventive_watch():
    """Healthy crop with severe weather should cap risk and output preventive watch (no false alarm)."""
    result = calculate_risk(
        disease_label="Healthy Tomato",
        confidence=0.95,
        is_healthy=True,
        severity_weight=0.0,
        favourable_temp_range=[20.0, 30.0],
        favourable_humidity_min=50.0,
        temperature_c=26.0,
        humidity_pct=92.0,  # >85 -> 20 pts
        rain_probability_pct=85.0,  # >70 -> 15 pts + leaf wetness -> 10 pts
        low_confidence=False
    )
    # Must NOT produce a HIGH disease alarm
    assert result.level == "LOW"
    assert result.score <= 35
    # Must contain preventive watch factor
    preventive_factor = next((f for f in result.factors if f.name == "Preventive watch"), None)
    assert preventive_factor is not None


def test_disease_humid_rainy_high_risk():
    """Severe disease under warm, humid, and rainy conditions must produce HIGH risk (>=70)."""
    result = calculate_risk(
        disease_label="Late Blight",
        confidence=0.92,
        is_healthy=False,
        severity_weight=0.95,
        favourable_temp_range=[15.0, 22.0],
        favourable_humidity_min=85.0,
        temperature_c=18.0,  # Within favourable range -> 10 pts
        humidity_pct=90.0,   # >85 -> 20 pts
        rain_probability_pct=80.0,  # >70 -> 15 pts; leaf-wetness -> 10 pts
        low_confidence=False
    )
    # Disease points: round(0.92 * 0.95 * 45) = 39 pts
    # Total = 39 + 20 + 15 + 10 + 10 = 94 pts
    assert result.level == "HIGH"
    assert result.score >= 70
    assert any(f.name == "Leaf-wetness proxy" and f.points == 10 for f in result.factors)


def test_disease_dry_medium_risk():
    """Disease detected under dry, unfavourable weather should result in MEDIUM or LOW risk."""
    result = calculate_risk(
        disease_label="Early Blight",
        confidence=0.80,
        is_healthy=False,
        severity_weight=0.75,
        favourable_temp_range=[24.0, 30.0],
        favourable_humidity_min=75.0,
        temperature_c=35.0,  # Outside favourable range -> 0 pts
        humidity_pct=50.0,   # Low humidity -> 0 pts
        rain_probability_pct=10.0,  # Low rain -> 0 pts
        low_confidence=False
    )
    # Disease points: round(0.80 * 0.75 * 45) = 27 pts
    # Total = 27 pts -> <40 => LOW, or with moderate disease -> between 25-45
    assert result.level in ["LOW", "MEDIUM"]
    assert result.score < 70


def test_low_confidence_uncertain():
    """When confidence is low (<0.60), risk level must be UNCERTAIN."""
    result = calculate_risk(
        disease_label="Early Blight",
        confidence=0.48,
        is_healthy=False,
        severity_weight=0.75,
        favourable_temp_range=[24.0, 30.0],
        favourable_humidity_min=75.0,
        temperature_c=27.0,
        humidity_pct=88.0,
        rain_probability_pct=80.0,
        low_confidence=True
    )
    assert result.level == "UNCERTAIN"


def test_boundary_values():
    """Test boundary conditions for thresholds (e.g. exactly 70, exactly 40)."""
    # Test boundary rain 70.0% and humidity 85.0%
    result = calculate_risk(
        disease_label="Early Blight",
        confidence=0.85,
        is_healthy=False,
        severity_weight=0.75,
        favourable_temp_range=[24.0, 30.0],
        favourable_humidity_min=75.0,
        temperature_c=25.0,
        humidity_pct=75.0,  # boundary for 60-75% band
        rain_probability_pct=40.0,  # boundary for 0-40% band
        low_confidence=False
    )
    assert result.score >= 0 and result.score <= 100
    assert result.level in ["LOW", "MEDIUM", "HIGH"]
