# Multi-Provider Routing

## Overview

The system now supports using multiple providers simultaneously, routing requests to the appropriate provider based on asset type or category.

- **Lighter**: Crypto assets (BTC, ETH, SOL, etc.)
- **Ostium**: TradFi assets (Forex, Indices, Commodities)

## How It Works

### Automatic Routing

The `ProviderRouter` automatically routes requests based on:

1. **Asset Symbol** (e.g., "BTC", "EURUSD")
2. **Asset Type** (numeric ID, e.g., 0=BTC, 1=ETH)
3. **Category** (crypto, forex, indices, commodities)

### Default Routing

- **Crypto assets** → Lighter
- **Forex/Indices/Commodities** → Ostium

## Configuration

### Environment Variables

```env
# Enable both providers
LIGHTER_ENABLED=true
OSTIUM_ENABLED=true

# Custom asset routing (optional)
# Format: JSON object mapping assets to providers
ASSET_ROUTING='{"BTC":"lighter","ETH":"lighter","EURUSD":"ostium","XAUUSD":"ostium"}'
```

### Programmatic Configuration

```python
from app.services.providers.router import get_provider_router

router = get_provider_router()

# Configure category-to-provider mapping
router.configure_category_provider("crypto", "lighter")
router.configure_category_provider("forex", "ostium")

# Configure specific asset routing
router.configure_asset_provider("BTC", "lighter")
router.configure_asset_provider("EURUSD", "ostium")
```

## Usage

### Trading

When creating a trade, include the `asset` field for automatic routing:

```json
{
  "collateral": 1000.0,
  "leverage": 10,
  "asset_type": 0,
  "asset": "BTC",  // Optional: helps with routing
  "direction": true,
  "order_type": "MARKET"
}
```

The system will:
1. Check if `asset` is provided → route to appropriate provider
2. Otherwise, use `asset_type` to determine provider
3. Fallback to default provider if routing fails

### Price Feeds

Price requests automatically route based on asset symbol:

```bash
# Crypto price → Lighter
GET /api/v1/prices/BTC/USD

# Forex price → Ostium
GET /api/v1/prices/EURUSD/USD
```

### Trading Pairs

Get pairs from all providers or filter by category:

```bash
# All pairs from all providers
GET /api/v1/trading/pairs

# Only crypto pairs (from Lighter)
GET /api/v1/trading/pairs?category=crypto

# Only forex pairs (from Ostium)
GET /api/v1/trading/pairs?category=forex
```

## Asset Categories

### Crypto (Lighter)
- BTC, ETH, SOL, AVAX, MATIC, ARB, OP, LINK, UNI, etc.

### TradFi (Ostium)
- **Forex**: EURUSD, GBPUSD, USDJPY, etc.
- **Indices**: SPX, NASDAQ, etc.
- **Commodities**: XAUUSD (Gold), XAGUSD (Silver), etc.

## Routing Priority

1. **Direct Asset Mapping** (`ASSET_ROUTING` or `configure_asset_provider`)
2. **Category Mapping** (crypto → lighter, tradfi → ostium)
3. **Asset Type Mapping** (numeric asset types)
4. **Default Provider** (falls back to configured default)

## Examples

### Example 1: Crypto Trade

```python
# Automatically routes to Lighter
trade = {
    "collateral": 1000,
    "leverage": 10,
    "asset_type": 0,  # BTC
    "asset": "BTC",   # Explicit routing
    "direction": True,
    "order_type": "MARKET"
}
```

### Example 2: Forex Trade

```python
# Automatically routes to Ostium
trade = {
    "collateral": 1000,
    "leverage": 20,
    "asset_type": 10,  # EURUSD (example)
    "asset": "EURUSD",  # Explicit routing
    "direction": True,
    "order_type": "LIMIT",
    "at_price": 1.0850
}
```

### Example 3: Mixed Price Query

```python
# Fetches BTC from Lighter, EURUSD from Ostium
prices = await price_service.get_prices([
    ("BTC", "USD"),    # → Lighter
    ("EURUSD", "USD")  # → Ostium
])
```

## Backward Compatibility

The system maintains backward compatibility:

- If a single provider is configured, it works as before
- Services can still accept explicit providers
- Default routing can be overridden per request

## Troubleshooting

### Provider Not Found

If a provider is not available, the system will:
1. Log a warning
2. Try the fallback provider
3. Return an error if no providers are available

### Routing Conflicts

If an asset is mapped to multiple providers:
- Direct asset mapping takes precedence
- Category mapping is secondary
- Asset type mapping is last resort
