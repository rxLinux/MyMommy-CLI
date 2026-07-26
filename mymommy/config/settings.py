from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "MyMommy-CLI"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Model Settings
    DEFAULT_MODEL: str = "gemma3:12b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Licensing
    FREE_TOKEN_LIMIT: int = 450000
    BACKEND_URL: str = "http://localhost:8000"
    
    # Storage
    DOT_DIR: str = ".mymommy"

    @property
    def dot_path(self) -> Path:
        path = Path.cwd() / self.DOT_DIR
        path.mkdir(exist_ok=True)
        return path

    @property
    def db_path(self) -> Path:
        return self.dot_path / "history.db"

settings = Settings()
