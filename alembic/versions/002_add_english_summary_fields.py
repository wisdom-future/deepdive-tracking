"""Add English summary fields to ProcessedNews table.

Revision ID: 002
Revises: 001
Create Date: 2025-11-03

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add English summary fields to processed_news table."""
    op.add_column(
        'processed_news',
        sa.Column('summary_pro_en', sa.Text(), nullable=True)
    )
    op.add_column(
        'processed_news',
        sa.Column('summary_sci_en', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Remove English summary fields from processed_news table."""
    op.drop_column('processed_news', 'summary_sci_en')
    op.drop_column('processed_news', 'summary_pro_en')
