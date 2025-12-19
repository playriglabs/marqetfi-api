"""add_ostium_wallet_table

Revision ID: 008
Revises: 007
Create Date: 2025-12-19 02:54:02.263970

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ostium_wallets table
    op.create_table(
        "ostium_wallets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "provider_type",
            sa.String(length=50),
            nullable=False,
            comment="Wallet provider type (privy/dynamic)",
        ),
        sa.Column(
            "provider_wallet_id",
            sa.String(length=255),
            nullable=False,
            comment="Provider-specific wallet ID",
        ),
        sa.Column(
            "wallet_address",
            sa.String(length=42),
            nullable=False,
            comment="Ethereum wallet address",
        ),
        sa.Column(
            "network", sa.String(length=20), nullable=False, comment="Network (testnet/mainnet)"
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Active status",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Provider-specific metadata",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Last update timestamp",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_wallet_id"),
    )

    # Create indexes
    op.create_index(op.f("ix_ostium_wallets_id"), "ostium_wallets", ["id"], unique=False)
    op.create_index(
        op.f("ix_ostium_wallets_provider_type"), "ostium_wallets", ["provider_type"], unique=False
    )
    op.create_index(
        op.f("ix_ostium_wallets_provider_wallet_id"),
        "ostium_wallets",
        ["provider_wallet_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_ostium_wallets_wallet_address"), "ostium_wallets", ["wallet_address"], unique=False
    )
    op.create_index(op.f("ix_ostium_wallets_network"), "ostium_wallets", ["network"], unique=False)
    op.create_index(
        "idx_provider_network_active",
        "ostium_wallets",
        ["provider_type", "network", "is_active"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_provider_network_active", table_name="ostium_wallets")
    op.drop_index(op.f("ix_ostium_wallets_network"), table_name="ostium_wallets")
    op.drop_index(op.f("ix_ostium_wallets_wallet_address"), table_name="ostium_wallets")
    op.drop_index(op.f("ix_ostium_wallets_provider_wallet_id"), table_name="ostium_wallets")
    op.drop_index(op.f("ix_ostium_wallets_provider_type"), table_name="ostium_wallets")
    op.drop_index(op.f("ix_ostium_wallets_id"), table_name="ostium_wallets")

    # Drop table
    op.drop_table("ostium_wallets")
