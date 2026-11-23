"""Irrigation scheduling advisory API route.
"""
from typing import Optional
from fastapi import APIRouter, Query
from schemas import IrrigationResponse

router = APIRouter(prefix="/api", tags=["Irrigation"])


@router.get(
    "/irrigation",
    response_model=IrrigationResponse,
    summary="Get irrigation recommendation based on soil moisture and weather forecast"
)
def get_irrigation_advisory(
    lat: float = Query(default=13.3409, description="Latitude"),
    lon: float = Query(default=74.7421, description="Longitude"),
    crop: str = Query(default="Tomato", description="Crop name"),
    growth_stage: str = Query(default="Vegetative", description="Crop growth stage"),
    soil_moisture_pct: Optional[float] = Query(default=45.0, description="Measured or estimated soil moisture percentage")
):
    """Calculates irrigation schedule decision based on soil moisture threshold and rain forecast."""
    # Baseline rule-based logic (expanded in Phase 2)
    reasons = []
    if soil_moisture_pct is not None and soil_moisture_pct < 30.0:
        decision = "IRRIGATE_NOW"
        reasons.append(f"Soil moisture ({soil_moisture_pct:.1f}%) is below optimal vegetative threshold (35%).")
        reasons.append("Irrigate during early morning hours to minimize evaporative losses.")
    elif soil_moisture_pct is not None and soil_moisture_pct > 65.0:
        decision = "SKIP_TODAY"
        reasons.append(f"Soil moisture ({soil_moisture_pct:.1f}%) is sufficient for root uptake.")
        reasons.append("Avoid standing water to prevent root asphyxiation and collar rot.")
    else:
        decision = "REDUCE_WATER"
        reasons.append(f"Soil moisture ({soil_moisture_pct:.1f}%) is adequate; maintain light deficit irrigation.")

    return IrrigationResponse(decision=decision, reasons=reasons)
