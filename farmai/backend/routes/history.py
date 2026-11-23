"""History API route retrieving saved crop diagnostic records.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.database import get_db
from database.orm_models import CropAnalysis, Crop
from schemas import HistoryItem

router = APIRouter(prefix="/api", tags=["History"])


@router.get(
    "/history",
    response_model=List[HistoryItem],
    summary="Get past crop disease diagnosis history"
)
def get_history(
    farm_id: Optional[int] = Query(default=None, description="Optional farm ID filter"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db)
):
    """Retrieve historical crop analyses with disease classification and risk metrics."""
    query = db.query(CropAnalysis).join(Crop, isouter=True)
    if farm_id:
        query = query.filter(Crop.farm_id == farm_id)

    records = query.order_by(desc(CropAnalysis.created_at)).limit(limit).all()
    results: List[HistoryItem] = []
    for r in records:
        crop_name = r.crop.crop_name if r.crop else "Tomato"
        results.append(
            HistoryItem(
                id=r.id,
                crop=crop_name,
                disease_label=r.disease,
                confidence=r.confidence,
                risk_level=r.risk_level,
                risk_score=r.risk_score,
                created_at=r.created_at.isoformat() if r.created_at else "",
                image_path=r.image_path,
                response_json=r.response_json
            )
        )
    return results
