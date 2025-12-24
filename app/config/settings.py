"""Application settings."""

from functools import lru_cache

from ostium_python_sdk import NetworkConfig, OstiumSDK
from pydantic import Field
from pydantic_settings import BaseSettings


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

    # Auth0 Configuration
    AUTH0_DOMAIN: str = ""
    AUTH0_CLIENT_ID: str = ""
    AUTH0_CLIENT_SECRET: str = ""
    AUTH0_AUDIENCE: str = ""
    AUTH0_ALGORITHM: str = "RS256"
    AUTH0_MANAGEMENT_CLIENT_ID: str = ""
    AUTH0_MANAGEMENT_CLIENT_SECRET: str = ""
    AUTH0_GOOGLE_ENABLED: bool = True
    AUTH0_APPLE_ENABLED: bool = True
    AUTH0_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/oauth/callback"

    # Wallet Provider Configuration
    WALLET_PROVIDER: str = Field(
        default="none",
        description="Wallet provider name (privy/dynamic/none)",
    )

    # Privy Configuration
    PRIVY_ENABLED: bool = Field(default=True, description="Enable Privy wallet provider")
    PRIVY_APP_ID: str = Field(default="", description="Privy App ID")
    PRIVY_APP_SECRET: str = Field(default="", description="Privy App Secret")
    PRIVY_API_URL: str = Field(
        default="https://api.privy.io",
        description="Privy API base URL",
    )
    PRIVY_USE_EMBEDDED_WALLETS: bool = Field(
        default=True,
        description="Use Privy embedded wallets",
    )
    PRIVY_TIMEOUT: int = Field(default=30, description="Privy API timeout in seconds")
    PRIVY_RETRY_ATTEMPTS: int = Field(default=3, description="Privy retry attempts")
    PRIVY_RETRY_DELAY: float = Field(default=1.0, description="Privy retry delay in seconds")

    # Dynamic Configuration
    DYNAMIC_ENABLED: bool = Field(default=True, description="Enable Dynamic wallet provider")
    DYNAMIC_API_KEY: str = Field(default="", description="Dynamic API key")
    DYNAMIC_API_SECRET: str = Field(default="", description="Dynamic API secret")
    DYNAMIC_API_URL: str = Field(
        default="https://api.dynamic.xyz",
        description="Dynamic API base URL",
    )
    DYNAMIC_ENVIRONMENT: str = Field(
        default="production",
        description="Dynamic environment (production/sandbox)",
    )
    DYNAMIC_TIMEOUT: int = Field(default=30, description="Dynamic API timeout in seconds")
    DYNAMIC_RETRY_ATTEMPTS: int = Field(default=3, description="Dynamic retry attempts")
    DYNAMIC_RETRY_DELAY: float = Field(default=1.0, description="Dynamic retry delay in seconds")

    # Ostium Wallet Provider Settings
    OSTIUM_USE_WALLET_PROVIDER: bool = Field(
        default=False,
        description="Enable wallet provider integration for Ostium",
    )
    OSTIUM_FALLBACK_TO_PRIVATE_KEY: bool = Field(
        default=True,
        description="Fall back to private key if wallet provider fails",
    )
    OSTIUM_WALLET_PROVIDER_ID: str | None = Field(
        default=None,
        description="Provider-specific wallet ID for Ostium (optional)",
    )

    # Legacy Wallet Configuration (kept for backward compatibility)
    ENABLE_MPC_WALLETS: bool = True
    ENABLE_EXTERNAL_WALLETS: bool = True

    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = Field(
        default="pretty",
        description="Log format: 'pretty' for colored human-readable (dev), 'json' for structured logs (prod)",
    )

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

    # Lighter Provider Settings
    lighter_enabled: bool = True
    lighter_api_url: str = "https://api.lighter.xyz"
    lighter_api_key: str | None = None
    lighter_private_key: str | None = None
    lighter_network: str = "mainnet"
    lighter_timeout: int = 30
    lighter_retry_attempts: int = 3
    lighter_retry_delay: float = 1.0

    # Multi-Provider Routing Configuration
    # Format: JSON string mapping assets to providers
    # Example: '{"BTC":"lighter","ETH":"lighter","EURUSD":"ostium","XAUUSD":"ostium"}'
    ASSET_ROUTING: dict[str, str] = Field(
        default_factory=dict,
        description="Asset-to-provider routing map (overrides category defaults)",
    )

    # Swap Provider Settings
    SWAP_PROVIDER: str = Field(default="lifi", description="Default swap provider (lifi)")
    LIFI_API_URL: str = Field(default="https://li.xyz/v1", description="LI-FI API base URL")
    LIFI_API_KEY: str | None = Field(default=None, description="LI-FI API key (if required)")
    lifi_enabled: bool = Field(default=True, description="Enable LI-FI swap provider")
    lifi_timeout: int = Field(default=30, description="LI-FI request timeout in seconds")
    lifi_retry_attempts: int = Field(default=3, description="LI-FI retry attempts")
    lifi_retry_delay: float = Field(default=1.0, description="LI-FI retry delay in seconds")

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # Allow case-insensitive env vars (PRIVATE_KEY = private_key)
        extra = "ignore"  # Ignore extra fields from .env that don't match model fields

    def get_ostium_network_config(self) -> NetworkConfig:
        """Get Ostium network config (backward compatible)."""
        network = self.ostium_network or self.network
        if network.lower() == "testnet":
            return NetworkConfig.testnet()
        return NetworkConfig.mainnet()

    def create_ostium_sdk(self) -> OstiumSDK:
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
