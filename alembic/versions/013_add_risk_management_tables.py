"""Add risk management tables

Revision ID: 013
Revises: 012
Create Date: 2025-01-21 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create risk_limits table
    op.create_table(
        "risk_limits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("asset", sa.String(length=20), nullable=True),
        sa.Column("max_leverage", sa.Integer(), nullable=False),
        sa.Column("max_position_size", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("min_margin", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_risk_limits_id"), "risk_limits", ["id"], unique=False)
    op.create_index(op.f("ix_risk_limits_user_id"), "risk_limits", ["user_id"], unique=False)
    op.create_index(op.f("ix_risk_limits_asset"), "risk_limits", ["asset"], unique=False)
    op.create_index("ix_risk_limits_user_asset", "risk_limits", ["user_id", "asset"], unique=False)

    # Create risk_events table
    op.create_table(
        "risk_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("threshold", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("current_value", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("position_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_risk_events_id"), "risk_events", ["id"], unique=False)
    op.create_index(op.f("ix_risk_events_user_id"), "risk_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_risk_events_event_type"), "risk_events", ["event_type"], unique=False)
    op.create_index(
        op.f("ix_risk_events_position_id"), "risk_events", ["position_id"], unique=False
    )
    op.create_index(
        "ix_risk_events_user_created", "risk_events", ["user_id", "created_at"], unique=False
    )


def downgrade() -> None:
    # Drop risk_events table
    op.drop_index("ix_risk_events_user_created", table_name="risk_events")
    op.drop_index(op.f("ix_risk_events_position_id"), table_name="risk_events")
    op.drop_index(op.f("ix_risk_events_event_type"), table_name="risk_events")
    op.drop_index(op.f("ix_risk_events_user_id"), table_name="risk_events")
    op.drop_index(op.f("ix_risk_events_id"), table_name="risk_events")
    op.drop_table("risk_events")

    # Drop risk_limits table
    op.drop_index("ix_risk_limits_user_asset", table_name="risk_limits")
    op.drop_index(op.f("ix_risk_limits_asset"), table_name="risk_limits")
    op.drop_index(op.f("ix_risk_limits_user_id"), table_name="risk_limits")
    op.drop_index(op.f("ix_risk_limits_id"), table_name="risk_limits")
    op.drop_table("risk_limits")
