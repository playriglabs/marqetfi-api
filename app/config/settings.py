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

    # Provider Selection
    TRADING_PROVIDER: str = "ostium"
    PRICE_PROVIDER: str = "ostium"
    SETTLEMENT_PROVIDER: str = "ostium"

    # Ostium Settings (backward compatible)
    private_key: str = ""
    rpc_url: str = ""
    network: str = "testnet"
    ostium_verbose: bool = False

    # Ostium Provider Settings (new format)
    ostium_enabled: bool = True
    ostium_private_key: str = ""
    ostium_rpc_url: str = ""
    ostium_network: str = "testnet"
    ostium_slippage_percentage: float = 1.0
    ostium_timeout: int = 30
    ostium_retry_attempts: int = 3
    ostium_retry_delay: float = 1.0

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def get_ostium_network_config(self):
        """Get Ostium network config (backward compatible)."""
        network = self.ostium_network or self.network
        if network.lower() == "testnet":
            return NetworkConfig.testnet()
        return NetworkConfig.mainnet()

    def create_ostium_sdk(self):
        """Create Ostium SDK instance (backward compatible)."""
        config = self.get_ostium_network_config()
        private_key = self.ostium_private_key or self.private_key
        rpc_url = self.ostium_rpc_url or self.rpc_url
        verbose = self.ostium_verbose
        return OstiumSDK(
            config,
            private_key,
            rpc_url,
            verbose=verbose,
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

