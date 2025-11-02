"""WeChat publishing workflow orchestration service."""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from src.services.publishing.publishing_service import PublishingService
from src.models import ContentReview, PublishedContent, ProcessedNews, RawNews

logger = logging.getLogger(__name__)


class WeChatPublishingWorkflow:
    """Orchestrates the WeChat publishing workflow."""

    def __init__(
        self,
        db_session: Session,
        wechat_app_id: str,
        wechat_app_secret: str
    ):
        """Initialize WeChat publishing workflow.

        Args:
            db_session: SQLAlchemy session for database operations
            wechat_app_id: WeChat Official Account App ID
            wechat_app_secret: WeChat Official Account App Secret
        """
        self.db_session = db_session
        self.publishing_service = PublishingService(
            db_session=db_session,
            wechat_app_id=wechat_app_id,
            wechat_app_secret=wechat_app_secret
        )
        self.logger = logger

    def execute(self) -> Dict[str, Any]:
        """Execute the WeChat publishing workflow.

        Workflow steps:
        1. Get approved but unpublished articles
        2. Create publishing plans
        3. Publish to WeChat
        4. Generate statistics

        Returns:
            Dictionary with workflow results:
            {
                "success": bool,
                "published_count": int,
                "failed_count": int,
                "stats": dict,
                "articles": list,
                "error": str (if failed)
            }
        """
        try:
            self.logger.info("Starting WeChat publishing workflow")

            # Get approved reviews
            approved_reviews = self.db_session.query(ContentReview).filter(
                ContentReview.status == "approved"
            ).all()

            if not approved_reviews:
                self.logger.info("No approved articles to publish")
                return {
                    "success": True,
                    "published_count": 0,
                    "failed_count": 0,
                    "articles": [],
                    "message": "No approved articles to publish"
                }

            # Filter unpublished articles
            articles_to_publish = []
            for review in approved_reviews:
                existing_publish = self.db_session.query(PublishedContent).filter(
                    PublishedContent.processed_news_id == review.processed_news_id
                ).first()

                if not existing_publish:
                    articles_to_publish.append(review)

            self.logger.info(f"Found {len(articles_to_publish)} articles to publish")

            # Publish articles
            published_count = 0
            failed_count = 0
            published_articles = []

            for review in articles_to_publish:
                try:
                    # Create publishing plan
                    pub_content = self.publishing_service.create_publishing_plan(
                        processed_news_id=review.processed_news_id,
                        channels=["wechat"],
                        content_review_id=review.id
                    )

                    # Publish to WeChat
                    result = self.publishing_service.publish_to_wechat(
                        published_content_id=pub_content.id
                    )

                    if result.wechat_url:
                        published_count += 1
                        published_articles.append({
                            "id": result.id,
                            "url": result.wechat_url,
                            "title": self._get_article_title(result.raw_news_id)
                        })
                        self.logger.info(
                            f"Published article to WeChat: {result.id}"
                        )
                    else:
                        failed_count += 1
                        self.logger.warning(
                            f"Failed to publish article {result.id}: {result.publish_error}"
                        )

                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"Error publishing article: {e}")

            # Get statistics
            stats = self.publishing_service.get_publishing_stats()

            self.logger.info(
                f"WeChat publishing workflow completed: "
                f"{published_count} published, {failed_count} failed"
            )

            return {
                "success": True,
                "published_count": published_count,
                "failed_count": failed_count,
                "articles": published_articles,
                "stats": stats
            }

        except Exception as e:
            self.logger.error(f"WeChat publishing workflow failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_article_title(self, raw_news_id: int) -> str:
        """Get article title from raw news ID.

        Args:
            raw_news_id: ID of raw news

        Returns:
            Article title
        """
        try:
            raw_news = self.db_session.query(RawNews).filter(
                RawNews.id == raw_news_id
            ).first()

            if raw_news:
                return raw_news.title
        except Exception:
            pass

        return "Unknown"

    def get_statistics(self) -> Dict[str, Any]:
        """Get current publishing statistics.

        Returns:
            Dictionary with publishing statistics
        """
        stats = self.publishing_service.get_publishing_stats()
        return {
            "total": stats["total"],
            "published": stats["published"],
            "scheduled": stats["scheduled"],
            "failed": stats["failed"],
            "publish_rate": stats["publish_rate"]
        }

    def get_published_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently published articles.

        Args:
            limit: Maximum number of articles to return

        Returns:
            List of published articles with metadata
        """
        published = self.db_session.query(PublishedContent).filter(
            PublishedContent.publish_status == "published"
        ).order_by(PublishedContent.published_at.desc()).limit(limit).all()

        articles = []
        for pub in published:
            raw_news = self.db_session.query(RawNews).filter(
                RawNews.id == pub.raw_news_id
            ).first()

            if raw_news:
                articles.append({
                    "id": pub.id,
                    "title": raw_news.title,
                    "url": pub.wechat_url,
                    "published_at": pub.published_at
                })

        return articles
