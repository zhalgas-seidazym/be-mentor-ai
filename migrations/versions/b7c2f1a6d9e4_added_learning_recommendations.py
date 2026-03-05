"""added learning recommendations

Revision ID: b7c2f1a6d9e4
Revises: a1f4c9e2b7d3
Create Date: 2026-03-05 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7c2f1a6d9e4"
down_revision: Union[str, Sequence[str], None] = "a1f4c9e2b7d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "learning_recommendations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=2048), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_learning_recommendations_id"),
        "learning_recommendations",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_learning_recommendations_skill_id"),
        "learning_recommendations",
        ["skill_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_learning_recommendations_created_at"),
        "learning_recommendations",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_learning_recommendations_updated_at"),
        "learning_recommendations",
        ["updated_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_learning_recommendations_updated_at"), table_name="learning_recommendations")
    op.drop_index(op.f("ix_learning_recommendations_created_at"), table_name="learning_recommendations")
    op.drop_index(op.f("ix_learning_recommendations_skill_id"), table_name="learning_recommendations")
    op.drop_index(op.f("ix_learning_recommendations_id"), table_name="learning_recommendations")
    op.drop_table("learning_recommendations")
