"""Unit tests for recommendation generation, IPM ordering, and safety constraints.
"""
from services.recommendation_service import generate_recommendations, KVK_MANDATORY_NOTE
from knowledge_base.kb_loader import get_disease_profile


def test_ipm_ordering_and_kvk_safety_line():
    """Verify that recommendations follow IPM hierarchy and chemical-advisory is always last with KVK notice."""
    kb_profile = get_disease_profile("tomato_early_blight")
    weather = {
        "temperature_c": 28.0,
        "humidity_pct": 88.0,
        "rain_probability_pct": 75.0
    }

    recs, explanation, sources = generate_recommendations(
        disease_entry=kb_profile,
        weather_data=weather,
        risk_level="HIGH",
        risk_score=82,
        confidence=0.91,
        low_confidence=False
    )

    categories = [r.category for r in recs]
    assert len(categories) > 0

    # Chemical advisory must be present and must be the final category
    assert categories[-1] == "chemical-advisory"
    chem_rec = recs[-1]
    assert KVK_MANDATORY_NOTE in chem_rec.action

    # Category precedence order check:
    # Any monitoring should appear before cultural; cultural before water; water before biological; biological before chemical
    order_map = {"monitoring": 1, "cultural": 2, "water": 3, "biological": 4, "chemical-advisory": 5}
    indices = [order_map[c] for c in categories]
    # Check that indices are non-decreasing
    assert indices == sorted(indices)


def test_weather_adjustments():
    """Verify that high humidity (>80%) and high rain (>60%) append specific cultural/water actions."""
    kb_profile = get_disease_profile("tomato_early_blight")
    weather = {
        "temperature_c": 28.0,
        "humidity_pct": 85.0,
        "rain_probability_pct": 70.0
    }

    recs, explanation, sources = generate_recommendations(
        disease_entry=kb_profile,
        weather_data=weather,
        risk_level="HIGH",
        risk_score=80,
        confidence=0.88,
        low_confidence=False
    )

    actions = [r.action for r in recs]
    assert any("drainage" in a.lower() or "suspend overhead watering" in a.lower() for a in actions)
    assert any("airflow" in a.lower() or "humidity" in a.lower() for a in actions)


def test_low_confidence_advisory():
    """When confidence is low, a photo retake recommendation must be present."""
    kb_profile = get_disease_profile("tomato_early_blight")
    weather = {"temperature_c": 25.0, "humidity_pct": 60.0, "rain_probability_pct": 20.0}

    recs, explanation, sources = generate_recommendations(
        disease_entry=kb_profile,
        weather_data=weather,
        risk_level="UNCERTAIN",
        risk_score=30,
        confidence=0.45,
        low_confidence=True
    )

    assert any("retake a clear" in r.action.lower() for r in recs)
    assert "UNCERTAIN" in explanation
