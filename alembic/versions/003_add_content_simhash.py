"""Add content_simhash field to RawNews table for similarity detection.

Revision ID: 003
Revises: 002
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add content_simhash field and index to raw_news table."""
    # Add content_simhash column
    op.add_column(
        'raw_news',
        sa.Column('content_simhash', sa.BigInteger(), nullable=True, comment='Content simhash for similarity detection')
    )

    # Add index for performance (similarity queries)
    op.create_index(
        'ix_raw_news_content_simhash',
        'raw_news',
        ['content_simhash']
    )


def downgrade() -> None:
    """Remove content_simhash field and index from raw_news table."""
    # Drop index first
    op.drop_index('ix_raw_news_content_simhash', table_name='raw_news')

    # Drop column
    op.drop_column('raw_news', 'content_simhash')
