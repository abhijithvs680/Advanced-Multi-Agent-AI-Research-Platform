"""Add state_results column to jobs table

Revision ID: 002
Revises: 001
Create Date: 2026-01-02 14:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '6d4d6dde8789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add state_results column to jobs table (for UI visualization)
    op.add_column(
        'jobs',
        sa.Column('state_results', postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('jobs', 'state_results')
