"""Application configuration module using pydantic-settings.
"""
from typing import List, Union
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Central configuration class loading values from environment or .env file."""
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = f"sqlite:///{BASE_DIR / 'farmai.db'}"
    cors_origins: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    demo_mode: bool = False
    model_weights_path: str = str(BASE_DIR / "models" / "weights" / "model.keras")
    class_names_path: str = str(BASE_DIR / "models" / "weights" / "class_names.json")
    diseases_kb_path: str = str(BASE_DIR / "knowledge_base" / "diseases.json")
    
    open_meteo_timeout: float = 5.0

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
