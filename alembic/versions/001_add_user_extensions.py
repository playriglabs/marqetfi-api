"""Add user extensions

Revision ID: 001
Revises:
Create Date: 2025-12-19 02:50:17.762981

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column(
        "users",
        sa.Column("auth_method", sa.String(length=20), nullable=False, server_default="email"),
    )
    op.add_column("users", sa.Column("wallet_type", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("primary_wallet_address", sa.String(length=42), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "feature_access_level", sa.String(length=20), nullable=False, server_default="full"
        ),
    )
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(), nullable=True))
    op.add_column(
        "users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false")
    )
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(), nullable=True))

    # Create indexes
    op.create_index(
        op.f("ix_users_primary_wallet_address"), "users", ["primary_wallet_address"], unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_users_primary_wallet_address"), table_name="users")

    # Drop columns
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "email_verified")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "feature_access_level")
    op.drop_column("users", "primary_wallet_address")
    op.drop_column("users", "wallet_type")
    op.drop_column("users", "auth_method")
