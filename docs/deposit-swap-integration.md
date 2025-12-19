# Deposit & Swap Integration

## Overview

The deposit system allows users to deposit any stablecoin on any blockchain. The system automatically detects if a token swap is needed based on provider requirements and executes the swap using configured swap providers (LI-FI or Symbiosis).

For example, Ostium (HyperEVM) requires USDC on Arbitrum. If a user deposits USDT on Ethereum, the system will automatically swap it to USDC on Arbitrum.

## Architecture

### Swap Provider Pattern

The system uses a provider pattern for swap services, similar to trading and price providers:

- **BaseSwapProvider**: Abstract interface for swap operations
- **LifiSwapProvider**: LI-FI implementation for cross-chain swaps
- **SymbiosisSwapProvider**: Symbiosis implementation (placeholder for future)

### Components

1. **Deposit Service**: Manages deposits and triggers automatic swaps
2. **Swap Provider Factory**: Creates and manages swap provider instances
3. **Deposit Models**: Database models for tracking deposits and swaps
4. **Provider Token Configuration**: Configurable token requirements per provider

## Provider Token Requirements

Each trading provider has specific token and chain requirements:

### Ostium (HyperEVM)
- **Required Token**: USDC
- **Required Chain**: Arbitrum
- **Token Address**: Configurable via `ostium_required_token_address`

### Lighter
- **Required Token**: USDC (configurable)
- **Required Chain**: Ethereum (configurable)
- **Token Address**: Configurable via `lighter_required_token_address`

## Deposit Flow

1. User deposits any stablecoin on any chain
2. Deposit Service receives deposit information
3. System checks if swap is needed by comparing:
   - Deposit token vs. provider required token
   - Deposit chain vs. provider required chain
4. If swap needed:
   - Get swap provider (LI-FI/Symbiosis)
   - Get swap quote
   - Execute swap (requires wallet signing)
   - Track swap status
5. Update deposit status based on swap completion
6. If no swap needed: Mark deposit as completed

## Configuration

### Swap Provider Settings

```env
# Default swap provider (lifi or symbiosis)
SWAP_PROVIDER=lifi

# LI-FI Configuration
LIFI_API_URL=https://li.xyz/v1
LIFI_API_KEY=your_api_key_here
lifi_enabled=true
lifi_timeout=30
lifi_retry_attempts=3
lifi_retry_delay=1.0

# Symbiosis Configuration (future)
SYMBIOSIS_API_URL=https://api.symbiosis.finance
```

### Provider Token Requirements

```env
# Ostium Requirements
ostium_required_token=USDC
ostium_required_chain=arbitrum
ostium_required_token_address=0x...

# Lighter Requirements
lighter_required_token=USDC
lighter_required_chain=ethereum
lighter_required_token_address=0x...
```

## API Endpoints

### Create Deposit

```http
POST /api/v1/deposits
Authorization: Bearer <token>
Content-Type: application/json

{
  "token_address": "0x...",
  "token_symbol": "USDT",
  "chain": "ethereum",
  "amount": "1000.0",
  "provider": "ostium",
  "transaction_hash": "0x..." // optional
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 123,
  "token_address": "0x...",
  "token_symbol": "USDT",
  "chain": "ethereum",
  "amount": "1000.0",
  "status": "processing",
  "provider": "ostium",
  "transaction_hash": "0x...",
  "created_at": "2025-01-21T12:00:00Z",
  "updated_at": "2025-01-21T12:00:00Z"
}
```

### List Deposits

```http
GET /api/v1/deposits?skip=0&limit=100&status=pending&provider=ostium
Authorization: Bearer <token>
```

**Response:**
```json
{
  "deposits": [
    {
      "id": 1,
      "user_id": 123,
      "token_address": "0x...",
      "token_symbol": "USDT",
      "chain": "ethereum",
      "amount": "1000.0",
      "status": "processing",
      "provider": "ostium",
      "transaction_hash": "0x...",
      "created_at": "2025-01-21T12:00:00Z",
      "updated_at": "2025-01-21T12:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

### Get Deposit Details

```http
GET /api/v1/deposits/{deposit_id}
Authorization: Bearer <token>
```

### Get Swap Status

```http
GET /api/v1/deposits/{deposit_id}/swap-status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "deposit_id": 1,
  "swap_needed": true,
  "swaps": [
    {
      "id": 1,
      "status": "processing",
      "from_token": "0x...",
      "to_token": "0x...",
      "from_chain": "ethereum",
      "to_chain": "arbitrum",
      "amount": "1000.0",
      "estimated_output": "998.5",
      "actual_output": null,
      "transaction_hash": "0x...",
      "error": null
    }
  ]
}
```

## Swap Providers

### LI-FI

LI-FI is the default swap provider for cross-chain token swaps.

**Features:**
- Support for multiple chains
- Automatic routing for best rates
- Real-time quote updates

**Configuration:**
- API URL: `https://li.xyz/v1`
- Requires API key (optional for basic usage)

