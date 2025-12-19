"""Add configuration tables

Revision ID: 011
Revises: 010
Create Date: 2025-01-21 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create app_configurations table
    op.create_table(
        "app_configurations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("config_key", sa.String(length=100), nullable=False),
        sa.Column("config_value", sa.Text(), nullable=True),
        sa.Column("config_type", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_encrypted", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_app_configurations_id"), "app_configurations", ["id"], unique=False)
    op.create_index(
        op.f("ix_app_configurations_config_key"), "app_configurations", ["config_key"], unique=True
    )
    op.create_index(
        op.f("ix_app_configurations_category"), "app_configurations", ["category"], unique=False
    )
    op.create_index(
        op.f("ix_app_configurations_created_by"), "app_configurations", ["created_by"], unique=False
    )
    op.create_index(
        "idx_app_config_key_active",
        "app_configurations",
        ["config_key", "is_active"],
        unique=False,
    )
    op.create_index("idx_app_config_category", "app_configurations", ["category"], unique=False)

    # Create provider_configurations table
    op.create_table(
        "provider_configurations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider_name", sa.String(length=50), nullable=False),
        sa.Column("provider_type", sa.String(length=50), nullable=False),
        sa.Column("config_data", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_provider_configurations_id"), "provider_configurations", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_provider_configurations_provider_name"),
        "provider_configurations",
        ["provider_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_provider_configurations_provider_type"),
        "provider_configurations",
        ["provider_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_provider_configurations_created_by"),
        "provider_configurations",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        "idx_provider_config_active",
        "provider_configurations",
        ["provider_name", "provider_type", "is_active"],
        unique=False,
    )
    op.create_index(
        "idx_provider_config_version",
        "provider_configurations",
        ["provider_name", "provider_type", "version"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_provider_config_version", table_name="provider_configurations")
    op.drop_index("idx_provider_config_active", table_name="provider_configurations")
    op.drop_index(
        op.f("ix_provider_configurations_created_by"), table_name="provider_configurations"
    )
    op.drop_index(
        op.f("ix_provider_configurations_provider_type"), table_name="provider_configurations"
    )
    op.drop_index(
        op.f("ix_provider_configurations_provider_name"), table_name="provider_configurations"
    )
    op.drop_index(op.f("ix_provider_configurations_id"), table_name="provider_configurations")
    op.drop_table("provider_configurations")

    op.drop_index("idx_app_config_category", table_name="app_configurations")
    op.drop_index("idx_app_config_key_active", table_name="app_configurations")
    op.drop_index(op.f("ix_app_configurations_created_by"), table_name="app_configurations")
    op.drop_index(op.f("ix_app_configurations_category"), table_name="app_configurations")
    op.drop_index(op.f("ix_app_configurations_config_key"), table_name="app_configurations")
    op.drop_index(op.f("ix_app_configurations_id"), table_name="app_configurations")
    op.drop_table("app_configurations")
