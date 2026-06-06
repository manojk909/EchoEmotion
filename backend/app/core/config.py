"""Application configuration via Pydantic Settings."""
from functools import lru_cache
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # ── App ───────────────────────────────────────────
    APP_NAME: str = "EchoEmotion"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-32chars!!"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── Database ──────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://ser_user:ser_pass@localhost:5432/ser_db"
    DATABASE_URL_SYNC: str = "postgresql://ser_user:ser_pass@localhost:5432/ser_db"

    # ── Auth ──────────────────────────────────────────
    JWT_SECRET_KEY: str = "jwt-secret-key-change-me-32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 h

    # ── ML ────────────────────────────────────────────
    MODELS_DIR: Path = ROOT_DIR / "models"
    DATASET_PATH: Path = ROOT_DIR / "dataset"
    UPLOAD_FOLDER: Path = ROOT_DIR / "uploads"
    MAX_UPLOAD_SIZE_MB: int = 16
    ALLOWED_AUDIO_EXTENSIONS: List[str] = ["wav", "mp3", "ogg", "flac", "m4a"]

    N_MFCC: int = 40
    SAMPLE_RATE: int = 22050

    OBSERVED_EMOTIONS: List[str] = ["calm", "happy", "fearful", "disgust"]

    # ── Rate limiting ─────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 30
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def models_dir(self) -> Path:
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        return self.MODELS_DIR

    @property
    def upload_folder(self) -> Path:
        self.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        return self.UPLOAD_FOLDER


EMOTIONS_MAP: dict = {
    "01": "neutral", "02": "calm", "03": "happy", "04": "sad",
    "05": "angry", "06": "fearful", "07": "disgust", "08": "surprised",
}


@lru_cache
def get_settings() -> Settings:
    return Settings()
