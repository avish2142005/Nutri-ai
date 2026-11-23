"""Database session management and schema initialisation.
"""
import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings
# pyrefly: ignore [missing-import]
from database.orm_models import Base, Farmer, Farm, Crop

logger = logging.getLogger(__name__)

# Configure connect_args only for SQLite
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency yield for FastAPI request lifecycle."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables and seed baseline demo data."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if demo farmer already seeded
        farmer = db.query(Farmer).first()
        if not farmer:
            logger.info("Seeding demo farmer, farm in Udupi, and Tomato crop...")
            demo_farmer = Farmer(
                name="Ramesh Patel",
                phone="+91-9876543210",
                location="Udupi, Karnataka, India"
            )
            db.add(demo_farmer)
            db.flush()

            demo_farm = Farm(
                farmer_id=demo_farmer.id,
                latitude=13.3409,
                longitude=74.7421,
                area=2.5,
                soil_type="Red Sandy Loam"
            )
            db.add(demo_farm)
            db.flush()

            demo_crop = Crop(
                farm_id=demo_farm.id,
                crop_name="Tomato",
                planting_date="2026-08-15",
                growth_stage="Flowering to Early Fruiting"
            )
            db.add(demo_crop)
            db.commit()
            logger.info("Demo data seeding completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during database initialization/seeding: {e}")
    finally:
        db.close()
