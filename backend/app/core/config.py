"""Backend Configuration Settings and Environment Settings (TASK 10 Hardened, TASK 12 Observability)."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Telecom Customer Churn Analysis Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "development"
    DEBUG: bool = False

    SECRET_KEY: str = "supersecret_key_change_in_production_environment_12345"
    JWT_SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # Short-lived 1-hour access token
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days refresh token
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15

    @property
    def get_jwt_secret(self) -> str:
        return self.JWT_SECRET_KEY if self.JWT_SECRET_KEY else self.SECRET_KEY

    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://localhost:8000"
    MAX_REQUEST_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB payload protection

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    
    # Database Settings
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/telecom_churn"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    
    # Fallback to local SQLite for local dev when PostgreSQL is not running
    USE_SQLITE_FALLBACK: bool = True
    DB_PATH: Path = DATA_DIR / "database" / "telecom_churn.db"
    
    @property
    def get_database_url(self) -> str:
        if self.USE_SQLITE_FALLBACK or self.DATABASE_URL.startswith("sqlite"):
            return f"sqlite:///{self.DB_PATH}"
        return self.DATABASE_URL

    # ── Rate Limiting & Abuse Protection (TASK 19) ───────────────────────────
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_PER_MINUTE: int = 15
    RATE_LIMIT_PREDICTION_PER_MINUTE: int = 60
    RATE_LIMIT_READ_PER_MINUTE: int = 120
    RATE_LIMIT_ADMIN_PER_MINUTE: int = 30
    RATE_LIMIT_EXPORT_PER_MINUTE: int = 10

    # Pagination Protection
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Trusted Proxies for IP Resolution
    TRUSTED_PROXIES: str = "127.0.0.1,::1"

    # Security Headers
    ENABLE_HSTS: bool = False  # Set to True in production with TLS

    @property
    def trusted_proxy_list(self) -> list[str]:
        if not self.TRUSTED_PROXIES:
            return ["127.0.0.1", "::1"]
        return [ip.strip() for ip in self.TRUSTED_PROXIES.split(",") if ip.strip()]

    # ── Observability (TASK 12) ──────────────────────────────────────────────
    # LOG_LEVEL: Python logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_LEVEL: str = "INFO"
    # LOG_FORMAT: "json" for production structured logs, "text" for human-readable dev output
    LOG_FORMAT: str = "json"
    # ENABLE_AUDIT_LOGGING: write business-event audit records to SQLite audit_logs table
    ENABLE_AUDIT_LOGGING: bool = True
    # ENABLE_METRICS: collect in-memory operational metrics exposed at /api/v1/metrics
    ENABLE_METRICS: bool = True
    # AUDIT_RETENTION_DAYS: purge audit records older than N days (0 = no automatic purge)
    AUDIT_RETENTION_DAYS: int = 90
    # REQUEST_ID_HEADER: primary header name used to propagate correlation IDs
    REQUEST_ID_HEADER: str = "X-Request-ID"

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated allowed origins for CORS middleware."""
        if not self.ALLOWED_ORIGINS:
            return ["http://localhost:5173", "http://127.0.0.1:5173"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

