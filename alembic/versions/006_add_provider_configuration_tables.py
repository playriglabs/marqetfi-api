"""Add provider configuration tables

Revision ID: 006
Revises: 005
Create Date: 2025-12-19 02:52:11.982357

"""

# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This migration is now empty as ostium_settings and ostium_wallets
    # are handled in separate migrations (004 and 008)
    pass


def downgrade() -> None:
    pass
