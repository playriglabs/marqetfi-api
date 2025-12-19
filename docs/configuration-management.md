# Configuration Management

## Overview

MarqetFi API supports database-backed configuration management, allowing all settings and third-party provider configurations to be managed through the admin API without requiring application restarts or environment variable changes.

## Architecture

### Configuration Sources (Priority Order)

1. **Database Configuration** (Highest Priority)
   - Stored in `app_configurations` and `provider_configurations` tables
   - Managed through admin API
   - Supports encryption for sensitive values
   - Versioned for provider configurations

2. **Environment Variables** (Fallback)
   - Loaded from `.env` file
   - Used when database configuration is not available
   - Default values for initial setup

3. **Default Values** (Lowest Priority)
   - Hardcoded defaults in Settings class
   - Used only when neither DB nor env provides value

### Configuration Types

#### App-Level Configurations

Stored in `app_configurations` table:
- Application settings (DEBUG, ENVIRONMENT, etc.)
- Security settings (SECRET_KEY, token expiration, etc.)
- Database/Redis/Celery connection strings
- CORS settings
- Logging configuration

#### Provider Configurations

Stored in `provider_configurations` table:
- **Trading Providers**: Ostium, Lighter
- **Price Providers**: Ostium, Lighter
- **Settlement Providers**: Ostium, Lighter
- **Swap Providers**: LI-FI, Symbiosis
- **Wallet Providers**: Privy, Dynamic

## Database Models

### AppConfiguration

Stores application-level settings:

```python
{
    "config_key": "SECRET_KEY",
    "config_value": "encrypted-value",
    "config_type": "string",  # string, int, float, bool, json
    "category": "security",
    "is_encrypted": true,
    "is_active": true
}
```

### ProviderConfiguration

Stores provider-specific settings:

```python
{
    "provider_name": "lifi",
    "provider_type": "swap",
    "config_data": {
        "enabled": true,
        "api_url": "https://li.xyz/v1",
        "api_key": "encrypted-key",
        "timeout": 30
    },
    "is_active": true,
    "version": 1
}
```

## Admin API Endpoints

### App Configuration Management

#### List App Configurations

```http
GET /api/v1/admin/config/app-configs?category=security&skip=0&limit=100
Authorization: Bearer <admin-token>
```

#### Get App Configuration

```http
GET /api/v1/admin/config/app-configs/{config_id}
Authorization: Bearer <admin-token>
```

#### Create App Configuration

```http
POST /api/v1/admin/config/app-configs
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "config_key": "SECRET_KEY",
  "config_value": "new-secret-key",
  "config_type": "string",
  "category": "security",
  "description": "Application secret key",
  "is_encrypted": true,
  "is_active": true
}
```

#### Update App Configuration

```http
PUT /api/v1/admin/config/app-configs/{config_id}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "config_value": "updated-value",
  "is_active": false
}
```

### Provider Configuration Management

#### List Provider Configurations

```http
GET /api/v1/admin/config/provider-configs?provider_name=lifi&provider_type=swap
Authorization: Bearer <admin-token>
```

#### Get Provider Configuration

```http
GET /api/v1/admin/config/provider-configs/{config_id}
Authorization: Bearer <admin-token>
```

#### Create Provider Configuration

```http
POST /api/v1/admin/config/provider-configs
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "provider_name": "lifi",
  "provider_type": "swap",
  "config_data": {
    "enabled": true,
    "api_url": "https://li.xyz/v1",
    "api_key": "your-api-key",
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1.0
  },
  "activate": true
}
```

#### Activate Provider Configuration

```http
POST /api/v1/admin/config/provider-configs/{config_id}/activate
Authorization: Bearer <admin-token>
```

## Configuration Loading Flow

```
Application Startup
    ↓
Load Settings from .env (defaults)
    ↓
When Provider/Config Needed:
    ↓
1. Check Database (ConfigurationService)
    ↓
2. If found → Use Database Config
    ↓
3. If not found → Use Environment Variable
    ↓
4. If not found → Use Default Value
```

## Encryption

Sensitive values (private keys, API secrets) are automatically encrypted when stored in the database:

- Encryption uses Fernet (symmetric encryption)
- Key derived from `SECRET_KEY` using PBKDF2
- Values marked with `is_encrypted=true` are encrypted/decrypted automatically

## Usage Examples

### Python Example

```python
from app.services.configuration_service import ConfigurationService
from app.core.database import get_db

# Get configuration from database
async with get_db() as db:
    config_service = ConfigurationService(db)

    # Get app config
    secret_key = await config_service.get_app_config("SECRET_KEY")

    # Get provider config
    lifi_config = await config_service.get_provider_config("lifi", "swap")

    # Get config with fallback
    timeout = await config_service.get_config_with_fallback(
        "lifi_timeout",
        default=30
    )
```

### Admin API Example

```python
import httpx

# Create provider configuration
response = httpx.post(
    "https://api.example.com/api/v1/admin/config/provider-configs",
    headers={"Authorization": "Bearer <admin-token>"},
    json={
        "provider_name": "lifi",
        "provider_type": "swap",
        "config_data": {
            "enabled": True,
            "api_url": "https://li.xyz/v1",
            "api_key": "new-api-key",
            "timeout": 30
        },
        "activate": True
    }
)
```

## Migration from Environment Variables

To migrate existing `.env` configurations to database:

1. Use admin API to create configurations
2. System will automatically use database configs
3. Keep `.env` as fallback for initial setup
4. Gradually move all configs to database

## Best Practices

1. **Sensitive Values**: Always mark as `is_encrypted=true`
2. **Versioning**: Provider configs are versioned - create new version instead of updating active
3. **Activation**: Use activate endpoint to switch between config versions
4. **Categories**: Use consistent categories for app configs (security, database, etc.)
5. **Fallback**: Keep `.env` file with defaults for initial setup

## Configuration Categories

### App Configuration Categories

- `app`: Application settings (DEBUG, ENVIRONMENT, etc.)
- `security`: Security settings (SECRET_KEY, token expiration)
- `database`: Database connection settings
- `redis`: Redis connection settings
- `celery`: Celery configuration
- `cors`: CORS settings
- `logging`: Logging configuration
- `api`: API settings (prefixes, docs URLs)

### Provider Types

- `trading`: Trading provider configs (Ostium, Lighter)
- `price`: Price provider configs (Ostium, Lighter)
- `settlement`: Settlement provider configs (Ostium, Lighter)
- `swap`: Swap provider configs (LI-FI, Symbiosis)
- `wallet`: Wallet provider configs (Privy, Dynamic)

## Troubleshooting

### Configuration Not Applied

1. Check if configuration is active (`is_active=true`)
2. Verify database connection
3. Check application logs for configuration loading errors
4. Ensure admin user has proper permissions

### Encryption Issues

1. Verify `SECRET_KEY` is set correctly
2. Check if value was encrypted with same key
3. Review encryption utility logs

### Provider Not Loading

1. Check provider configuration exists in database
2. Verify `is_active=true` for provider config
3. Check provider name and type match exactly
4. Review factory logs for loading errors
