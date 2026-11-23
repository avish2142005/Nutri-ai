"""Crop disease analysis endpoint handling image upload, ML prediction, weather risk fusion, and database persistence.
"""
import os
import uuid
import logging
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.orm_models import CropAnalysis, WeatherRecord, Crop, Farm
from schemas import AnalyzeCropResponse
from models.disease_model import predict_crop_disease
from services.weather_service import fetch_weather_and_forecast
from services.risk_engine import calculate_risk
from services.recommendation_service import generate_recommendations
from services.multilingual_service import get_multilingual_diagnosis
from knowledge_base.kb_loader import get_disease_profile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Crop Analysis"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "/analyze",
    response_model=AnalyzeCropResponse,
    summary="Analyze crop leaf image for disease, weather risk, and IPM recommendations"
)
async def analyze_crop(
    image: UploadFile = File(..., description="Crop leaf photo (JPEG, PNG, WebP up to 8MB)"),
    crop: Optional[str] = Form(default=None, description="Optional crop name (e.g. Tomato, Potato, Pepper)"),
    architecture: str = Form(default="efficientnet_b3", description="Deep learning architecture ('efficientnet_b3', 'resnet50', 'mobilenet_v2')"),
    lat: float = Form(default=13.3409, description="Latitude (default: Udupi, 13.3409)"),
    lon: float = Form(default=74.7421, description="Longitude (default: Udupi, 74.7421)"),
    farm_id: Optional[int] = Form(default=None, description="Optional associated farm ID"),
    db: Session = Depends(get_db)
):
    """Orchestrates image inference, live weather fetching, explainable risk scoring,
    and tailored IPM recommendations with database persistence.
    """
    # 1. Validate file extension and MIME type
    filename = image.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    content_type = image.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES and ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid file type '{content_type}'. Supported formats: JPEG, PNG, WebP."
        )

    # 2. Read and validate file size
    try:
        image_bytes = await image.read()
    except Exception as read_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to read uploaded image: {read_err}"
        )

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty."
        )

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Image file exceeds maximum allowed size of 8 MB."
        )

    # 3. Save uploaded image to disk for persistence
    file_id = f"{uuid.uuid4().hex}{ext if ext else '.jpg'}"
    saved_path = UPLOAD_DIR / file_id
    try:
        with open(saved_path, "wb") as f:
            f.write(image_bytes)
        relative_image_path = f"uploads/{file_id}"
    except Exception as save_err:
        logger.warning(f"Could not persist image file to disk: {save_err}")
        relative_image_path = None

    # 4. Predict disease
    all_warnings = []
    try:
        disease_result, kb_id, model_warnings = predict_crop_disease(
            image_bytes, preferred_crop=crop, architecture=architecture, filename=filename
        )
        all_warnings.extend(model_warnings)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err)
        )

    # 5. Fetch knowledge base profile
    kb_profile = get_disease_profile(kb_id)
    detected_crop = kb_profile.get("crop", crop or "Tomato")

    # 6. Fetch live weather & forecast
    weather_data, _, weather_warnings = fetch_weather_and_forecast(lat=lat, lon=lon)
    all_warnings.extend(weather_warnings)

    # 7. Compute explainable risk
    risk_result = calculate_risk(
        disease_label=disease_result.label,
        confidence=disease_result.confidence,
        is_healthy=disease_result.is_healthy,
        severity_weight=kb_profile.get("severity_weight", 0.5),
        favourable_temp_range=kb_profile.get("favourable_temp_range"),
        favourable_humidity_min=kb_profile.get("favourable_humidity_min"),
        temperature_c=weather_data.temperature_c,
        humidity_pct=weather_data.humidity_pct,
        rain_probability_pct=weather_data.rain_probability_pct,
        low_confidence=disease_result.low_confidence
    )

    # 8. Generate IPM recommendations & plain-language explanation
    recommendations, explanation, sources = generate_recommendations(
        disease_entry=kb_profile,
        weather_data={
            "temperature_c": weather_data.temperature_c,
            "humidity_pct": weather_data.humidity_pct,
            "rain_probability_pct": weather_data.rain_probability_pct
        },
        risk_level=risk_result.level,
        risk_score=risk_result.score,
        confidence=disease_result.confidence,
        low_confidence=disease_result.low_confidence
    )

    # 8b. Multilingual summary for Indian farming languages
    affected_pct = disease_result.severity.affected_percentage if disease_result.severity else 0.0
    severity_lvl = disease_result.severity.level if disease_result.severity else "Mild"
    multilingual_summary = get_multilingual_diagnosis(
        crop=detected_crop,
        disease_label=disease_result.label,
        severity_level=severity_lvl,
        risk_level=risk_result.level,
        affected_percentage=affected_pct,
        is_healthy=disease_result.is_healthy
    )

    # 9. Database persistence
    analysis_id = 1
    try:
        # Resolve target crop record
        crop_record = None
        if farm_id:
            crop_record = db.query(Crop).filter(Crop.farm_id == farm_id).first()
        if not crop_record:
            crop_record = db.query(Crop).first()

        crop_id = crop_record.id if crop_record else None
        target_farm_id = farm_id or (crop_record.farm_id if crop_record else None)

        # Log weather record
        w_record = WeatherRecord(
            farm_id=target_farm_id,
            temperature=weather_data.temperature_c,
            humidity=weather_data.humidity_pct,
            rain_probability=weather_data.rain_probability_pct
        )
        db.add(w_record)

        # Prepare response payload
        temp_response = {
            "crop": detected_crop,
            "disease": disease_result.model_dump(),
            "weather": weather_data.model_dump(),
            "risk": risk_result.model_dump(),
            "recommendations": [r.model_dump() for r in recommendations],
            "explanation": explanation,
            "sources": sources,
            "multilingual_summary": multilingual_summary,
            "warnings": all_warnings
        }

        # Create CropAnalysis record
        analysis_record = CropAnalysis(
            crop_id=crop_id,
            disease=disease_result.label,
            confidence=disease_result.confidence,
            risk_level=risk_result.level,
            risk_score=risk_result.score,
            image_path=relative_image_path,
            response_json=temp_response
        )
        db.add(analysis_record)
        db.commit()
        db.refresh(analysis_record)
        analysis_id = analysis_record.id

    except Exception as db_err:
        db.rollback()
        logger.error(f"Database persistence failure in /api/analyze: {db_err}")
        all_warnings.append("Analysis result could not be permanently saved to local history.")

    return AnalyzeCropResponse(
        analysis_id=analysis_id,
        crop=detected_crop,
        disease=disease_result,
        weather=weather_data,
        risk=risk_result,
        recommendations=recommendations,
        explanation=explanation,
        sources=sources,
        multilingual_summary=multilingual_summary,
        warnings=all_warnings
    )
