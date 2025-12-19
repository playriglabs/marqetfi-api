"""Add Auth0 authentication fields

Revision ID: 009
Revises: 008
Create Date: 2025-01-20 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add auth0_user_id to users table (unique, indexed, nullable)
    op.add_column("users", sa.Column("auth0_user_id", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_users_auth0_user_id"), "users", ["auth0_user_id"], unique=True)

    # Add mpc_wallet_id to users table (foreign key to wallets.id, nullable)
    op.add_column("users", sa.Column("mpc_wallet_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_users_mpc_wallet_id", "users", "wallets", ["mpc_wallet_id"], ["id"], ondelete="SET NULL"
    )

    # Rename primary_wallet_address to wallet_address
    # Drop old index first
    op.drop_index(op.f("ix_users_primary_wallet_address"), table_name="users")
    # Rename the column
    op.alter_column("users", "primary_wallet_address", new_column_name="wallet_address")
    # Create new index with new column name
    op.create_index(op.f("ix_users_wallet_address"), "users", ["wallet_address"], unique=False)

    # Make hashed_password nullable (for OAuth/wallet users who don't have passwords)
    op.alter_column("users", "hashed_password", nullable=True)

    # Add provider_wallet_id to wallet_connections table
    op.add_column(
        "wallet_connections", sa.Column("provider_wallet_id", sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    # Remove provider_wallet_id from wallet_connections
    op.drop_column("wallet_connections", "provider_wallet_id")

    # Revert hashed_password to NOT NULL (with a default for existing nullable values)
    op.alter_column("users", "hashed_password", nullable=False)

    # Rename wallet_address back to primary_wallet_address
    op.drop_index(op.f("ix_users_wallet_address"), table_name="users")
    op.alter_column("users", "wallet_address", new_column_name="primary_wallet_address")
    op.create_index(
        op.f("ix_users_primary_wallet_address"), "users", ["primary_wallet_address"], unique=False
    )

    # Remove mpc_wallet_id foreign key and column
    op.drop_constraint("fk_users_mpc_wallet_id", "users", type_="foreignkey")
    op.drop_column("users", "mpc_wallet_id")

    # Remove auth0_user_id index and column
    op.drop_index(op.f("ix_users_auth0_user_id"), table_name="users")
    op.drop_column("users", "auth0_user_id")
