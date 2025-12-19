"""Add wallet tables

Revision ID: 003
Revises: 002
Create Date: 2025-12-19 02:51:11.982357

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create wallets table
    op.create_table(
        "wallets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider_type", sa.String(length=50), nullable=False),
        sa.Column("provider_wallet_id", sa.String(length=255), nullable=False),
        sa.Column("wallet_address", sa.String(length=42), nullable=False),
        sa.Column("network", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("wallet_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_wallets_id"), "wallets", ["id"], unique=False)
    op.create_index(op.f("ix_wallets_wallet_address"), "wallets", ["wallet_address"], unique=False)
    op.create_index("ix_wallets_user_primary", "wallets", ["user_id", "is_primary"], unique=False)
    op.create_index(
        "ix_wallets_provider_wallet_id",
        "wallets",
        ["provider_type", "provider_wallet_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_wallets_provider_wallet_id", table_name="wallets")
    op.drop_index("ix_wallets_user_primary", table_name="wallets")
    op.drop_index(op.f("ix_wallets_wallet_address"), table_name="wallets")
    op.drop_index(op.f("ix_wallets_id"), table_name="wallets")
    op.drop_table("wallets")
