"""Application configuration settings."""
import os
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./maintenance_wizard.db"
    
    # Application
    APP_NAME: str = "Maintenance Wizard"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # File Upload
    UPLOAD_DIR: Path = Path(__file__).parent.parent.parent / "data"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # RAG Configuration
    CHROMA_DB_DIR: Path = Path(__file__).parent.parent.parent / "chroma_db"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # LLM Configuration
    LLM_PROVIDER: str = "groq"  # "openai", "ollama", or "groq"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Allowed file types
    ALLOWED_PDF_TYPES: list[str] = ["application/pdf"]
    ALLOWED_CSV_TYPES: list[str] = ["text/csv", "application/vnd.ms-excel"]
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure upload directories exist
def ensure_upload_dirs():
    """Create all upload directories if they don't exist."""
    dirs = ["manuals", "sop", "maintenance_logs", "failure_reports", "sensor_data", "spares", "incidents", "rag_documents"]
    for dir_name in dirs:
        dir_path = settings.UPLOAD_DIR / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Ensure ChromaDB directory exists
    settings.CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

ensure_upload_dirs()