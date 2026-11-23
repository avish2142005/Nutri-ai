"""Recommendation service building ordered, weather-adjusted IPM action plans.
"""
from typing import Dict, Any, List, Tuple
from schemas import RecommendationItem

KVK_MANDATORY_NOTE = "Confirm with your local agriculture officer / Krishi Vigyan Kendra (KVK) before applying any chemical treatment."


def generate_recommendations(
    disease_entry: Dict[str, Any],
    weather_data: Dict[str, Any],
    risk_level: str,
    risk_score: int,
    confidence: float,
    low_confidence: bool = False
) -> Tuple[List[RecommendationItem], str, List[str]]:
    """Build an ordered IPM recommendation action list, plain-language explanation, and sources.

    Order:
        1. monitoring
        2. cultural
        3. water
        4. biological
        5. chemical-advisory (always last, always includes KVK confirmation notice)

    Args:
        disease_entry: Knowledge base entry dict for the detected disease.
        weather_data: Dict containing temperature_c, humidity_pct, rain_probability_pct.
        risk_level: Calculated risk level ("LOW", "MEDIUM", "HIGH", "UNCERTAIN").
        risk_score: Calculated risk score (0-100).
        confidence: Prediction confidence (0.0 - 1.0).
        low_confidence: True if confidence < 0.60.

    Returns:
        Tuple of (List[RecommendationItem], explanation_text, sources_list).
    """
    items: List[RecommendationItem] = []
    crop_name = disease_entry.get("crop", "Crop")
    display_name = disease_entry.get("display_name", "Condition")
    is_healthy = disease_entry.get("is_healthy", False)
    disease_id = disease_entry.get("id", "unknown")

    humidity = float(weather_data.get("humidity_pct", 65.0))
    rain_prob = float(weather_data.get("rain_probability_pct", 20.0))
    temp_c = float(weather_data.get("temperature_c", 25.0))

    # Low confidence advisory
    if low_confidence:
        items.append(
            RecommendationItem(
                action="Retake a clear, close, well-lit photo of a single leaf to improve diagnosis confidence.",
                category="monitoring"
            )
        )

    # 1. Monitoring actions
    for m in disease_entry.get("monitoring", []):
        items.append(RecommendationItem(action=m, category="monitoring"))

    # 2. Cultural controls
    for c in disease_entry.get("cultural_controls", []):
        items.append(RecommendationItem(action=c, category="cultural"))

    if humidity > 80.0 and not is_healthy:
        items.append(
            RecommendationItem(
                action="High humidity alert: Improve canopy airflow by pruning lower suckers and widening plant staking.",
                category="cultural"
            )
        )

    # 3. Water management
    for w in disease_entry.get("water_management", []):
        items.append(RecommendationItem(action=w, category="water"))

    if rain_prob > 60.0:
        items.append(
            RecommendationItem(
                action="Elevated rain probability: Suspend overhead watering and clear drainage channels to prevent waterlogging.",
                category="water"
            )
        )

    # 4. Biological controls
    for b in disease_entry.get("biological_controls", []):
        items.append(RecommendationItem(action=b, category="biological"))

    # 5. Chemical advisory (strictly compliant with safety rule: generic text + KVK note)
    chem_advice = disease_entry.get("chemical_advisory", "")
    if chem_advice:
        if KVK_MANDATORY_NOTE not in chem_advice:
            chem_advice = f"{chem_advice} {KVK_MANDATORY_NOTE}"
        items.append(RecommendationItem(action=chem_advice, category="chemical-advisory"))

    # Explanation generation
    if is_healthy:
        explanation = (
            f"Your {crop_name} crop shows no symptoms of foliar disease and is currently in healthy condition. "
            f"Local weather is {temp_c}°C with {humidity:.0f}% humidity and {rain_prob:.0f}% rain probability. "
            f"Continue routine monitoring and follow good agricultural practices to maintain healthy growth."
        )
    elif low_confidence:
        explanation = (
            f"The image suggests possible symptoms of {display_name} on your {crop_name}, but the confidence "
            f"is below the reliable threshold ({confidence * 100:.1f}%). Risk is marked UNCERTAIN. "
            f"Please retake a clear, close-up photo of a single affected leaf before taking corrective action."
        )
    else:
        weather_impact = "strongly accelerate" if risk_level == "HIGH" else "moderately influence"
        explanation = (
            f"{display_name} has been detected on your {crop_name} with {confidence * 100:.1f}% confidence, "
            f"resulting in a {risk_level} risk score of {risk_score}/100. Current weather conditions "
            f"({temp_c}°C, {humidity:.0f}% humidity, {rain_prob:.0f}% rain chance) {weather_impact} disease progression. "
            f"Prioritize cultural sanitation and biological interventions immediately."
        )

    sources = [f"diseases.json#{disease_id}"]
    if disease_entry.get("source_note"):
        sources.append(disease_entry["source_note"])

    return items, explanation, sources
