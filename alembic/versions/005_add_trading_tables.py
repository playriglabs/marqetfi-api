"""Add trading tables

Revision ID: 005
Revises: 003
Create Date: 2025-12-19 02:51:11.982357

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create orders table
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_type", sa.String(length=20), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("asset", sa.String(length=20), nullable=False),
        sa.Column("quote", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("price", sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column("leverage", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_order_id", sa.String(length=255), nullable=True),
        sa.Column("transaction_hash", sa.String(length=66), nullable=True),
        sa.Column("filled_quantity", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("average_fill_price", sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("filled_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_id"), "orders", ["id"], unique=False)
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)
    op.create_index("ix_orders_user_status", "orders", ["user_id", "status"], unique=False)
    op.create_index(
        "ix_orders_provider_order_id", "orders", ["provider", "provider_order_id"], unique=False
    )

    # Create trades table
    op.create_table(
        "trades",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("pair_id", sa.Integer(), nullable=False),
        sa.Column("trade_index", sa.Integer(), nullable=False),
        sa.Column("asset", sa.String(length=20), nullable=False),
        sa.Column("quote", sa.String(length=20), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("entry_price", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("leverage", sa.Integer(), nullable=False),
        sa.Column("collateral", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("tp_price", sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column("sl_price", sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column("exit_price", sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column("pnl", sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column("pnl_percentage", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_trade_id", sa.String(length=255), nullable=False),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trades_id"), "trades", ["id"], unique=False)
    op.create_index(op.f("ix_trades_order_id"), "trades", ["order_id"], unique=False)
    op.create_index(op.f("ix_trades_status"), "trades", ["status"], unique=False)
    op.create_index("ix_trades_user_status", "trades", ["user_id", "status"], unique=False)
    op.create_index(
        "ix_trades_provider_trade_id", "trades", ["provider", "provider_trade_id"], unique=False
    )
    op.create_index(
        "ix_trades_pair_trade_index", "trades", ["pair_id", "trade_index"], unique=False
    )

    # Create positions table
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("trade_id", sa.Integer(), nullable=False),
        sa.Column("asset", sa.String(length=20), nullable=False),
        sa.Column("quote", sa.String(length=20), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("size", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("entry_price", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("current_price", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("leverage", sa.Integer(), nullable=False),
        sa.Column("collateral", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("unrealized_pnl", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("unrealized_pnl_percentage", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("liquidation_price", sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column("margin_ratio", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trade_id"], ["trades.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trade_id"),
    )
    op.create_index(op.f("ix_positions_id"), "positions", ["id"], unique=False)
    op.create_index(op.f("ix_positions_trade_id"), "positions", ["trade_id"], unique=False)
    op.create_index("ix_positions_user", "positions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_positions_user", table_name="positions")
    op.drop_index(op.f("ix_positions_trade_id"), table_name="positions")
    op.drop_index(op.f("ix_positions_id"), table_name="positions")
    op.drop_table("positions")
    op.drop_index("ix_trades_pair_trade_index", table_name="trades")
    op.drop_index("ix_trades_provider_trade_id", table_name="trades")
    op.drop_index("ix_trades_user_status", table_name="trades")
    op.drop_index(op.f("ix_trades_status"), table_name="trades")
    op.drop_index(op.f("ix_trades_order_id"), table_name="trades")
    op.drop_index(op.f("ix_trades_id"), table_name="trades")
    op.drop_table("trades")
    op.drop_index("ix_orders_provider_order_id", table_name="orders")
    op.drop_index("ix_orders_user_status", table_name="orders")
    op.drop_index(op.f("ix_orders_status"), table_name="orders")
    op.drop_index(op.f("ix_orders_id"), table_name="orders")
    op.drop_table("orders")
