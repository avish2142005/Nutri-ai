"""SQLAlchemy ORM models matching FarmAI database schema.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """Authenticated user account entity."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="farmer", nullable=False)
    preferred_language = Column(String(10), default="en", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Farmer(Base):
    """Farmer profile entity."""
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    location = Column(String(200), nullable=False)

    farms = relationship("Farm", back_populates="farmer", cascade="all, delete-orphan")


class Farm(Base):
    """Farm land parcel entity."""
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    area = Column(Float, nullable=True)  # in acres / hectares
    soil_type = Column(String(50), nullable=True)

    farmer = relationship("Farmer", back_populates="farms")
    crops = relationship("Crop", back_populates="farm", cascade="all, delete-orphan")
    weather_records = relationship("WeatherRecord", back_populates="farm", cascade="all, delete-orphan")


class Crop(Base):
    """Crop planted in a farm."""
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    crop_name = Column(String(50), nullable=False)
    planting_date = Column(String(20), nullable=True)
    growth_stage = Column(String(50), nullable=True)

    farm = relationship("Farm", back_populates="crops")
    analyses = relationship("CropAnalysis", back_populates="crop", cascade="all, delete-orphan")


class CropAnalysis(Base):
    """Crop disease diagnosis and risk analysis records."""
    __tablename__ = "crop_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=True)
    disease = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    risk_score = Column(Integer, nullable=False)
    image_path = Column(String(500), nullable=True)
    response_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    crop = relationship("Crop", back_populates="analyses")


class WeatherRecord(Base):
    """Weather log records."""
    __tablename__ = "weather"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    rain_probability = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    farm = relationship("Farm", back_populates="weather_records")
