"""Application settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings
from ostium_python_sdk import OstiumSDK, NetworkConfig


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "MarqetFi API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/dbname"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 10

    # Celery
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True

    # Security
    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # API
    API_V1_PREFIX: str = "/api/v1"
    DOCS_URL: str | None = "/docs"
    REDOC_URL: str | None = "/redoc"

    # Ostium Settings
    private_key: str = ""
    rpc_url: str = ""
    network: str = "testnet"
    ostium_verbose: bool = False

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def get_ostium_network_config(self):
        """Get Ostium network config."""
        if self.network.lower() == "testnet":
            return NetworkConfig.testnet()
        return NetworkConfig.mainnet()

    def create_ostium_sdk(self):
        """Create Ostium SDK instance."""
        config = self.get_ostium_network_config()
        return OstiumSDK(
            config,
            self.private_key,
            self.rpc_url,
            verbose=self.ostium_verbose
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

