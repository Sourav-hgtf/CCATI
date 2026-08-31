"""Backend Configuration Settings and Environment Settings (TASK 10 Hardened)."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Telecom Customer Churn Analysis Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "development"
    DEBUG: bool = False

    SECRET_KEY: str = "supersecret_key_change_in_production_environment_12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://localhost:8000"
    MAX_REQUEST_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB payload protection

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "database" / "telecom_churn.db"
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated allowed origins for CORS middleware."""
        if not self.ALLOWED_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
