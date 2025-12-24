# OAuth Authentication Guide

This document describes how to use OAuth authentication with Google and Apple providers in the MarqetFi API.

## Overview

The OAuth authentication flow allows users to authenticate using their Google or Apple accounts. The system uses Auth0 as the identity provider, which handles the OAuth flow with Google and Apple.

## OAuth Flow

The OAuth flow follows the standard OAuth 2.0 authorization code flow:

1. **Authorization Request**: Client requests authorization URL
2. **User Consent**: User is redirected to provider (Google/Apple) to authorize
3. **Callback**: Provider redirects back with authorization code
4. **Token Exchange**: System exchanges code for access token
5. **User Creation/Linking**: System creates or links user account
6. **JWT Tokens**: System returns JWT tokens for API access

## API Endpoints

### 1. Initiate OAuth Flow

**Endpoint**: `GET /api/v1/auth/oauth/authorize/{provider}`

**Parameters**:
- `provider` (path): OAuth provider (`google` or `apple`)
- `redirect_uri` (query, optional): Custom redirect URI (defaults to configured URI)

**Response**:
```json
{
  "authorization_url": "https://auth0.example.com/authorize?...",
  "state": "random_state_token_123"
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/auth/oauth/authorize/google"
```

**Response**:
```json
{
  "authorization_url": "https://your-auth0-domain.auth0.com/authorize?client_id=...&connection=google-oauth2&state=abc123&redirect_uri=...",
  "state": "abc123"
}
```

### 2. OAuth Callback (Generic)

**Endpoint**: `GET /api/v1/auth/oauth/callback`

**Parameters**:
- `code` (query, required): Authorization code from OAuth provider
- `state` (query, required): State token (must match the one from authorization request)
- `redirect_uri` (query, optional): Redirect URI used in authorization

**Response**:
```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token",
  "token_type": "bearer"
}
```

### 3. Google OAuth Callback

**Endpoint**: `GET /api/v1/auth/oauth/google/callback`

**Parameters**: Same as generic callback

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/auth/oauth/google/callback?code=auth_code_123&state=abc123"
```

### 4. Apple OAuth Callback

**Endpoint**: `GET /api/v1/auth/oauth/apple/callback`

**Parameters**: Same as generic callback

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/auth/oauth/apple/callback?code=auth_code_456&state=xyz789"
```

## State Management

The system implements OAuth state management for CSRF protection:

- **State Generation**: Random 32-byte URL-safe token generated for each authorization request
- **State Storage**: State is stored in Redis cache with provider and redirect_uri
- **State Expiration**: States expire after 10 minutes
- **State Validation**: State is validated on callback and deleted after use (one-time use)
- **State Mismatch**: Callbacks with invalid or expired states are rejected

## User Account Handling

### New User Creation

When a user authenticates via OAuth for the first time:
1. System retrieves user info from OAuth provider
2. System creates new user account with:
   - Email from OAuth provider
   - Username generated from email or name
   - `auth_method` set to `GOOGLE` or `APPLE`
   - `email_verified` set based on provider verification status
3. System creates `OAuthConnection` record linking OAuth account to user
4. System returns JWT tokens

### Existing User Linking

When OAuth email matches existing user:
1. System links OAuth account to existing user
2. System updates `auth_method` if needed
3. System creates or updates `OAuthConnection` record
4. System returns JWT tokens

### Duplicate OAuth Connection

If OAuth account is already linked:
1. System updates existing `OAuthConnection` record
2. System updates access token and refresh token
3. System returns JWT tokens

## Error Handling

### Invalid State

**Error**: `400 Bad Request`

**Message**: `"OAuth state validation failed: Invalid or expired OAuth state"`

**Cause**: State token is missing, invalid, expired, or already used

**Resolution**: Initiate new OAuth flow

### Token Exchange Failure

**Error**: `400 Bad Request`

**Message**: `"OAuth token exchange failed: [error details]"`

**Cause**: Authorization code is invalid, expired, or already used

**Resolution**: Initiate new OAuth flow

### User Info Retrieval Failure

**Error**: `400 Bad Request`

**Message**: `"OAuth user info retrieval failed: [error details]"`

**Cause**: Access token is invalid or provider API is unavailable

**Resolution**: Retry OAuth flow

### Provider Mismatch

**Error**: `400 Bad Request`

**Message**: `"OAuth provider mismatch"`

**Cause**: Provider in callback doesn't match provider in state

**Resolution**: Use correct provider-specific callback endpoint

## Configuration

### Environment Variables

Required environment variables for OAuth:

```bash
# Auth0 Configuration
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret
AUTH0_AUDIENCE=your_api_audience
AUTH0_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/callback

# Provider Enablement
AUTH0_GOOGLE_ENABLED=true
AUTH0_APPLE_ENABLED=true

# Redis (for state management)
REDIS_URL=redis://localhost:6379/0
```

### Auth0 Setup

1. Create Auth0 application
2. Configure Google and Apple connections in Auth0 dashboard
3. Set allowed callback URLs in Auth0:
   - `http://localhost:8000/api/v1/auth/oauth/callback`
   - `http://localhost:8000/api/v1/auth/oauth/google/callback`
   - `http://localhost:8000/api/v1/auth/oauth/apple/callback`
4. Configure provider-specific settings in Auth0

## Frontend Integration Example

### React/Next.js Example

```typescript
// 1. Initiate OAuth flow
const initiateOAuth = async (provider: 'google' | 'apple') => {
  const response = await fetch(
    `http://localhost:8000/api/v1/auth/oauth/authorize/${provider}`
  );
  const { authorization_url, state } = await response.json();
  
  // Store state in sessionStorage for validation
  sessionStorage.setItem('oauth_state', state);
  
  // Redirect user to authorization URL
  window.location.href = authorization_url;
};

// 2. Handle callback (in callback page)
const handleCallback = async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  const state = urlParams.get('state');
  const storedState = sessionStorage.getItem('oauth_state');
  
  // Validate state
  if (state !== storedState) {
    console.error('Invalid OAuth state');
    return;
  }
  
  // Exchange code for tokens
  const response = await fetch(
    `http://localhost:8000/api/v1/auth/oauth/callback?code=${code}&state=${state}`
  );
  
  if (response.ok) {
    const { access_token, refresh_token } = await response.json();
    // Store tokens and redirect to app
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    window.location.href = '/dashboard';
  } else {
    const error = await response.json();
    console.error('OAuth callback failed:', error);
  }
};
```

## Security Considerations

1. **State Validation**: Always validate state tokens to prevent CSRF attacks
2. **HTTPS**: Use HTTPS in production for all OAuth endpoints
3. **Token Storage**: Store JWT tokens securely (httpOnly cookies recommended)
4. **State Expiration**: States expire after 10 minutes for security
5. **One-Time Use**: States are deleted after use to prevent replay attacks
6. **Provider Verification**: System verifies provider matches state

## Troubleshooting

### State Validation Fails

- Check that state is stored correctly in sessionStorage/localStorage
- Ensure state hasn't expired (10 minutes)
- Verify state hasn't been used already

### Token Exchange Fails

- Verify authorization code hasn't expired (typically 10 minutes)
- Check that redirect_uri matches exactly
- Ensure Auth0 credentials are correct

### User Not Created

- Check that email is provided by OAuth provider
- Verify Auth0 user info includes required fields
- Check database connection and permissions

## Related Documentation

- [Authentication Overview](./PRD.md#authentication)
- [Configuration Management](./configuration-management.md)
- [API Documentation](http://localhost:8000/docs)

