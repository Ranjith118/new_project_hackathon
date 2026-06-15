"""Application configuration settings."""
import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database — on Render the working dir is /opt/render/project/src/backend
    DATABASE_URL: str = "sqlite+aiosqlite:///./maintenance_wizard.db"

    # Application
    APP_NAME: str = "Maintenance Wizard"
    APP_VERSION: str = "9.0.0"
    DEBUG: bool = False

    # File Upload — use /tmp on Render (ephemeral but acceptable for uploads)
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "/tmp/maintenance_wizard/data"))
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB

    # RAG / ChromaDB — persisted inside the app working directory so it survives redeploys
    CHROMA_DB_DIR: Path = Path(os.getenv("CHROMA_DB_DIR", "./chroma_db"))
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # LLM
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Allowed file types
    ALLOWED_PDF_TYPES: list[str] = ["application/pdf"]
    ALLOWED_CSV_TYPES: list[str] = ["text/csv", "application/vnd.ms-excel"]

    # CORS — allow all origins so the Render static frontend can talk to the backend
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def ensure_upload_dirs() -> None:
    """Create all upload directories if they don't exist."""
    subdirs = [
        "manuals", "sop", "maintenance_logs", "failure_reports",
        "sensor_data", "spares", "incidents", "rag_documents",
    ]
    for d in subdirs:
        (settings.UPLOAD_DIR / d).mkdir(parents=True, exist_ok=True)

    settings.CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)


ensure_upload_dirs()
