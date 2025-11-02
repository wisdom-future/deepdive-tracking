"""Publishing service for publishing content to multiple channels."""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from src.models import PublishedContent, ProcessedNews, ContentReview, RawNews

logger = logging.getLogger(__name__)


class PublishingService:
    """Service for managing content publishing to multiple channels."""

    SUPPORTED_CHANNELS = ["wechat", "xiaohongshu", "website"]

    def __init__(self, db_session: Session):
        """Initialize publishing service.

        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db_session = db_session
        self.logger = logger

    def create_publishing_plan(
        self,
        processed_news_id: int,
        channels: List[str],
        scheduled_at: Optional[datetime] = None,
        content_review_id: Optional[int] = None
    ) -> PublishedContent:
        """Create a publishing plan for content.

        Args:
            processed_news_id: ID of processed news
            channels: List of channels to publish to
            scheduled_at: Scheduled publish time
            content_review_id: Optional review ID

        Returns:
            PublishedContent record

        Raises:
            ValueError: If processed news not found or invalid channel
        """
        # Validate processed news exists
        processed_news = self.db_session.query(ProcessedNews).filter(
            ProcessedNews.id == processed_news_id
        ).first()

        if not processed_news:
            raise ValueError(f"Processed news {processed_news_id} not found")

        # Validate channels
        invalid_channels = set(channels) - set(self.SUPPORTED_CHANNELS)
        if invalid_channels:
            raise ValueError(f"Invalid channels: {invalid_channels}")

        # Get raw news ID
        raw_news_id = processed_news.raw_news_id

        # Create publishing plan
        published_content = PublishedContent(
            processed_news_id=processed_news_id,
            raw_news_id=raw_news_id,
            content_review_id=content_review_id,
            channels=channels,
            scheduled_at=scheduled_at,
            publish_status="draft"
        )

        self.db_session.add(published_content)
        self.db_session.commit()

        self.logger.info(
            f"Created publishing plan for processed_news {processed_news_id} "
            f"to {', '.join(channels)}"
        )
        return published_content

    def get_scheduled_content(self, limit: int = 100) -> List[PublishedContent]:
        """Get content scheduled for publishing.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of PublishedContent ready to publish
        """
        from sqlalchemy import and_, or_

        now = datetime.utcnow()

        content = self.db_session.query(PublishedContent).filter(
            and_(
                PublishedContent.publish_status.in_(["scheduled", "draft"]),
                or_(
                    PublishedContent.scheduled_at.is_(None),
                    PublishedContent.scheduled_at <= now
                )
            )
        ).order_by(PublishedContent.scheduled_at).limit(limit).all()

        return content

    def publish_to_channel(
        self,
        published_content_id: int,
        channel: str,
        channel_url: str,
        channel_id: str = "",
        publisher_name: str = "system"
    ) -> PublishedContent:
        """Mark content as published to a specific channel.

        Args:
            published_content_id: ID of published content
            channel: Channel name (wechat, xiaohongshu, website)
            channel_url: URL of published content
            channel_id: Channel-specific ID (message ID, post ID, etc.)
            publisher_name: Name of the publisher

        Returns:
            Updated PublishedContent

        Raises:
            ValueError: If published content not found or invalid channel
        """
        published_content = self.db_session.query(PublishedContent).filter(
            PublishedContent.id == published_content_id
        ).first()

        if not published_content:
            raise ValueError(f"Published content {published_content_id} not found")

        if channel not in self.SUPPORTED_CHANNELS:
            raise ValueError(f"Unsupported channel: {channel}")

        # Update channel-specific fields
        if channel == "wechat":
            published_content.wechat_url = channel_url
            published_content.wechat_msg_id = channel_id
        elif channel == "xiaohongshu":
            published_content.xiaohongshu_url = channel_url
            published_content.xiaohongshu_post_id = channel_id
        elif channel == "website":
            published_content.web_url = channel_url

        published_content.published_by = publisher_name

        # Check if all channels are published
        channels_published = 0
        if published_content.wechat_url:
            channels_published += 1
        if published_content.xiaohongshu_url:
            channels_published += 1
        if published_content.web_url:
            channels_published += 1

        if channels_published == len(published_content.channels):
            published_content.publish_status = "published"
            published_content.published_at = datetime.utcnow()

        self.db_session.commit()

        self.logger.info(
            f"Published content {published_content_id} to {channel}: {channel_url}"
        )
        return published_content

    def mark_published(
        self,
        published_content_id: int,
        final_title: Optional[str] = None,
        final_summary_pro: Optional[str] = None,
        final_summary_sci: Optional[str] = None,
        final_keywords: Optional[List[str]] = None,
        publisher_name: str = "system"
    ) -> PublishedContent:
        """Mark content as published with final content.

        Args:
            published_content_id: ID of published content
            final_title: Final published title
            final_summary_pro: Final professional summary
            final_summary_sci: Final scientific summary
            final_keywords: Final keywords
            publisher_name: Name of the publisher

        Returns:
            Updated PublishedContent

        Raises:
            ValueError: If published content not found
        """
        published_content = self.db_session.query(PublishedContent).filter(
            PublishedContent.id == published_content_id
        ).first()

        if not published_content:
            raise ValueError(f"Published content {published_content_id} not found")

        # Store final content
        if final_title:
            published_content.final_title = final_title
        if final_summary_pro:
            published_content.final_summary_pro = final_summary_pro
        if final_summary_sci:
            published_content.final_summary_sci = final_summary_sci
        if final_keywords:
            published_content.final_keywords = final_keywords

        published_content.publish_status = "published"
        published_content.published_at = datetime.utcnow()
        published_content.published_by = publisher_name

        self.db_session.commit()

        self.logger.info(f"Marked content {published_content_id} as published")
        return published_content

    def retry_publish(
        self,
        published_content_id: int,
        error_message: str = ""
    ) -> PublishedContent:
        """Mark a publishing attempt as failed and retry.

        Args:
            published_content_id: ID of published content
            error_message: Error message from failed attempt

        Returns:
            Updated PublishedContent

        Raises:
            ValueError: If published content not found
        """
        published_content = self.db_session.query(PublishedContent).filter(
            PublishedContent.id == published_content_id
        ).first()

        if not published_content:
            raise ValueError(f"Published content {published_content_id} not found")

        published_content.retry_count = (published_content.retry_count or 0) + 1
        published_content.last_retry_at = datetime.utcnow()
        published_content.publish_error = error_message

        # Mark as failed if too many retries
        if published_content.retry_count >= 3:
            published_content.publish_status = "failed"

        self.db_session.commit()

        self.logger.info(
            f"Retrying publish for content {published_content_id} "
            f"(attempt {published_content.retry_count})"
        )
        return published_content

    def get_publishing_stats(self) -> Dict[str, Any]:
        """Get publishing statistics.

        Returns:
            Dictionary with publishing statistics
        """
        total = self.db_session.query(PublishedContent).count()
        published = self.db_session.query(PublishedContent).filter(
            PublishedContent.publish_status == "published"
        ).count()
        scheduled = self.db_session.query(PublishedContent).filter(
            PublishedContent.publish_status.in_(["scheduled", "draft"])
        ).count()
        failed = self.db_session.query(PublishedContent).filter(
            PublishedContent.publish_status == "failed"
        ).count()

        return {
            "total": total,
            "published": published,
            "scheduled": scheduled,
            "failed": failed,
            "publish_rate": published / total * 100 if total > 0 else 0
        }
