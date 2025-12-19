"""Feature access control service."""

from app.models.enums import FeatureAccessLevel, WalletType
from app.models.user import User


class FeatureAccessService:
    """Service for checking feature access levels."""

    @staticmethod
    def check_feature_access(
        user: User,
        feature: str,
    ) -> bool:
        """Check if user can access a feature.

        Args:
            user: User instance
            feature: Feature name

        Returns:
            True if user can access the feature
        """
        # Features available to all users
        public_features = ["view_prices", "view_positions"]

        if feature in public_features:
            return True

        # Features requiring full access
        full_access_features = [
            "open_trade",
            "close_trade",
            "update_tp_sl",
            "batch_operations",
            "auto_trading",
            "position_management",
        ]

        if feature in full_access_features:
            # External wallet users have limited access
            if user.wallet_type == WalletType.EXTERNAL:
                # Some features are available but require confirmation
                if feature in ["open_trade", "close_trade", "update_tp_sl", "position_management"]:
                    return True  # Available but requires confirmation
                # Batch operations and auto trading not available
                return False

            # MPC wallet and Web2 users have full access
            return user.feature_access_level == FeatureAccessLevel.FULL

        return False

    @staticmethod
    def get_available_features(user: User) -> dict[str, bool]:
        """Get list of available features for user.

        Args:
            user: User instance

        Returns:
            Dictionary of feature names and availability
        """
        features = {
            "view_prices": True,
            "view_positions": True,
            "open_trade": FeatureAccessService.check_feature_access(user, "open_trade"),
            "close_trade": FeatureAccessService.check_feature_access(user, "close_trade"),
            "update_tp_sl": FeatureAccessService.check_feature_access(user, "update_tp_sl"),
            "batch_operations": FeatureAccessService.check_feature_access(user, "batch_operations"),
            "auto_trading": FeatureAccessService.check_feature_access(user, "auto_trading"),
            "position_management": FeatureAccessService.check_feature_access(
                user, "position_management"
            ),
        }

        return features

    @staticmethod
    def requires_confirmation(user: User, feature: str) -> bool:
        """Check if feature requires confirmation for user.

        Args:
            user: User instance
            feature: Feature name

        Returns:
            True if feature requires confirmation
        """
        # External wallet users need confirmation for trading operations
        if user.wallet_type == WalletType.EXTERNAL:
            confirmation_features = [
                "open_trade",
                "close_trade",
                "update_tp_sl",
                "position_management",
            ]
            return feature in confirmation_features

        return False

    @staticmethod
    def require_mpc_wallet(user: User) -> bool:
        """Check if user has MPC wallet.

        Args:
            user: User instance

        Returns:
            True if user has MPC wallet
        """
        return user.wallet_type == WalletType.MPC
