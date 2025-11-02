"""initial: create all tables

Revision ID: 001
Revises:
Create Date: 2025-11-02 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create data_sources table
    op.create_table(
        'data_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=True),
        sa.Column('method', sa.String(length=10), server_default='GET', nullable=False),
        sa.Column('headers', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('params', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('auth_type', sa.String(length=50), nullable=True),
        sa.Column('auth_token', sa.String(length=1024), nullable=True),
        sa.Column('css_selectors', sa.JSON(), nullable=True),
        sa.Column('xpath_patterns', sa.JSON(), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='5', nullable=False),
        sa.Column('refresh_interval', sa.Integer(), server_default='30', nullable=False),
        sa.Column('max_items_per_run', sa.Integer(), server_default='50', nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_check_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('consecutive_failures', sa.Integer(), server_default='0', nullable=False),
        sa.Column('supports_pagination', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('supports_filter', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('tags', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.CheckConstraint("type IN ('rss', 'crawler', 'api', 'twitter', 'email')", name='valid_source_type'),
        sa.CheckConstraint('priority BETWEEN 1 AND 10', name='valid_priority'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'type', name='_unique_datasource_name_type'),
    )

    # Create raw_news table
    op.create_table(
        'raw_news',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('html_content', sa.LargeBinary(), nullable=True),
        sa.Column('language', sa.String(length=10), server_default='en', nullable=False),
        sa.Column('hash', sa.String(length=64), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('source_name', sa.String(length=255), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='raw', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_spam', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('raw', 'processing', 'processed', 'failed', 'duplicate')", name='valid_raw_news_status'),
        sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url', name='_unique_raw_news_url'),
        sa.UniqueConstraint('hash', name='_unique_raw_news_hash'),
    )

    # Create processed_news table
    op.create_table(
        'processed_news',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_news_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('score_breakdown', sa.JSON(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('sub_categories', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('summary_pro', sa.Text(), nullable=False),
        sa.Column('summary_sci', sa.Text(), nullable=False),
        sa.Column('keywords', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('entities', sa.JSON(), nullable=True),
        sa.Column('tech_terms', sa.JSON(), nullable=True),
        sa.Column('infrastructure_tags', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('company_mentions', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('readability_score', sa.Float(), nullable=True),
        sa.Column('sentiment', sa.String(length=50), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('ai_models_used', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('cost_breakdown', sa.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('previous_id', sa.Integer(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('quality_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.CheckConstraint('score BETWEEN 0 AND 100', name='valid_processed_score'),
        sa.CheckConstraint("category IN ('company_news', 'tech_breakthrough', 'applications', 'infrastructure', 'policy', 'market_trends', 'expert_opinions', 'learning_resources')", name='valid_category'),
        sa.ForeignKeyConstraint(['previous_id'], ['processed_news.id']),
        sa.ForeignKeyConstraint(['raw_news_id'], ['raw_news.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('raw_news_id', name='_unique_processed_news_raw_news'),
    )

    # Create content_review table
    op.create_table(
        'content_review',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('processed_news_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.String(length=255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_decision', sa.String(length=50), nullable=True),
        sa.Column('title_edited', sa.String(length=512), nullable=True),
        sa.Column('summary_pro_edited', sa.Text(), nullable=True),
        sa.Column('summary_sci_edited', sa.Text(), nullable=True),
        sa.Column('keywords_edited', sa.JSON(), nullable=True),
        sa.Column('category_edited', sa.String(length=50), nullable=True),
        sa.Column('editor_notes', sa.Text(), nullable=True),
        sa.Column('edited_by', sa.String(length=255), nullable=True),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('change_log', sa.JSON(), nullable=True),
        sa.Column('checked_sensitive_words', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('has_sensitive_words', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('sensitive_words_detail', sa.Text(), nullable=True),
        sa.Column('checked_copyright', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('copyright_issues', sa.Text(), nullable=True),
        sa.Column('checked_technical_accuracy', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('technical_accuracy_notes', sa.Text(), nullable=True),
        sa.Column('reviewer_confidence', sa.Float(), nullable=True),
        sa.Column('reviewer_tags', sa.JSON(), nullable=True),
        sa.Column('send_back_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('final_decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected', 'needs_edit', 'in_review')", name='valid_review_status'),
        sa.ForeignKeyConstraint(['processed_news_id'], ['processed_news.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('processed_news_id', name='_unique_content_review'),
    )

    # Create published_content table
    op.create_table(
        'published_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('processed_news_id', sa.Integer(), nullable=False),
        sa.Column('content_review_id', sa.Integer(), nullable=True),
        sa.Column('raw_news_id', sa.Integer(), nullable=False),
        sa.Column('publish_status', sa.String(length=50), server_default='draft', nullable=False),
        sa.Column('channels', sa.JSON(), nullable=False),
        sa.Column('final_title', sa.String(length=512), nullable=True),
        sa.Column('final_summary_pro', sa.Text(), nullable=True),
        sa.Column('final_summary_sci', sa.Text(), nullable=True),
        sa.Column('final_keywords', sa.JSON(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('wechat_msg_id', sa.String(length=255), nullable=True),
        sa.Column('wechat_url', sa.String(length=2048), nullable=True),
        sa.Column('xiaohongshu_post_id', sa.String(length=255), nullable=True),
        sa.Column('xiaohongshu_url', sa.String(length=2048), nullable=True),
        sa.Column('web_url', sa.String(length=2048), nullable=True),
        sa.Column('content_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('published_by', sa.String(length=255), nullable=True),
        sa.Column('publish_error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('featured_image_url', sa.String(length=2048), nullable=True),
        sa.Column('images', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.CheckConstraint("publish_status IN ('draft', 'scheduled', 'published', 'archived', 'failed')", name='valid_publish_status'),
        sa.ForeignKeyConstraint(['content_review_id'], ['content_review.id']),
        sa.ForeignKeyConstraint(['processed_news_id'], ['processed_news.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['raw_news_id'], ['raw_news.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create content_stats table
    op.create_table(
        'content_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('published_content_id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('view_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('unique_viewers', sa.Integer(), server_default='0', nullable=False),
        sa.Column('read_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('completion_rate', sa.Float(), nullable=True),
        sa.Column('avg_read_time', sa.Integer(), nullable=True),
        sa.Column('like_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('share_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('comment_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('collection_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('click_through_rate', sa.Float(), nullable=True),
        sa.Column('social_share_rate', sa.Float(), nullable=True),
        sa.Column('nps_score', sa.Integer(), nullable=True),
        sa.Column('nps_feedback_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('rating_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('referrer_stats', sa.JSON(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.CheckConstraint("channel IN ('wechat', 'xiaohongshu', 'web', 'email')", name='valid_channel'),
        sa.ForeignKeyConstraint(['published_content_id'], ['published_content.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create publishing_schedules table
    op.create_table(
        'publishing_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_type', sa.String(length=50), nullable=False),
        sa.Column('content_ids', sa.JSON(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('execution_window_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_window_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('target_channels', sa.JSON(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('template_variables', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('max_retries', sa.Integer(), server_default='3', nullable=False),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('can_rollback', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('rollback_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rolled_back', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('rollback_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'running', 'completed', 'failed', 'cancelled')", name='valid_schedule_status'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create cost_logs table
    op.create_table(
        'cost_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('processed_news_id', sa.Integer(), nullable=True),
        sa.Column('publishing_schedule_id', sa.Integer(), nullable=True),
        sa.Column('service', sa.String(length=100), nullable=False),
        sa.Column('operation', sa.String(length=100), nullable=False),
        sa.Column('usage_units', sa.Integer(), nullable=True),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('request_id', sa.String(length=255), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('total_cost >= 0', name='positive_cost'),
        sa.ForeignKeyConstraint(['processed_news_id'], ['processed_news.id']),
        sa.ForeignKeyConstraint(['publishing_schedule_id'], ['publishing_schedules.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create operation_logs table
    op.create_table(
        'operation_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('operator_id', sa.String(length=255), nullable=True),
        sa.Column('operator_name', sa.String(length=255), nullable=True),
        sa.Column('action_detail', sa.Text(), nullable=True),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes
    op.create_index('idx_sources_enabled_priority', 'data_sources', ['is_enabled', 'priority'], unique=False)
    op.create_index('idx_sources_last_check', 'data_sources', ['last_check_at'], unique=False)
    op.create_index('idx_sources_type', 'data_sources', ['type'], unique=False)

    op.create_index('idx_raw_news_status_created', 'raw_news', ['status', 'created_at'], unique=False)
    op.create_index('idx_raw_news_source_time', 'raw_news', ['source_id', 'published_at'], unique=False)
    op.create_index('idx_raw_news_url', 'raw_news', ['url'], unique=False)
    op.create_index('idx_raw_news_hash', 'raw_news', ['hash'], unique=False)
    op.create_index('idx_raw_news_published', 'raw_news', ['published_at'], unique=False)

    op.create_index('idx_processed_score_desc', 'processed_news', ['score'], unique=False)
    op.create_index('idx_processed_category', 'processed_news', ['category'], unique=False)
    op.create_index('idx_processed_confidence', 'processed_news', ['confidence'], unique=False)
    op.create_index('idx_processed_created', 'processed_news', ['created_at'], unique=False)
    op.create_index('idx_processed_company_mentions', 'processed_news', ['company_mentions'], unique=False, postgresql_using='gin')
    op.create_index('idx_processed_keywords', 'processed_news', ['keywords'], unique=False, postgresql_using='gin')

    op.create_index('idx_review_status', 'content_review', ['status'], unique=False)
    op.create_index('idx_review_reviewed_at', 'content_review', ['reviewed_at'], unique=False)
    op.create_index('idx_review_edited_by', 'content_review', ['edited_by'], unique=False)

    op.create_index('idx_published_status', 'published_content', ['publish_status'], unique=False)
    op.create_index('idx_published_published_at', 'published_content', ['published_at'], unique=False)
    op.create_index('idx_published_scheduled', 'published_content', ['scheduled_at'], unique=False, postgresql_where="publish_status = 'scheduled'")
    op.create_index('idx_published_channels', 'published_content', ['channels'], unique=False, postgresql_using='gin')

    op.create_index('idx_stats_content_channel', 'content_stats', ['published_content_id', 'channel'], unique=False)
    op.create_index('idx_stats_completion_rate', 'content_stats', ['completion_rate'], unique=False, postgresql_where='completion_rate > 0')
    op.create_index('idx_stats_updated', 'content_stats', ['updated_at'], unique=False)

    op.create_index('idx_schedules_time', 'publishing_schedules', ['scheduled_at', 'status'], unique=False)
    op.create_index('idx_schedules_status', 'publishing_schedules', ['status'], unique=False, postgresql_where="status IN ('pending', 'running')")

    op.create_index('idx_cost_service_date', 'cost_logs', ['service', 'created_at'], unique=False)
    op.create_index('idx_cost_date', 'cost_logs', ['created_at'], unique=False)

    op.create_index('idx_operation_type_date', 'operation_logs', ['operation_type', 'created_at'], unique=False)
    op.create_index('idx_operation_resource', 'operation_logs', ['resource_type', 'resource_id'], unique=False)
    op.create_index('idx_operation_operator', 'operation_logs', ['operator_id', 'created_at'], unique=False)


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_index('idx_operation_operator')
    op.drop_index('idx_operation_resource')
    op.drop_index('idx_operation_type_date')
    op.drop_index('idx_cost_date')
    op.drop_index('idx_cost_service_date')
    op.drop_index('idx_schedules_status')
    op.drop_index('idx_schedules_time')
    op.drop_index('idx_stats_updated')
    op.drop_index('idx_stats_completion_rate')
    op.drop_index('idx_stats_content_channel')
    op.drop_index('idx_published_channels')
    op.drop_index('idx_published_scheduled')
    op.drop_index('idx_published_published_at')
    op.drop_index('idx_published_status')
    op.drop_index('idx_review_edited_by')
    op.drop_index('idx_review_reviewed_at')
    op.drop_index('idx_review_status')
    op.drop_index('idx_processed_keywords')
    op.drop_index('idx_processed_company_mentions')
    op.drop_index('idx_processed_created')
    op.drop_index('idx_processed_confidence')
    op.drop_index('idx_processed_category')
    op.drop_index('idx_processed_score_desc')
    op.drop_index('idx_raw_news_published')
    op.drop_index('idx_raw_news_hash')
    op.drop_index('idx_raw_news_url')
    op.drop_index('idx_raw_news_source_time')
    op.drop_index('idx_raw_news_status_created')
    op.drop_index('idx_sources_type')
    op.drop_index('idx_sources_last_check')
    op.drop_index('idx_sources_enabled_priority')

    op.drop_table('operation_logs')
    op.drop_table('cost_logs')
    op.drop_table('publishing_schedules')
    op.drop_table('content_stats')
    op.drop_table('published_content')
    op.drop_table('content_review')
    op.drop_table('processed_news')
    op.drop_table('raw_news')
    op.drop_table('data_sources')
