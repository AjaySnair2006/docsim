"""
Central configuration for the backend.
All configurable values are read from environment variables (see .env.example).
Never hardcode secrets or paths directly in code — add them here instead.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # loads variables from a .env file if present


BASE_DIR = Path(__file__).resolve().parent.parent  # backend/

class Settings:
    # --- App info ---
    APP_NAME: str = os.getenv("APP_NAME", "AI Document Similarity Detection System")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # --- CORS ---
    # Comma separated list of allowed origins, e.g. "http://localhost:5173,http://localhost:3000"
    ALLOWED_ORIGINS: list[str] = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")

    # --- File storage ---
    UPLOAD_DIR: Path = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
    REPORT_DIR: Path = BASE_DIR / os.getenv("REPORT_DIR", "reports")

    # --- Upload validation ---
    ALLOWED_EXTENSIONS: set = {".pdf"}
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    # --- Similarity thresholds (used by the report/comparison module) ---
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.75"))
    CONTENT_SIMILARITY_THRESHOLD: float = float(
        os.getenv("CONTENT_SIMILARITY_THRESHOLD", "0.45")
    )
    CONTENT_SIMILARITY_MODEL: str = os.getenv(
        "CONTENT_SIMILARITY_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # --- Any API keys used by the AI/ML module go here, pulled from env ---
    # Example: OPENAI_API_KEY, HUGGINGFACE_API_KEY, etc.
    AI_MODULE_API_KEY: str = os.getenv("AI_MODULE_API_KEY", "")


settings = Settings()

# Ensure required directories exist at startup
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORT_DIR.mkdir(parents=True, exist_ok=True)
