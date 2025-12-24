"""Test OAuth service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import OAuthConnection
from app.models.enums import AuthMethod
from app.models.user import User
from app.services.oauth_service import OAUTH_STATE_EXPIRATION, OAuthService


class TestOAuthService:
    """Test OAuthService class."""

    @pytest.fixture
    def service(self):
        """Create test service."""
        return OAuthService()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=AsyncSession)

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.auth_method = AuthMethod.GOOGLE
        user.email_verified = True
        return user

    @pytest.mark.asyncio
    async def test_store_oauth_state(self, service):
        """Test storing OAuth state in cache."""
        state = "test_state_123"
        provider = "google"
        redirect_uri = "http://localhost:8000/callback"

        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.set = AsyncMock(return_value=True)

            await service._store_oauth_state(state, provider, redirect_uri)

            mock_cache.set.assert_called_once()
            call_args = mock_cache.set.call_args
            assert call_args[0][0] == f"oauth:state:{state}"
            assert call_args[0][1]["provider"] == provider
            assert call_args[0][1]["redirect_uri"] == redirect_uri
            assert call_args[1]["expire"] == OAUTH_STATE_EXPIRATION

    @pytest.mark.asyncio
    async def test_validate_oauth_state_success(self, service):
        """Test validating OAuth state successfully."""
        state = "test_state_123"
        state_data = {
            "provider": "google",
            "redirect_uri": "http://localhost:8000/callback",
        }

        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=state_data)
            mock_cache.delete = AsyncMock(return_value=True)

            result = await service._validate_oauth_state(state)

            assert result == state_data
            mock_cache.get.assert_called_once_with(f"oauth:state:{state}")
            mock_cache.delete.assert_called_once_with(f"oauth:state:{state}")

    @pytest.mark.asyncio
    async def test_validate_oauth_state_invalid(self, service):
        """Test validating invalid OAuth state."""
        state = "invalid_state"

        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)

            with pytest.raises(ValueError, match="Invalid or expired OAuth state"):
                await service._validate_oauth_state(state)

    @pytest.mark.asyncio
    async def test_validate_oauth_state_expired(self, service):
        """Test validating expired OAuth state."""
        state = "expired_state"

        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)

            with pytest.raises(ValueError, match="Invalid or expired OAuth state"):
                await service._validate_oauth_state(state)

    @pytest.mark.asyncio
    async def test_get_oauth_authorization_url_google(self, service):
        """Test getting OAuth authorization URL for Google."""
        provider = "google"
        redirect_uri = "http://localhost:8000/callback"
        auth_url = "https://auth0.example.com/authorize?client_id=123&connection=google-oauth2"

        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.set = AsyncMock(return_value=True)
            with patch.object(service.auth0_service, "get_authorization_url") as mock_get_url:
                mock_get_url.return_value = auth_url

                result_url, result_state = await service.get_oauth_authorization_url(
                    provider=provider, redirect_uri=redirect_uri
                )

                assert result_url == auth_url
                assert result_state is not None
                assert len(result_state) > 0
                mock_get_url.assert_called_once()
                mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_oauth_authorization_url_apple(self, service):
        """Test getting OAuth authorization URL for Apple."""
        provider = "apple"
        redirect_uri = "http://localhost:8000/callback"
        auth_url = "https://auth0.example.com/authorize?client_id=123&connection=apple"

        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.set = AsyncMock(return_value=True)
            with patch.object(service.auth0_service, "get_authorization_url") as mock_get_url:
                mock_get_url.return_value = auth_url

                result_url, result_state = await service.get_oauth_authorization_url(
                    provider=provider, redirect_uri=redirect_uri
                )

                assert result_url == auth_url
                assert result_state is not None

    @pytest.mark.asyncio
    async def test_get_oauth_authorization_url_unsupported_provider(self, service):
        """Test getting OAuth authorization URL with unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported OAuth provider"):
            await service.get_oauth_authorization_url(provider="facebook")

    @pytest.mark.asyncio
    async def test_handle_oauth_callback_success(self, service, mock_db, mock_user):
        """Test handling OAuth callback successfully."""
        code = "auth_code_123"
        state = "valid_state_123"
        redirect_uri = "http://localhost:8000/callback"
        provider = "google"

        state_data = {
            "provider": provider,
            "redirect_uri": redirect_uri,
        }

        token_response = {
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_123",
            "expires_in": 3600,
        }

        userinfo = {
            "sub": "google-oauth2|123456789",
            "email": "test@example.com",
            "name": "Test User",
            "email_verified": True,
        }

        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=state_data)
            mock_cache.delete = AsyncMock(return_value=True)

            with patch.object(service.auth0_service, "exchange_code_for_tokens") as mock_exchange:
                mock_exchange.return_value = token_response

                with patch.object(service.auth0_service, "get_userinfo") as mock_userinfo:
                    mock_userinfo.return_value = userinfo

                    with patch.object(
                        service.auth_service, "create_or_update_user_from_auth0"
                    ) as mock_create_user:
                        mock_create_user.return_value = mock_user

                        with patch.object(
                            service.auth_service, "_store_oauth_connection"
                        ) as mock_store_conn:
                            mock_store_conn.return_value = MagicMock(spec=OAuthConnection)

                            with patch.object(
                                service.auth_service, "_generate_tokens"
                            ) as mock_gen_tokens:
                                mock_gen_tokens.return_value = {
                                    "access_token": "jwt_token",
                                    "refresh_token": "refresh_jwt",
                                    "token_type": "bearer",
                                }

                                user, tokens = await service.handle_oauth_callback(
                                    db=mock_db,
                                    code=code,
                                    state=state,
                                    redirect_uri=redirect_uri,
                                    provider=provider,
                                )

                                assert user == mock_user
                                assert "access_token" in tokens
                                mock_exchange.assert_called_once_with(
                                    code=code, redirect_uri=redirect_uri
                                )
                                mock_userinfo.assert_called_once_with(
                                    token_response["access_token"]
                                )
                                mock_create_user.assert_called_once()
                                mock_store_conn.assert_called_once()
                                mock_gen_tokens.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_oauth_callback_invalid_state(self, service, mock_db):
        """Test handling OAuth callback with invalid state."""
        code = "auth_code_123"
        state = "invalid_state"

        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)

            with pytest.raises(ValueError, match="OAuth state validation failed"):
                await service.handle_oauth_callback(db=mock_db, code=code, state=state)

    @pytest.mark.asyncio
    async def test_handle_oauth_callback_provider_mismatch(self, service, mock_db):
        """Test handling OAuth callback with provider mismatch."""
        code = "auth_code_123"
        state = "valid_state_123"
        provider = "apple"

        state_data = {
            "provider": "google",  # Mismatch
            "redirect_uri": "http://localhost:8000/callback",
        }

        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=state_data)
            mock_cache.delete = AsyncMock(return_value=True)

            with pytest.raises(ValueError, match="OAuth provider mismatch"):
                await service.handle_oauth_callback(
                    db=mock_db, code=code, state=state, provider=provider
                )

    @pytest.mark.asyncio
    async def test_handle_oauth_callback_token_exchange_failure(self, service, mock_db):
        """Test handling OAuth callback with token exchange failure."""
        code = "auth_code_123"
        state = "valid_state_123"
        provider = "google"

        state_data = {
            "provider": provider,
            "redirect_uri": "http://localhost:8000/callback",
        }

        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=state_data)
            mock_cache.delete = AsyncMock(return_value=True)

            with patch.object(service.auth0_service, "exchange_code_for_tokens") as mock_exchange:
                mock_exchange.side_effect = Exception("Token exchange failed")

                with pytest.raises(ValueError, match="OAuth token exchange failed"):
                    await service.handle_oauth_callback(
                        db=mock_db, code=code, state=state, provider=provider
                    )

    @pytest.mark.asyncio
    async def test_handle_oauth_callback_userinfo_failure(self, service, mock_db):
        """Test handling OAuth callback with user info retrieval failure."""
        code = "auth_code_123"
        state = "valid_state_123"
        provider = "google"

        state_data = {
            "provider": provider,
            "redirect_uri": "http://localhost:8000/callback",
        }

        token_response = {
            "access_token": "access_token_123",
            "expires_in": 3600,
        }

        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=state_data)
            mock_cache.delete = AsyncMock(return_value=True)

            with patch.object(service.auth0_service, "exchange_code_for_tokens") as mock_exchange:
                mock_exchange.return_value = token_response

                with patch.object(service.auth0_service, "get_userinfo") as mock_userinfo:
                    mock_userinfo.side_effect = Exception("User info retrieval failed")

                    with pytest.raises(ValueError, match="OAuth user info retrieval failed"):
                        await service.handle_oauth_callback(
                            db=mock_db, code=code, state=state, provider=provider
                        )

    @pytest.mark.asyncio
    async def test_handle_oauth_callback_auto_detect_provider(self, service, mock_db, mock_user):
        """Test handling OAuth callback with auto-detected provider."""
        code = "auth_code_123"
        state = "valid_state_123"

        state_data = {
            "provider": "google",
            "redirect_uri": "http://localhost:8000/callback",
        }

        token_response = {
            "access_token": "access_token_123",
            "expires_in": 3600,
        }

        userinfo = {
            "sub": "google-oauth2|123456789",
            "email": "test@example.com",
        }

        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=state_data)
            mock_cache.delete = AsyncMock(return_value=True)

            with patch.object(service.auth0_service, "exchange_code_for_tokens") as mock_exchange:
                mock_exchange.return_value = token_response

                with patch.object(service.auth0_service, "get_userinfo") as mock_userinfo:
                    mock_userinfo.return_value = userinfo

                    with patch.object(
                        service.auth_service, "create_or_update_user_from_auth0"
                    ) as mock_create_user:
                        mock_create_user.return_value = mock_user

                        with patch.object(
                            service.auth_service, "_store_oauth_connection"
                        ) as mock_store_conn:
                            mock_store_conn.return_value = MagicMock(spec=OAuthConnection)

                            with patch.object(
                                service.auth_service, "_generate_tokens"
                            ) as mock_gen_tokens:
                                mock_gen_tokens.return_value = {
                                    "access_token": "jwt_token",
                                    "refresh_token": "refresh_jwt",
                                    "token_type": "bearer",
                                }

                                # Don't pass provider, should auto-detect
                                user, tokens = await service.handle_oauth_callback(
                                    db=mock_db, code=code, state=state
                                )

                                assert user == mock_user
                                # Verify provider was detected from userinfo
                                call_args = mock_store_conn.call_args
                                assert call_args[1]["provider"] == "google"

    @pytest.mark.asyncio
    async def test_handle_oauth_callback_unknown_provider(self, service, mock_db):
        """Test handling OAuth callback with unknown provider in userinfo."""
        code = "auth_code_123"
        state = "valid_state_123"

        # Don't include provider in state_data to force provider detection from userinfo
        state_data = {
            "redirect_uri": "http://localhost:8000/callback",
        }

        token_response = {
            "access_token": "access_token_123",
            "expires_in": 3600,
        }

        userinfo = {
            "sub": "unknown-provider|123456789",  # Unknown provider
            "email": "test@example.com",
        }

        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=state_data)
            mock_cache.delete = AsyncMock(return_value=True)

            with patch.object(service.auth0_service, "exchange_code_for_tokens") as mock_exchange:
                mock_exchange.return_value = token_response

                with patch.object(service.auth0_service, "get_userinfo") as mock_userinfo:
                    mock_userinfo.return_value = userinfo

                    with pytest.raises(ValueError, match="Unable to determine OAuth provider"):
                        await service.handle_oauth_callback(db=mock_db, code=code, state=state)
