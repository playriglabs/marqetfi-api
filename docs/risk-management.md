# Risk Management System

## Overview

The risk management system provides comprehensive protection for users and the platform by enforcing leverage limits, position size limits, margin requirements, and real-time position monitoring. Risk checks are performed before trade execution and continuously monitored for open positions.

## Risk Management Rules

### Leverage Limits

- **Default Maximum Leverage**: 10x (configurable per user/asset)
- **Validation**: Leverage is checked before trade execution
- **Priority**: User-specific limits > Asset-specific limits > Global defaults

#### Scenario: Leverage Validation
- **WHEN** user attempts to open a trade with leverage
- **THEN** system checks leverage against user's risk limit
- **THEN** if leverage exceeds limit, trade is rejected with error message
- **THEN** error message includes current limit and attempted value

### Position Size Limits

- **Default Maximum Position Size**: 1,000,000 (configurable per user/asset)
- **Validation**: Aggregate position size is checked before new trades
- **Calculation**: Sum of all existing positions + new position size

#### Scenario: Position Size Validation
- **WHEN** user attempts to open a new position
- **THEN** system calculates total position size (existing + new)
- **THEN** if total exceeds limit, trade is rejected
- **THEN** error message indicates maximum allowed size

### Margin Requirements

- **Minimum Margin**: 100 (configurable per user/asset)
- **Required Margin Calculation**: `collateral * leverage`
- **Validation**: Checks both minimum margin requirement and available balance

#### Scenario: Margin Validation
- **WHEN** user attempts to open a trade
- **THEN** system calculates required margin (collateral × leverage)
- **THEN** system checks if required margin meets minimum requirement
- **THEN** system checks if user has sufficient available balance
- **THEN** if any check fails, trade is rejected with specific error

### Pre-Trade Risk Validation

All risk checks are performed before trade execution:

1. **Leverage Limit Check**: Validates requested leverage against limits
2. **Position Size Check**: Validates aggregate position size
3. **Margin Check**: Validates margin requirements and available balance

#### Scenario: Pre-Trade Risk Validation
- **WHEN** user submits trade order
- **THEN** system performs leverage limit check
- **THEN** system performs position size limit check
- **THEN** system performs margin requirement check
- **THEN** if any check fails, trade is rejected before provider execution
- **THEN** if all checks pass, trade proceeds to execution

### Real-Time Position Monitoring

Positions are monitored continuously for risk threshold breaches:

- **Margin Call Threshold**: 10% margin ratio
- **Liquidation Risk Threshold**: Within 5% of liquidation price
- **Monitoring Frequency**: Background task runs periodically

#### Scenario: Margin Call Monitoring
- **WHEN** position margin ratio falls below 10%
- **THEN** margin call alert is generated
- **THEN** alert includes position details and required margin
- **THEN** alert is logged and can trigger notifications

#### Scenario: Liquidation Risk Monitoring
- **WHEN** position approaches liquidation threshold (within 5%)
- **THEN** liquidation risk alert is generated
- **THEN** alert includes position details and liquidation price
- **THEN** alert is logged with critical severity

## Risk Limit Configuration

### Risk Limit Hierarchy

Risk limits follow a priority hierarchy:

1. **User-Specific Asset Limit**: Highest priority, applies to specific user and asset
2. **User-Specific Global Limit**: Applies to all assets for specific user
3. **Asset-Specific Global Limit**: Applies to all users for specific asset
4. **Global Default Limit**: Lowest priority, applies when no other limit exists

### Default Risk Limits

If no risk limit is configured, the system uses these defaults:

- **Max Leverage**: 10x
- **Max Position Size**: 1,000,000
- **Min Margin**: 100

### Creating Risk Limits

Risk limits can be created via the admin API:

```http
POST /api/v1/admin/risk/limits
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "user_id": 123,           // Optional: null for global limit
  "asset": "BTC",           // Optional: null for all assets
  "max_leverage": 20,
  "max_position_size": "2000000",
  "min_margin": "200",
  "is_active": true
}
```

### Updating Risk Limits

```http
PUT /api/v1/admin/risk/limits/{limit_id}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "max_leverage": 25,
  "is_active": false
}
```

### Risk Limit Fields

- **user_id**: Optional. If null, applies globally. If set, applies to specific user.
- **asset**: Optional. If null, applies to all assets. If set, applies to specific asset.
- **max_leverage**: Maximum allowed leverage multiplier
- **max_position_size**: Maximum aggregate position size
- **min_margin**: Minimum required margin
- **is_active**: Whether the limit is currently active

## Risk Metrics API

### User Risk Metrics

Get risk metrics for a specific user:

```http
GET /api/v1/admin/risk/metrics/users/{user_id}
Authorization: Bearer <admin-token>
```

**Response:**
```json
{
  "user_id": 123,
  "total_positions": 5,
  "aggregate_leverage": 8.5,
  "total_position_size": 500000.0,
  "total_collateral": 58823.53,
  "recent_risk_events": [
    {
      "event_type": "margin_call",
      "severity": "critical",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Platform Risk Metrics

Get platform-wide risk metrics:

```http
GET /api/v1/admin/risk/metrics/platform?skip=0&limit=100
Authorization: Bearer <admin-token>
```

**Response:**
```json
{
  "total_positions": 150,
  "aggregate_leverage": 7.2,
  "total_position_size": 15000000.0,
  "total_collateral": 2083333.33,
  "total_notional": 15000000.0
}
```

## Risk Events

### Event Types

- **margin_call**: Generated when margin ratio falls below threshold
- **liquidation_risk**: Generated when position approaches liquidation price
- **leverage_exceeded**: Generated when aggregate leverage exceeds warning threshold

### Event Severity Levels

- **warning**: Informational alerts
- **critical**: Requires immediate attention
- **alert**: General risk notifications

### Querying Risk Events

```http
GET /api/v1/admin/risk/events?user_id=123&event_type=margin_call&skip=0&limit=100
Authorization: Bearer <admin-token>
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 123,
      "event_type": "margin_call",
      "threshold": "0.1",
      "current_value": "0.05",
      "severity": "critical",
      "message": "Margin ratio 0.05 is below 10%",
      "position_id": 456,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

## Background Monitoring

The risk monitoring system includes a background task that periodically checks all open positions for risk threshold breaches:

- **Task Name**: `monitor_position_risk`
- **Frequency**: Configurable (typically every 30-60 seconds)
- **Checks**: Margin ratio, liquidation risk, other risk events

The task generates risk events for any positions that breach thresholds, which are then logged and can trigger notifications.

## Integration with Trading Service

Risk validation is automatically integrated into the trading service:

- **Pre-Trade Validation**: All trades are validated before execution
- **Error Messages**: Clear error messages indicate which check failed
- **Automatic Rejection**: Trades that fail risk checks are rejected before provider execution

## Best Practices

1. **Set Appropriate Limits**: Configure risk limits based on user experience and asset volatility
2. **Monitor Risk Events**: Regularly review risk events to identify patterns
3. **Adjust Limits Dynamically**: Update limits based on market conditions and user behavior
4. **Use User-Specific Limits**: Apply stricter limits for new or high-risk users
5. **Monitor Platform Metrics**: Track aggregate metrics to identify systemic risks
