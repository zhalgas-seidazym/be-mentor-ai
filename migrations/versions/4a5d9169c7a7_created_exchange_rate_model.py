"""created exchange rate model

Revision ID: 4a5d9169c7a7
Revises: 80c5207116ff
Create Date: 2026-04-22 18:10:52.177793

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a5d9169c7a7'
down_revision: Union[str, Sequence[str], None] = '80c5207116ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
