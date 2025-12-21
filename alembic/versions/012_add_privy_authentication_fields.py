"""Add Privy authentication fields

Revision ID: 012
Revises: 011
Create Date: 2025-01-22 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add privy_user_id to users table (unique, indexed, nullable)
    op.add_column("users", sa.Column("privy_user_id", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_users_privy_user_id"), "users", ["privy_user_id"], unique=True)


def downgrade() -> None:
    # Remove privy_user_id index and column
    op.drop_index(op.f("ix_users_privy_user_id"), table_name="users")
    op.drop_column("users", "privy_user_id")
