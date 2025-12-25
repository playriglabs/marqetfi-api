"""Extended tests for FeatureAccessService."""

import pytest

from app.models.enums import FeatureAccessLevel, WalletType
from app.models.user import User
from app.services.feature_access_service import FeatureAccessService


class TestFeatureAccessServiceExtended:
    """Extended tests for FeatureAccessService class."""

    @pytest.fixture
    def mpc_user(self):
        """Create MPC wallet user."""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            wallet_type=WalletType.MPC,
            feature_access_level=FeatureAccessLevel.FULL,
            is_active=True,
        )

    @pytest.fixture
    def external_user(self):
        """Create external wallet user."""
        return User(
            id=2,
            email="external@example.com",
            username="externaluser",
            wallet_type=WalletType.EXTERNAL,
            feature_access_level=FeatureAccessLevel.FULL,
            is_active=True,
        )

    @pytest.fixture
    def web2_user(self):
        """Create Web2 user."""
        return User(
            id=3,
            email="web2@example.com",
            username="web2user",
            wallet_type=WalletType.NONE,
            feature_access_level=FeatureAccessLevel.FULL,
            is_active=True,
        )

    def test_get_available_features_mpc_user(self, mpc_user):
        """Test getting available features for MPC user."""
        features = FeatureAccessService.get_available_features(mpc_user)

        assert features["view_prices"] is True
        assert features["view_positions"] is True
        assert features["open_trade"] is True
        assert features["close_trade"] is True

    def test_get_available_features_external_user(self, external_user):
        """Test getting available features for external wallet user."""
        features = FeatureAccessService.get_available_features(external_user)

        assert features["view_prices"] is True
        assert features["open_trade"] is True
        assert features["batch_operations"] is False
        assert features["auto_trading"] is False

    def test_get_available_features_web2_user(self, web2_user):
        """Test getting available features for Web2 user."""
        features = FeatureAccessService.get_available_features(web2_user)

        assert features["view_prices"] is True
        assert features["open_trade"] is True

    def test_check_feature_access_public_features(self, mpc_user):
        """Test checking access to public features."""
        assert FeatureAccessService.check_feature_access(mpc_user, "view_prices") is True
        assert FeatureAccessService.check_feature_access(mpc_user, "view_positions") is True

    def test_check_feature_access_external_batch_operations(self, external_user):
        """Test external user cannot access batch operations."""
        assert FeatureAccessService.check_feature_access(external_user, "batch_operations") is False

    def test_check_feature_access_external_auto_trading(self, external_user):
        """Test external user cannot access auto trading."""
        assert FeatureAccessService.check_feature_access(external_user, "auto_trading") is False

    def test_check_feature_access_external_allowed_features(self, external_user):
        """Test external user can access allowed features."""
        assert FeatureAccessService.check_feature_access(external_user, "open_trade") is True
        assert FeatureAccessService.check_feature_access(external_user, "close_trade") is True
        assert FeatureAccessService.check_feature_access(external_user, "update_tp_sl") is True
        assert FeatureAccessService.check_feature_access(external_user, "position_management") is True

    def test_check_feature_access_unknown_feature(self, mpc_user):
        """Test checking access to unknown feature."""
        assert FeatureAccessService.check_feature_access(mpc_user, "unknown_feature") is False

    def test_check_feature_access_limited_access_level(self):
        """Test user with limited access level."""
        limited_user = User(
            id=4,
            email="limited@example.com",
            username="limiteduser",
            wallet_type=WalletType.MPC,
            feature_access_level=FeatureAccessLevel.LIMITED,
            is_active=True,
        )

        assert FeatureAccessService.check_feature_access(limited_user, "view_prices") is True
        assert FeatureAccessService.check_feature_access(limited_user, "open_trade") is False

    def test_requires_confirmation_external_user(self, external_user):
        """Test requires_confirmation for external wallet user."""
        assert FeatureAccessService.requires_confirmation(external_user, "open_trade") is True
        assert FeatureAccessService.requires_confirmation(external_user, "close_trade") is True
        assert FeatureAccessService.requires_confirmation(external_user, "batch_operations") is False

    def test_requires_confirmation_mpc_user(self, mpc_user):
        """Test requires_confirmation for MPC wallet user."""
        assert FeatureAccessService.requires_confirmation(mpc_user, "open_trade") is False

    def test_require_mpc_wallet(self, mpc_user, external_user, web2_user):
        """Test require_mpc_wallet method."""
        assert FeatureAccessService.require_mpc_wallet(mpc_user) is True
        assert FeatureAccessService.require_mpc_wallet(external_user) is False
        assert FeatureAccessService.require_mpc_wallet(web2_user) is False

