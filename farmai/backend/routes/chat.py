"""Farmer agricultural assistant chat API route.

POST /api/chat
- Accepts a natural-language question, optional analysis_id (for context),
  and a language code (en / kn / hi).
- Retrieves relevant IPM knowledge-base chunks via RAG.
- Calls the LLM (Anthropic) if key is configured; else uses a grounded
  template fallback.
- Returns the answer, source citations, and a grounded flag.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas import ChatRequest, ChatResponse
from database.database import get_db
from database.orm_models import CropAnalysis
from services.chat_service import chat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask FarmAI assistant agricultural and disease queries",
)
async def chat_with_assistant(
    payload: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Answers farmer queries grounded in IPM agricultural knowledge base.

    Optionally enriches the prompt with context from a previous analysis
    identified by *analysis_id*.
    """
    # Build extra context from stored analysis if provided
    analysis_context = ""
    if payload.analysis_id is not None:
        try:
            record: Optional[CropAnalysis] = (
                db.query(CropAnalysis).filter(CropAnalysis.id == payload.analysis_id).first()
            )
            if record:
                crop_name = record.crop.crop_name if record.crop else "Tomato"
                analysis_context = (
                    f"Crop: {crop_name}, "
                    f"Disease: {record.disease} "
                    f"(confidence {record.confidence:.0%}), "
                    f"Risk: {record.risk_level} ({record.risk_score}/100)."
                )
        except Exception as exc:
            logger.warning("Could not load analysis %s: %s", payload.analysis_id, exc)

    answer, sources, grounded = await chat(
        message=payload.message,
        analysis_context=analysis_context,
        language=payload.language,
    )

    return ChatResponse(answer=answer, sources=sources, grounded=grounded)
