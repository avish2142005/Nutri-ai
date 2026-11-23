"""FarmAI FastAPI Application Entry Point.
"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from schemas import HealthResponse
from database.database import init_db
from models.disease_model import is_model_loaded, is_demo_mode
from routes import crop, weather, irrigation, satellite, chat, history, auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("farmai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager: handles startup and shutdown."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    logger.info("Starting up FarmAI API Server...")
    # Initialize DB tables and demo seed
    init_db()

    # Pre-build RAG index in background thread (non-blocking)
    try:
        from services.rag_service import build_index, _chunks
        if not _chunks:
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor(max_workers=1)
            loop.run_in_executor(executor, build_index)
            logger.info("RAG index build scheduled in background thread.")
    except Exception as exc:
        logger.warning("RAG index pre-build skipped: %s", exc)

    yield
    logger.info("Shutting down FarmAI API Server...")


app = FastAPI(
    title="KrishiNetra - AI-Powered Agricultural Intelligence Platform",
    description="Enterprise agricultural decision-support and disease diagnostic intelligence platform combining EfficientNetB3/ResNet50/MobileNetV2 deep learning architectures, hybrid computer vision severity estimation, live weather pathogen risk, and multilingual advisories.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
origins = settings.cors_origins if isinstance(settings.cors_origins, list) else [settings.cors_origins]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for previewing uploaded leaf images
uploads_dir = Path(__file__).resolve().parent / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check endpoint indicating model state and demo mode status."""
    return HealthResponse(
        status="ok",
        model_loaded=is_model_loaded(),
        demo_mode=is_demo_mode()
    )


# Include API routers
app.include_router(auth.router)
app.include_router(crop.router)
app.include_router(weather.router)
app.include_router(irrigation.router)
app.include_router(satellite.router)
app.include_router(chat.router)
app.include_router(history.router)

# Serve built frontend in production if dist directory exists
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    logger.info("Mounted production frontend SPA from %s", frontend_dist)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
