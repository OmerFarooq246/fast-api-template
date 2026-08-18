"""Add user account status.

Revision ID: 4c38d1f5a1b2
Revises: c8654356d733
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "4c38d1f5a1b2"
down_revision: str | None = "c8654356d733"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "is_active")
