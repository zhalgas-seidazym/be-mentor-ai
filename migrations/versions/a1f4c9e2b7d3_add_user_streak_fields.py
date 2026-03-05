"""add user streak fields

Revision ID: a1f4c9e2b7d3
Revises: d1e2bd92fa48
Create Date: 2026-03-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1f4c9e2b7d3"
down_revision: Union[str, Sequence[str], None] = "d1e2bd92fa48"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("longest_streak", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("last_interview_day", sa.Date(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("timezone", sa.String(), nullable=False, server_default="UTC"),
    )

    # Keep defaults in ORM, not hard DB defaults.
    op.alter_column("users", "current_streak", server_default=None)
    op.alter_column("users", "longest_streak", server_default=None)
    op.alter_column("users", "timezone", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "timezone")
    op.drop_column("users", "last_interview_day")
    op.drop_column("users", "longest_streak")
    op.drop_column("users", "current_streak")

