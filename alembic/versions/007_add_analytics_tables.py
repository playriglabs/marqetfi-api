"""Add analytics tables

Revision ID: 007
Revises: 006
Create Date: 2025-12-19 02:52:41.123682

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create trade_history table
    op.create_table(
        "trade_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("trade_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trade_id"], ["trades.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trade_history_id"), "trade_history", ["id"], unique=False)
    op.create_index(op.f("ix_trade_history_user_id"), "trade_history", ["user_id"], unique=False)
    op.create_index(op.f("ix_trade_history_trade_id"), "trade_history", ["trade_id"], unique=False)

    # Create user_stats table
    op.create_table(
        "user_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("total_trades", sa.Integer(), nullable=False),
        sa.Column("winning_trades", sa.Integer(), nullable=False),
        sa.Column("losing_trades", sa.Integer(), nullable=False),
        sa.Column("total_pnl", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("total_volume", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("average_leverage", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("best_trade_pnl", sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column("worst_trade_pnl", sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column("last_trade_at", sa.DateTime(), nullable=True),
        sa.Column("calculated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_stats_id"), "user_stats", ["id"], unique=False)
    op.create_index(op.f("ix_user_stats_user_id"), "user_stats", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_stats_user_id"), table_name="user_stats")
    op.drop_index(op.f("ix_user_stats_id"), table_name="user_stats")
    op.drop_table("user_stats")
    op.drop_index(op.f("ix_trade_history_trade_id"), table_name="trade_history")
    op.drop_index(op.f("ix_trade_history_user_id"), table_name="trade_history")
    op.drop_index(op.f("ix_trade_history_id"), table_name="trade_history")
    op.drop_table("trade_history")
