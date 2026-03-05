"""make user password nullable

Revision ID: 4c01beffda8c
Revises: b7c2f1a6d9e4
Create Date: 2026-03-05 11:45:26.970878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c01beffda8c'
down_revision: Union[str, Sequence[str], None] = 'b7c2f1a6d9e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "users",
        "password",
        existing_type=sa.String(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "users",
        "password",
        existing_type=sa.String(),
        nullable=False,
    )
