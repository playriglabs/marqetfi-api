"""Test FeatureAccessService."""

import pytest

from app.models.enums import FeatureAccessLevel, WalletType
from app.models.user import User
from app.services.feature_access_service import FeatureAccessService


class TestFeatureAccessService:
    """Test FeatureAccessService class."""

    @pytest.fixture
    def user_full_access_mpc(self):
        """Create user with full access and MPC wallet."""
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            feature_access_level=FeatureAccessLevel.FULL,
            wallet_type=WalletType.MPC,
        )
        return user

    @pytest.fixture
    def user_full_access_external(self):
        """Create user with full access and external wallet."""
        user = User(
            id=2,
            email="test2@example.com",
            username="testuser2",
            feature_access_level=FeatureAccessLevel.FULL,
            wallet_type=WalletType.EXTERNAL,
        )
        return user

    @pytest.fixture
    def user_limited_access(self):
        """Create user with limited access."""
        user = User(
            id=3,
            email="test3@example.com",
            username="testuser3",
            feature_access_level=FeatureAccessLevel.LIMITED,
            wallet_type=WalletType.NONE,
        )
        return user

    def test_check_feature_access_public_features(self, user_limited_access):
        """Test public features are accessible to all users."""
        assert FeatureAccessService.check_feature_access(user_limited_access, "view_prices") is True
        assert (
            FeatureAccessService.check_feature_access(user_limited_access, "view_positions") is True
        )

    def test_check_feature_access_full_access_mpc(self, user_full_access_mpc):
        """Test full access features for MPC wallet user."""
        assert (
            FeatureAccessService.check_feature_access(user_full_access_mpc, "open_trade") is True
        )
        assert (
            FeatureAccessService.check_feature_access(user_full_access_mpc, "close_trade") is True
        )
        assert (
            FeatureAccessService.check_feature_access(user_full_access_mpc, "update_tp_sl") is True
        )
        assert (
            FeatureAccessService.check_feature_access(user_full_access_mpc, "batch_operations")
            is True
        )
        assert (
            FeatureAccessService.check_feature_access(user_full_access_mpc, "auto_trading") is True
        )

    def test_check_feature_access_external_wallet(self, user_full_access_external):
        """Test feature access for external wallet user."""
        # Some features available but require confirmation
        assert (
            FeatureAccessService.check_feature_access(user_full_access_external, "open_trade")
            is True
        )
        assert (
            FeatureAccessService.check_feature_access(user_full_access_external, "close_trade")
            is True
        )
        # Batch operations and auto trading not available
        assert (
            FeatureAccessService.check_feature_access(user_full_access_external, "batch_operations")
            is False
        )
        assert (
            FeatureAccessService.check_feature_access(user_full_access_external, "auto_trading")
            is False
        )

    def test_check_feature_access_limited_user(self, user_limited_access):
        """Test feature access for limited access user."""
        assert (
            FeatureAccessService.check_feature_access(user_limited_access, "open_trade") is False
        )
        assert (
            FeatureAccessService.check_feature_access(user_limited_access, "batch_operations")
            is False
        )

    def test_check_feature_access_unknown_feature(self, user_full_access_mpc):
        """Test unknown feature returns False."""
        assert (
            FeatureAccessService.check_feature_access(user_full_access_mpc, "unknown_feature")
            is False
        )

    def test_get_available_features(self, user_full_access_mpc):
        """Test getting available features."""
        features = FeatureAccessService.get_available_features(user_full_access_mpc)

        assert features["view_prices"] is True
        assert features["view_positions"] is True
        assert features["open_trade"] is True
        assert features["close_trade"] is True
        assert features["batch_operations"] is True

    def test_get_available_features_external(self, user_full_access_external):
        """Test getting available features for external wallet user."""
        features = FeatureAccessService.get_available_features(user_full_access_external)

        assert features["view_prices"] is True
        assert features["open_trade"] is True
        assert features["batch_operations"] is False
        assert features["auto_trading"] is False

    def test_requires_confirmation_external_wallet(self, user_full_access_external):
        """Test confirmation requirement for external wallet user."""
        assert (
            FeatureAccessService.requires_confirmation(user_full_access_external, "open_trade")
            is True
        )
        assert (
            FeatureAccessService.requires_confirmation(user_full_access_external, "close_trade")
            is True
        )
        assert (
            FeatureAccessService.requires_confirmation(
                user_full_access_external, "position_management"
            )
            is True
        )
        assert (
            FeatureAccessService.requires_confirmation(
                user_full_access_external, "batch_operations"
            )
            is False
        )

    def test_requires_confirmation_mpc_wallet(self, user_full_access_mpc):
        """Test confirmation requirement for MPC wallet user."""
        assert (
            FeatureAccessService.requires_confirmation(user_full_access_mpc, "open_trade") is False
        )
        assert (
            FeatureAccessService.requires_confirmation(user_full_access_mpc, "close_trade") is False
        )

    def test_require_mpc_wallet_true(self, user_full_access_mpc):
        """Test require MPC wallet when user has MPC wallet."""
        assert FeatureAccessService.require_mpc_wallet(user_full_access_mpc) is True

    def test_require_mpc_wallet_false(self, user_full_access_external):
        """Test require MPC wallet when user doesn't have MPC wallet."""
        assert FeatureAccessService.require_mpc_wallet(user_full_access_external) is False