### Symbiosis (Future)

Symbiosis will be available as an alternative swap provider.

**Status:** Placeholder implementation ready for future integration

## Usage Examples

### Python Example

```python
import httpx

# Create deposit
response = httpx.post(
    "https://api.example.com/api/v1/deposits",
    headers={"Authorization": "Bearer <token>"},
    json={
        "token_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "token_symbol": "USDC",
        "chain": "ethereum",
        "amount": "1000.0",
        "provider": "ostium",
    }
)
deposit = response.json()

# Check swap status
swap_status = httpx.get(
    f"https://api.example.com/api/v1/deposits/{deposit['id']}/swap-status",
    headers={"Authorization": "Bearer <token>"}
).json()
```

### JavaScript Example

```javascript
// Create deposit
const deposit = await fetch('https://api.example.com/api/v1/deposits', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    token_address: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    token_symbol: 'USDC',
    chain: 'ethereum',
    amount: '1000.0',
    provider: 'ostium'
  })
}).then(r => r.json());

// Check swap status
const swapStatus = await fetch(
  `https://api.example.com/api/v1/deposits/${deposit.id}/swap-status`,
  {
    headers: { 'Authorization': 'Bearer <token>' }
  }
).then(r => r.json());
```

## Error Handling

### Common Errors

1. **Invalid Token**: Deposit token not supported
   - **Status Code**: 400
   - **Message**: "Unsupported token for swap"

2. **Insufficient Liquidity**: Not enough liquidity for swap
   - **Status Code**: 400
   - **Message**: "Insufficient liquidity for swap"

3. **Swap Failed**: Swap execution failed
   - **Status Code**: 500
   - **Message**: "Swap execution failed: <error details>"

4. **Provider Unavailable**: Swap provider not available
   - **Status Code**: 503
   - **Message**: "Swap provider unavailable"

### Retry Logic

- Failed swaps are automatically retried with exponential backoff
- Maximum retry attempts: 3 (configurable)
- Retry delay: 1.0 seconds (configurable)

## Database Models

### Deposit

Tracks user deposits with the following fields:
- `id`: Deposit ID
- `user_id`: User ID
- `token_address`: Token contract address
- `token_symbol`: Token symbol
- `chain`: Chain identifier
- `amount`: Deposit amount
- `status`: Deposit status (pending, processing, completed, failed)
- `provider`: Provider name (ostium, lighter)
- `transaction_hash`: Blockchain transaction hash
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### TokenSwap

Tracks swap transactions with the following fields:
- `id`: Swap ID
- `deposit_id`: Related deposit ID
- `from_token`: Source token address
- `to_token`: Destination token address
- `from_chain`: Source chain
- `to_chain`: Destination chain
- `amount`: Swap amount
- `swap_provider`: Swap provider (lifi, symbiosis)
- `swap_status`: Swap status (pending, processing, completed, failed)
- `swap_transaction_hash`: Swap transaction hash
- `estimated_output`: Estimated output amount
- `actual_output`: Actual output amount (when completed)
- `error_message`: Error message (if failed)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `completed_at`: Completion timestamp

## Status Flow

### Deposit Status
- `pending`: Deposit created, awaiting processing
- `processing`: Swap in progress
- `completed`: Deposit and swap (if needed) completed
- `failed`: Deposit or swap failed

### Swap Status
- `pending`: Swap quote obtained, awaiting execution
- `processing`: Swap transaction submitted
- `completed`: Swap successfully completed
- `failed`: Swap failed

## Best Practices

1. **Monitor Swap Status**: Regularly check swap status for pending deposits
2. **Handle Errors**: Implement proper error handling for failed swaps
3. **User Notifications**: Notify users when swaps complete or fail
4. **Gas Optimization**: Consider gas costs when executing swaps
5. **Rate Limiting**: Respect API rate limits for swap providers

## Troubleshooting

### Swap Not Executing

- Check swap provider configuration
- Verify API keys are valid
- Check network connectivity
- Review swap provider logs

### Incorrect Token Received

- Verify provider token requirements
- Check swap quote accuracy
- Review swap transaction details

### High Swap Fees

- Compare quotes from different providers
- Consider direct deposits when possible
- Monitor gas prices
