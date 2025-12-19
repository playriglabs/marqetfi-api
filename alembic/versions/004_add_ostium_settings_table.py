"""Add ostium settings table

Revision ID: 004
Revises: 003
Create Date: 2025-01-20 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ostium_settings table
    op.create_table(
        "ostium_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("private_key_encrypted", sa.String(length=500), nullable=False),
        sa.Column("rpc_url", sa.String(length=500), nullable=False),
        sa.Column("network", sa.String(length=20), nullable=False),
        sa.Column("verbose", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("slippage_percentage", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("default_fee_percentage", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("min_fee", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("max_fee", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("timeout", sa.Integer(), nullable=False),
        sa.Column("retry_attempts", sa.Integer(), nullable=False),
        sa.Column("retry_delay", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(op.f("ix_ostium_settings_id"), "ostium_settings", ["id"], unique=False)
    op.create_index(
        op.f("ix_ostium_settings_is_active"), "ostium_settings", ["is_active"], unique=False
    )
    op.create_index(
        op.f("ix_ostium_settings_version"), "ostium_settings", ["version"], unique=False
    )
    op.create_index(
        op.f("ix_ostium_settings_created_by"), "ostium_settings", ["created_by"], unique=False
    )
    op.create_index(
        op.f("ix_ostium_settings_created_at"), "ostium_settings", ["created_at"], unique=False
    )
    op.create_index(
        "idx_ostium_settings_active", "ostium_settings", ["is_active", "created_at"], unique=False
    )
    op.create_index("idx_ostium_settings_version", "ostium_settings", ["version"], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_ostium_settings_version", table_name="ostium_settings")
    op.drop_index("idx_ostium_settings_active", table_name="ostium_settings")
    op.drop_index(op.f("ix_ostium_settings_created_at"), table_name="ostium_settings")
    op.drop_index(op.f("ix_ostium_settings_created_by"), table_name="ostium_settings")
    op.drop_index(op.f("ix_ostium_settings_version"), table_name="ostium_settings")
    op.drop_index(op.f("ix_ostium_settings_is_active"), table_name="ostium_settings")
    op.drop_index(op.f("ix_ostium_settings_id"), table_name="ostium_settings")

    # Drop table
    op.drop_table("ostium_settings")
