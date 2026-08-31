"""Backend Configuration Settings and Environment Settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Telecom Customer Churn Analysis Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "supersecret_key_change_in_production_environment_12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "database" / "telecom_churn.db"
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
