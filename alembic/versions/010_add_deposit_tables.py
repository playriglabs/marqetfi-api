"""Add deposit tables

Revision ID: 010
Revises: 009
Create Date: 2025-01-21 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create deposits table
    op.create_table(
        "deposits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_address", sa.String(length=42), nullable=False),
        sa.Column("token_symbol", sa.String(length=20), nullable=False),
        sa.Column("chain", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("transaction_hash", sa.String(length=66), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deposits_id"), "deposits", ["id"], unique=False)
    op.create_index("ix_deposits_user_status", "deposits", ["user_id", "status"], unique=False)
    op.create_index("ix_deposits_provider", "deposits", ["provider"], unique=False)
    op.create_index("ix_deposits_transaction_hash", "deposits", ["transaction_hash"], unique=False)

    # Create token_swaps table
    op.create_table(
        "token_swaps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("deposit_id", sa.Integer(), nullable=False),
        sa.Column("from_token", sa.String(length=42), nullable=False),
        sa.Column("to_token", sa.String(length=42), nullable=False),
        sa.Column("from_chain", sa.String(length=50), nullable=False),
        sa.Column("to_chain", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("swap_provider", sa.String(length=50), nullable=False),
        sa.Column("swap_status", sa.String(length=20), nullable=False),
        sa.Column("swap_transaction_hash", sa.String(length=66), nullable=True),
        sa.Column("estimated_output", sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column("actual_output", sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["deposit_id"], ["deposits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_token_swaps_id"), "token_swaps", ["id"], unique=False)
    op.create_index("ix_token_swaps_deposit", "token_swaps", ["deposit_id"], unique=False)
    op.create_index("ix_token_swaps_status", "token_swaps", ["swap_status"], unique=False)
    op.create_index(
        "ix_token_swaps_transaction_hash", "token_swaps", ["swap_transaction_hash"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_token_swaps_transaction_hash", table_name="token_swaps")
    op.drop_index("ix_token_swaps_status", table_name="token_swaps")
    op.drop_index("ix_token_swaps_deposit", table_name="token_swaps")
    op.drop_index(op.f("ix_token_swaps_id"), table_name="token_swaps")
    op.drop_table("token_swaps")

    op.drop_index("ix_deposits_transaction_hash", table_name="deposits")
    op.drop_index("ix_deposits_provider", table_name="deposits")
    op.drop_index("ix_deposits_user_status", table_name="deposits")
    op.drop_index(op.f("ix_deposits_id"), table_name="deposits")
    op.drop_table("deposits")
