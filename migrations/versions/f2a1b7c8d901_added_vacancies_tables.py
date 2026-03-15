"""added vacancies tables

Revision ID: f2a1b7c8d901
Revises: d1e2bd92fa48
Create Date: 2026-03-13 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f2a1b7c8d901'
down_revision: Union[str, Sequence[str], None] = 'd1e2bd92fa48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vacancy_type') THEN
                CREATE TYPE vacancy_type AS ENUM ('ONLINE', 'OFFLINE');
            END IF;
        END$$;
        """
    )

    vacancy_type = postgresql.ENUM('ONLINE', 'OFFLINE', name='vacancy_type', create_type=False)

    op.create_table(
        'vacancies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('direction_id', sa.Integer(), nullable=False),
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('salary_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('salary_currency', sa.String(length=10), nullable=True),
        sa.Column('vacancy_type', vacancy_type, nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['direction_id'], ['directions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vacancies_city_id'), 'vacancies', ['city_id'], unique=False)
    op.create_index(op.f('ix_vacancies_created_at'), 'vacancies', ['created_at'], unique=False)
    op.create_index(op.f('ix_vacancies_direction_id'), 'vacancies', ['direction_id'], unique=False)
    op.create_index(op.f('ix_vacancies_id'), 'vacancies', ['id'], unique=False)
    op.create_index(op.f('ix_vacancies_title'), 'vacancies', ['title'], unique=False)
    op.create_index(op.f('ix_vacancies_updated_at'), 'vacancies', ['updated_at'], unique=False)

    op.create_table(
        'vacancy_skills',
        sa.Column('vacancy_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vacancy_id'], ['vacancies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('vacancy_id', 'skill_id')
    )

    op.create_table(
        'user_vacancies',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('vacancy_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vacancy_id'], ['vacancies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'vacancy_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('user_vacancies')
    op.drop_table('vacancy_skills')
    op.drop_index(op.f('ix_vacancies_updated_at'), table_name='vacancies')
    op.drop_index(op.f('ix_vacancies_title'), table_name='vacancies')
    op.drop_index(op.f('ix_vacancies_id'), table_name='vacancies')
    op.drop_index(op.f('ix_vacancies_direction_id'), table_name='vacancies')
    op.drop_index(op.f('ix_vacancies_created_at'), table_name='vacancies')
    op.drop_index(op.f('ix_vacancies_city_id'), table_name='vacancies')
    op.drop_table('vacancies')

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vacancy_type') THEN
                DROP TYPE vacancy_type;
            END IF;
        END$$;
        """
    )
