"""Pydantic schemas and data contracts for FarmAI API.
"""
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., json_schema_extra={"example": "ok"})
    model_loaded: bool = Field(..., json_schema_extra={"example": True})
    demo_mode: bool = Field(..., json_schema_extra={"example": False})


class TopKPrediction(BaseModel):
    """Individual class prediction with confidence."""
    label: str = Field(..., json_schema_extra={"example": "Early Blight"})
    confidence: float = Field(..., json_schema_extra={"example": 0.91})


class SeverityResult(BaseModel):
    """Disease severity estimation metrics."""
    level: Literal["Healthy", "Mild", "Moderate", "Severe"] = Field(..., json_schema_extra={"example": "Moderate"})
    score: float = Field(default=0.0, ge=0.0, le=1.0, json_schema_extra={"example": 0.42})
    affected_percentage: float = Field(default=0.0, json_schema_extra={"example": 21.5})
    lesion_count: int = Field(default=0, json_schema_extra={"example": 7})
    canopy_risk: str = Field(default="Guarded", json_schema_extra={"example": "Guarded"})
    action_urgency: str = Field(default="Targeted Intervention", json_schema_extra={"example": "Biological / Targeted Intervention"})
    overlay_image: Optional[str] = Field(default=None, json_schema_extra={"example": "data:image/jpeg;base64,..."})


class DiseaseResult(BaseModel):
    """Disease detection output schema."""
    label: str = Field(..., json_schema_extra={"example": "Early Blight"})
    raw_class: str = Field(..., json_schema_extra={"example": "Tomato___Early_blight"})
    confidence: float = Field(..., json_schema_extra={"example": 0.91})
    is_healthy: bool = Field(..., json_schema_extra={"example": False})
    condition_type: str = Field(default="fungal", json_schema_extra={"example": "fungal"})
    architecture: str = Field(default="efficientnet_b3", json_schema_extra={"example": "efficientnet_b3"})
    severity: Optional[SeverityResult] = None
    top_k: List[TopKPrediction] = Field(default_factory=list)
    low_confidence: bool = Field(default=False)


class WeatherData(BaseModel):
    """Current weather observations and 24h summary."""
    temperature_c: float = Field(..., json_schema_extra={"example": 28.0})
    humidity_pct: float = Field(..., json_schema_extra={"example": 88.0})
    rain_probability_pct: float = Field(..., json_schema_extra={"example": 75.0})
    precipitation_mm_24h: float = Field(..., json_schema_extra={"example": 12.4})
    source: str = Field(default="open-meteo", json_schema_extra={"example": "open-meteo"})
    fetched_at: str = Field(..., json_schema_extra={"example": "2026-09-24T22:00:00Z"})


class WeatherForecastDay(BaseModel):
    """Daily forecast summary item."""
    date: str = Field(..., json_schema_extra={"example": "2026-09-25"})
    temperature_max_c: float = Field(..., json_schema_extra={"example": 30.5})
    temperature_min_c: float = Field(..., json_schema_extra={"example": 24.1})
    precipitation_probability_max: float = Field(..., json_schema_extra={"example": 60.0})


class WeatherForecastResponse(BaseModel):
    """Weather endpoint response with current conditions and 3-day forecast."""
    current: WeatherData
    forecast: List[WeatherForecastDay] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class RiskFactor(BaseModel):
    """Explainable risk factor item."""
    name: str = Field(..., json_schema_extra={"example": "Disease detection"})
    points: int = Field(..., json_schema_extra={"example": 45})
    reason: str = Field(..., json_schema_extra={"example": "Early Blight detected with 91.0% confidence"})


class RiskResult(BaseModel):
    """Calculated risk score and categorized risk level."""
    level: Literal["LOW", "MEDIUM", "HIGH", "UNCERTAIN"] = Field(..., json_schema_extra={"example": "HIGH"})
    score: int = Field(..., ge=0, le=100, json_schema_extra={"example": 82})
    factors: List[RiskFactor] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    """Specific actionable agricultural advisory item."""
    action: str = Field(..., json_schema_extra={"example": "Remove and safely dispose of infected lower leaves."})
    category: Literal["cultural", "biological", "monitoring", "water", "chemical-advisory"] = Field(
        ..., json_schema_extra={"example": "cultural"}
    )


class AnalyzeCropResponse(BaseModel):
    """Full crop analysis response model matching API specification."""
    analysis_id: int = Field(..., json_schema_extra={"example": 1})
    crop: str = Field(..., json_schema_extra={"example": "Tomato"})
    disease: DiseaseResult
    weather: WeatherData
    risk: RiskResult
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    explanation: str = Field(..., json_schema_extra={"example": "Early Blight detected on Tomato. High humidity and rain elevate risk."})
    sources: List[str] = Field(default_factory=list, json_schema_extra={"example": ["diseases.json#tomato_early_blight"]})
    multilingual_summary: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class IrrigationResponse(BaseModel):
    """Irrigation scheduling advisory response."""
    decision: Literal["IRRIGATE_NOW", "SKIP_TODAY", "REDUCE_WATER"] = Field(..., json_schema_extra={"example": "SKIP_TODAY"})
    reasons: List[str] = Field(default_factory=list)


class NdviStats(BaseModel):
    """Statistical distribution of NDVI values across the field."""
    min: float = Field(..., json_schema_extra={"example": 0.12})
    max: float = Field(..., json_schema_extra={"example": 0.88})
    p10: float = Field(..., json_schema_extra={"example": 0.25})
    p90: float = Field(..., json_schema_extra={"example": 0.79})


class NdviHealthClassPct(BaseModel):
    """Field area distribution across vegetation health categories."""
    healthy: float = Field(..., json_schema_extra={"example": 62.5})
    moderate: float = Field(..., json_schema_extra={"example": 24.1})
    stressed: float = Field(..., json_schema_extra={"example": 9.4})
    bare_or_water: float = Field(..., json_schema_extra={"example": 4.0})


class SatelliteNdviResponse(BaseModel):
    """Sentinel-2 vegetation index monitoring response."""
    acquired_on: str = Field(..., json_schema_extra={"example": "2026-09-20"})
    cloud_cover_pct: float = Field(..., json_schema_extra={"example": 4.2})
    mean_ndvi: float = Field(..., json_schema_extra={"example": 0.64})
    stats: NdviStats
    health_class_pct: NdviHealthClassPct
    bbox: List[float] = Field(..., json_schema_extra={"example": [74.737, 13.336, 74.747, 13.345]})
    overlay_png_base64: str = Field(...)
    grid: List[List[float]] = Field(default_factory=list)
    source: Literal["sentinel-2", "synthetic-demo"] = Field(..., json_schema_extra={"example": "sentinel-2"})
    warnings: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Farmer chat query model."""
    message: str = Field(..., json_schema_extra={"example": "What organic spray can I use for early blight?"})
    analysis_id: Optional[int] = Field(default=None, json_schema_extra={"example": 1})
    language: str = Field(default="en", json_schema_extra={"example": "en"})


class ChatResponse(BaseModel):
    """Farmer chat response model."""
    answer: str = Field(..., json_schema_extra={"example": "Use neem seed kernel extract (5%) or bio-fungicide Bacillus subtilis."})
    sources: List[str] = Field(default_factory=list, json_schema_extra={"example": ["docs/ipm_principles.md"]})
    grounded: bool = Field(default=True)


class HistoryItem(BaseModel):
    """Historical analysis record summary."""
    id: int
    crop: str
    disease_label: str
    confidence: float
    risk_level: str
    risk_score: int
    created_at: str
    image_path: Optional[str] = None
    response_json: Optional[Dict[str, Any]] = None
