"""Init: Create all database tables for DeepDive Tracking.

Revision ID: 001
Revises:
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables for the application."""

    # Create data_sources table
    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("method", sa.String(10), nullable=False, server_default="GET"),
        sa.Column("headers", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("params", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("auth_type", sa.String(50), nullable=True),
        sa.Column("auth_token", sa.String(1024), nullable=True),
        sa.Column("css_selectors", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("xpath_patterns", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("refresh_interval", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("max_items_per_run", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("supports_pagination", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("supports_filter", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("tags", postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default="[]"),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("type IN ('rss', 'crawler', 'api', 'twitter', 'email')", name="valid_source_type"),
        sa.CheckConstraint("priority BETWEEN 1 AND 10", name="valid_priority"),
    )

    # Create raw_news table
    op.create_table(
        "raw_news",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("html_content", sa.LargeBinary(), nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("source_name", sa.String(255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="raw"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_spam", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
        sa.UniqueConstraint("hash"),
        sa.CheckConstraint(
            "status IN ('raw', 'processing', 'processed', 'failed', 'duplicate')",
            name="valid_raw_news_status",
        ),
    )

    # Create processed_news table
    op.create_table(
        "processed_news",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_news_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("score_breakdown", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("sub_categories", postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default="[]"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("summary_pro", sa.Text(), nullable=False),
        sa.Column("summary_sci", sa.Text(), nullable=False),
        sa.Column("keywords", postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default="[]"),
        sa.Column("entities", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("tech_terms", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("infrastructure_tags", postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default="[]"),
        sa.Column("company_mentions", postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default="[]"),
        sa.Column("readability_score", sa.Float(), nullable=True),
        sa.Column("sentiment", sa.String(50), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("ai_models_used", postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default="[]"),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("cost_breakdown", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("previous_id", sa.Integer(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("quality_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["raw_news_id"], ["raw_news.id"], ),
        sa.ForeignKeyConstraint(["previous_id"], ["processed_news.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("raw_news_id"),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="valid_processed_score"),
        sa.CheckConstraint(
            "category IN ("
            "'company_news', 'tech_breakthrough', 'applications', "
            "'infrastructure', 'policy', 'market_trends', "
            "'expert_opinions', 'learning_resources')",
            name="valid_category",
        ),
    )

    # Create content_review table
    op.create_table(
        "content_review",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_news_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("reviewer_id", sa.String(255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("suggested_category", sa.String(50), nullable=True),
        sa.Column("suggested_score", sa.Float(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["processed_news_id"], ["processed_news.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("processed_news_id"),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'archived')",
            name="valid_review_status",
        ),
    )

    # Create published_content table
    op.create_table(
        "published_content",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_news_id", sa.Integer(), nullable=False),
        sa.Column("content_review_id", sa.Integer(), nullable=True),
        sa.Column("raw_news_id", sa.Integer(), nullable=False),
        sa.Column("publish_status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("channels", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("final_title", sa.String(512), nullable=True),
        sa.Column("final_summary_pro", sa.Text(), nullable=True),
        sa.Column("final_summary_sci", sa.Text(), nullable=True),
        sa.Column("final_keywords", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("wechat_msg_id", sa.String(255), nullable=True),
        sa.Column("wechat_url", sa.String(2048), nullable=True),
        sa.Column("xiaohongshu_post_id", sa.String(255), nullable=True),
        sa.Column("xiaohongshu_url", sa.String(2048), nullable=True),
        sa.Column("web_url", sa.String(2048), nullable=True),
        sa.Column("content_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("published_by", sa.String(255), nullable=True),
        sa.Column("publish_error", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("featured_image_url", sa.String(2048), nullable=True),
        sa.Column("images", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["processed_news_id"], ["processed_news.id"], ),
        sa.ForeignKeyConstraint(["content_review_id"], ["content_review.id"], ),
        sa.ForeignKeyConstraint(["raw_news_id"], ["raw_news.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "publish_status IN ('draft', 'scheduled', 'published', 'archived', 'failed')",
            name="valid_publish_status",
        ),
    )

    # Create content_stats table
    op.create_table(
        "content_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_content_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("share_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("read_time_avg", sa.Float(), nullable=True),
        sa.Column("click_through_rate", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["published_content_id"], ["published_content.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "channel IN ('wechat', 'xiaohongshu', 'web', 'email')",
            name="valid_channel",
        ),
    )

    # Create publishing_schedule table
    op.create_table(
        "publishing_schedule",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("schedule_type", sa.String(50), nullable=False),
        sa.Column("content_ids", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("target_channels", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("published_by", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('pending', 'in_progress', 'published', 'failed', 'cancelled')",
            name="valid_schedule_status",
        ),
    )

    # Create cost_log table
    op.create_table(
        "cost_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_news_id", sa.Integer(), nullable=True),
        sa.Column("service", sa.String(50), nullable=False),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("usage_units", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("total_cost", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("request_id", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["processed_news_id"], ["processed_news.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("total_cost >= 0", name="positive_cost"),
    )

    # Create operation_log table
    op.create_table(
        "operation_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("operation_type", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("operator_id", sa.String(255), nullable=False),
        sa.Column("operator_name", sa.String(255), nullable=True),
        sa.Column("action_detail", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
    )
    op.create_primary_key("operation_log_pkey", "operation_log", ["id"])

    # Create publishing_schedule_content table (many-to-many bridge)
    op.create_table(
        "publishing_schedule_content",
        sa.Column("schedule_id", sa.Integer(), nullable=False),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["schedule_id"], ["publishing_schedule.id"], ),
        sa.ForeignKeyConstraint(["content_id"], ["published_content.id"], ),
        sa.PrimaryKeyConstraint("schedule_id", "content_id"),
    )

    # Create indexes for better query performance
    op.create_index("ix_raw_news_source_id", "raw_news", ["source_id"])
    op.create_index("ix_raw_news_status", "raw_news", ["status"])
    op.create_index("ix_raw_news_published_at", "raw_news", ["published_at"])
    op.create_index("ix_raw_news_is_duplicate", "raw_news", ["is_duplicate"])

    op.create_index("ix_processed_news_raw_news_id", "processed_news", ["raw_news_id"])
    op.create_index("ix_processed_news_score", "processed_news", ["score"])
    op.create_index("ix_processed_news_category", "processed_news", ["category"])

    op.create_index("ix_content_review_processed_news_id", "content_review", ["processed_news_id"])
    op.create_index("ix_content_review_status", "content_review", ["status"])

    op.create_index("ix_published_content_processed_news_id", "published_content", ["processed_news_id"])
    op.create_index("ix_published_content_status", "published_content", ["publish_status"])
    op.create_index("ix_published_content_published_at", "published_content", ["published_at"])

    op.create_index("ix_content_stats_published_content_id", "content_stats", ["published_content_id"])
    op.create_index("ix_content_stats_channel", "content_stats", ["channel"])

    op.create_index("ix_publishing_schedule_status", "publishing_schedule", ["status"])
    op.create_index("ix_publishing_schedule_scheduled_at", "publishing_schedule", ["scheduled_at"])

    op.create_index("ix_cost_log_service", "cost_log", ["service"])
    op.create_index("ix_cost_log_created_at", "cost_log", ["created_at"])

    op.create_index("ix_operation_log_operation_type", "operation_log", ["operation_type"])
    op.create_index("ix_operation_log_created_at", "operation_log", ["created_at"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index("ix_operation_log_created_at", table_name="operation_log")
    op.drop_index("ix_operation_log_operation_type", table_name="operation_log")
    op.drop_index("ix_cost_log_created_at", table_name="cost_log")
    op.drop_index("ix_cost_log_service", table_name="cost_log")
    op.drop_index("ix_publishing_schedule_scheduled_at", table_name="publishing_schedule")
    op.drop_index("ix_publishing_schedule_status", table_name="publishing_schedule")
    op.drop_index("ix_content_stats_channel", table_name="content_stats")
    op.drop_index("ix_content_stats_published_content_id", table_name="content_stats")
    op.drop_index("ix_published_content_published_at", table_name="published_content")
    op.drop_index("ix_published_content_status", table_name="published_content")
    op.drop_index("ix_published_content_processed_news_id", table_name="published_content")
    op.drop_index("ix_content_review_status", table_name="content_review")
    op.drop_index("ix_content_review_processed_news_id", table_name="content_review")
    op.drop_index("ix_processed_news_category", table_name="processed_news")
    op.drop_index("ix_processed_news_score", table_name="processed_news")
    op.drop_index("ix_processed_news_raw_news_id", table_name="processed_news")
    op.drop_index("ix_raw_news_is_duplicate", table_name="raw_news")
    op.drop_index("ix_raw_news_published_at", table_name="raw_news")
    op.drop_index("ix_raw_news_status", table_name="raw_news")
    op.drop_index("ix_raw_news_source_id", table_name="raw_news")

    op.drop_table("publishing_schedule_content")
    op.drop_table("operation_log")
    op.drop_table("cost_log")
    op.drop_table("publishing_schedule")
    op.drop_table("content_stats")
    op.drop_table("published_content")
    op.drop_table("content_review")
    op.drop_table("processed_news")
    op.drop_table("raw_news")
    op.drop_table("data_sources")
