"""Add authentication tables

Revision ID: 002
Revises: 001
Create Date: 2025-12-19 02:50:32.809511

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create oauth_connections table
    op.create_table(
        "oauth_connections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_oauth_connections_id"), "oauth_connections", ["id"], unique=False)
    op.create_index(
        "ix_oauth_connections_user_provider",
        "oauth_connections",
        ["user_id", "provider"],
        unique=False,
    )
    op.create_index(
        "ix_oauth_connections_provider_user_id",
        "oauth_connections",
        ["provider", "provider_user_id"],
        unique=False,
    )

    # Create wallet_connections table
    op.create_table(
        "wallet_connections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("wallet_address", sa.String(length=42), nullable=False),
        sa.Column("wallet_type", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_wallet_connections_id"), "wallet_connections", ["id"], unique=False)
    op.create_index(
        op.f("ix_wallet_connections_wallet_address"),
        "wallet_connections",
        ["wallet_address"],
        unique=False,
    )
    op.create_index(
        "ix_wallet_connections_user_primary",
        "wallet_connections",
        ["user_id", "is_primary"],
        unique=False,
    )

    # Create sessions table
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=255), nullable=False),
        sa.Column("device_info", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sessions_id"), "sessions", ["id"], unique=False)
    op.create_index(op.f("ix_sessions_token_hash"), "sessions", ["token_hash"], unique=False)
    op.create_index(
        op.f("ix_sessions_refresh_token_hash"), "sessions", ["refresh_token_hash"], unique=False
    )
    op.create_index(op.f("ix_sessions_expires_at"), "sessions", ["expires_at"], unique=False)
    op.create_index("ix_sessions_user_expires", "sessions", ["user_id", "expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sessions_user_expires", table_name="sessions")
    op.drop_index(op.f("ix_sessions_expires_at"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_refresh_token_hash"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_token_hash"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_id"), table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_wallet_connections_user_primary", table_name="wallet_connections")
    op.drop_index(op.f("ix_wallet_connections_wallet_address"), table_name="wallet_connections")
    op.drop_index(op.f("ix_wallet_connections_id"), table_name="wallet_connections")
    op.drop_table("wallet_connections")
    op.drop_index("ix_oauth_connections_provider_user_id", table_name="oauth_connections")
    op.drop_index("ix_oauth_connections_user_provider", table_name="oauth_connections")
    op.drop_index(op.f("ix_oauth_connections_id"), table_name="oauth_connections")
    op.drop_table("oauth_connections")
