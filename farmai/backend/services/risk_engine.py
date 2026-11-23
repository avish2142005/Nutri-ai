"""Explainable, pure-function risk assessment engine for FarmAI.
"""
from typing import Dict, Any, List, Optional
from schemas import RiskResult, RiskFactor

# Configurable risk scoring weights and thresholds
RISK_CONFIG: Dict[str, Any] = {
    "max_disease_points": 45,
    "humidity_bands": [
        (85.0, 20),
        (75.0, 14),
        (60.0, 7)
    ],
    "rain_bands": [
        (70.0, 15),
        (40.0, 8)
    ],
    "temp_favourability_points": 10,
    "leaf_wetness_points": 10,
    "thresholds": {
        "high": 70,
        "medium": 40
    }
}


def calculate_risk(
    disease_label: str,
    confidence: float,
    is_healthy: bool,
    severity_weight: float,
    favourable_temp_range: Optional[List[float]],
    favourable_humidity_min: Optional[float],
    temperature_c: float,
    humidity_pct: float,
    rain_probability_pct: float,
    low_confidence: bool = False,
    field_stress_pct: Optional[float] = None
) -> RiskResult:
    """Calculate an explainable risk score (0-100) and categorized risk level.

    Args:
        disease_label: Friendly name of disease or crop status.
        confidence: Model prediction confidence (0.0 - 1.0).
        is_healthy: True if diagnosed as healthy.
        severity_weight: Severity multiplier (0.0 - 1.0) from knowledge base.
        favourable_temp_range: [min_temp, max_temp] favourable for disease.
        favourable_humidity_min: Minimum relative humidity for spore spread.
        temperature_c: Current ambient temperature in Celsius.
        humidity_pct: Current relative humidity percentage.
        rain_probability_pct: Max rain probability percentage over 24h.
        low_confidence: Flag indicating confidence < 0.60.
        field_stress_pct: Optional satellite-derived stressed vegetation percentage.

    Returns:
        RiskResult containing level, score, and granular explainable factors.
    """
    factors: List[RiskFactor] = []
    total_score = 0

    # 1. Disease signal factor (0 - 45 points)
    if is_healthy:
        factors.append(
            RiskFactor(
                name="Disease detection",
                points=0,
                reason="Plant tissue diagnosed healthy; no active infection detected."
            )
        )
    else:
        max_disease = RISK_CONFIG["max_disease_points"]
        disease_pts = int(round(confidence * severity_weight * max_disease))
        total_score += disease_pts
        factors.append(
            RiskFactor(
                name="Disease detection",
                points=disease_pts,
                reason=f"{disease_label} identified with {confidence * 100:.1f}% confidence (severity factor {severity_weight:.2f})."
            )
        )

    # 2. Humidity factor (0 - 20 points)
    humid_pts = 0
    for threshold, pts in RISK_CONFIG["humidity_bands"]:
        if humidity_pct > threshold:
            humid_pts = pts
            break
    total_score += humid_pts

    if humid_pts > 0:
        factors.append(
            RiskFactor(
                name="Relative humidity",
                points=humid_pts,
                reason=f"High ambient humidity ({humidity_pct:.1f}%) promotes fungal spore germination and lesion expansion."
            )
        )
    else:
        factors.append(
            RiskFactor(
                name="Relative humidity",
                points=0,
                reason=f"Current humidity ({humidity_pct:.1f}%) is moderate and does not aggressively encourage fungal infection."
            )
        )

    # 3. Rain probability factor (0 - 15 points)
    rain_pts = 0
    for threshold, pts in RISK_CONFIG["rain_bands"]:
        if rain_probability_pct > threshold:
            rain_pts = pts
            break
    total_score += rain_pts

    if rain_pts > 0:
        factors.append(
            RiskFactor(
                name="Rain probability",
                points=rain_pts,
                reason=f"Elevated rain probability ({rain_probability_pct:.1f}%) increases rain splash dispersal and canopy moisture."
            )
        )
    else:
        factors.append(
            RiskFactor(
                name="Rain probability",
                points=0,
                reason=f"Rain probability ({rain_probability_pct:.1f}%) is low; minimal splash dispersal anticipated."
            )
        )

    # 4. Temperature favourability factor (0 - 10 points)
    temp_pts = 0
    if not is_healthy and favourable_temp_range and len(favourable_temp_range) == 2:
        min_temp, max_temp = favourable_temp_range
        if min_temp <= temperature_c <= max_temp:
            temp_pts = RISK_CONFIG["temp_favourability_points"]
            factors.append(
                RiskFactor(
                    name="Temperature favourability",
                    points=temp_pts,
                    reason=f"Current temperature ({temperature_c:.1f}°C) falls inside the optimal pathogen range ({min_temp:.1f}°C - {max_temp:.1f}°C)."
                )
            )
        else:
            factors.append(
                RiskFactor(
                    name="Temperature favourability",
                    points=0,
                    reason=f"Current temperature ({temperature_c:.1f}°C) is outside the primary pathogen propagation range ({min_temp:.1f}°C - {max_temp:.1f}°C)."
                )
            )
    else:
        factors.append(
            RiskFactor(
                name="Temperature favourability",
                points=0,
                reason=f"Current temperature ({temperature_c:.1f}°C) is normal for standard vegetative growth."
            )
        )
    total_score += temp_pts

    # 5. Leaf-wetness proxy factor (0 - 10 points)
    leaf_wet_pts = 0
    if humidity_pct > 80.0 and rain_probability_pct > 50.0:
        leaf_wet_pts = RISK_CONFIG["leaf_wetness_points"]
        factors.append(
            RiskFactor(
                name="Leaf-wetness proxy",
                points=leaf_wet_pts,
                reason=f"Combined high humidity ({humidity_pct:.1f}%) and rain probability ({rain_probability_pct:.1f}%) indicates prolonged free moisture on leaves."
            )
        )
    else:
        factors.append(
            RiskFactor(
                name="Leaf-wetness proxy",
                points=0,
                reason="Leaf surface moisture conditions do not meet persistent wetness criteria."
            )
        )
    total_score += leaf_wet_pts

    # Optional Phase 3: Satellite vegetation stress factor (0 - 15 points)
    if field_stress_pct is not None and field_stress_pct > 25.0:
        stress_pts = min(15, int(field_stress_pct * 0.3))
        total_score += stress_pts
        factors.append(
            RiskFactor(
                name="Field-level vegetation stress",
                points=stress_pts,
                reason=f"Satellite NDVI indicates {field_stress_pct:.1f}% of the field is exhibiting vegetative stress."
            )
        )

    # Explainability & Safety logic for Healthy crops:
    # Healthy crops with severe weather get a 'preventive watch' factor without triggering a false disease alarm
    if is_healthy:
        # Cap score at 35 so it remains LOW / early preventive warning
        if total_score > 35:
            total_score = 35
        # Replace factors with preventive watch notation if weather was high
        if humid_pts > 0 or rain_pts > 0:
            factors.insert(
                0,
                RiskFactor(
                    name="Preventive watch",
                    points=0,
                    reason="Crop is currently healthy, but weather conditions require vigilance against upcoming fungal pressure."
                )
            )

    # Clamp total score between 0 and 100
    final_score = max(0, min(100, total_score))

    # Determine risk category
    if low_confidence:
        level = "UNCERTAIN"
    elif final_score >= RISK_CONFIG["thresholds"]["high"]:
        level = "HIGH"
    elif final_score >= RISK_CONFIG["thresholds"]["medium"]:
        level = "MEDIUM"
    else:
        level = "LOW"

    return RiskResult(level=level, score=final_score, factors=factors)
