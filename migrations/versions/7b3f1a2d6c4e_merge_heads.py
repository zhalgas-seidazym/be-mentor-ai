"""merge heads

Revision ID: 7b3f1a2d6c4e
Revises: 4c01beffda8c, f2a1b7c8d901
Create Date: 2026-03-15 21:55:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7b3f1a2d6c4e'
down_revision: Union[str, Sequence[str], None] = ('4c01beffda8c', 'f2a1b7c8d901')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
