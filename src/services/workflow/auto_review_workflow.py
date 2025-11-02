"""Auto-review workflow orchestration service."""

import logging
from typing import Tuple, Dict, Any
from sqlalchemy.orm import Session

from src.services.review_service import ReviewService
from src.models import ContentReview, ProcessedNews

logger = logging.getLogger(__name__)


class AutoReviewWorkflow:
    """Orchestrates the automatic review workflow."""

    def __init__(self, db_session: Session):
        """Initialize auto-review workflow.

        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db_session = db_session
        self.review_service = ReviewService(db_session)
        self.logger = logger

    def execute(
        self,
        score_threshold: int = 50,
        max_reviews: int = 100
    ) -> Dict[str, Any]:
        """Execute the auto-review workflow.

        Workflow steps:
        1. Get pending reviews
        2. Auto-approve high-scoring articles
        3. Generate statistics

        Args:
            score_threshold: Minimum score to auto-approve (0-100)
            max_reviews: Maximum reviews to process

        Returns:
            Dictionary with workflow results:
            {
                "success": bool,
                "approved_count": int,
                "skipped_count": int,
                "stats": dict,
                "error": str (if failed)
            }
        """
        try:
            self.logger.info(
                f"Starting auto-review workflow (threshold: {score_threshold}, max: {max_reviews})"
            )

            # Execute auto-approval
            approved_count, skipped_count = self.review_service.auto_approve_reviews(
                score_threshold=score_threshold,
                max_reviews=max_reviews
            )

            # Get statistics
            stats = self.review_service.get_review_stats()

            self.logger.info(
                f"Auto-review workflow completed: "
                f"{approved_count} approved, {skipped_count} skipped"
            )

            return {
                "success": True,
                "approved_count": approved_count,
                "skipped_count": skipped_count,
                "total_processed": approved_count + skipped_count,
                "stats": stats
            }

        except Exception as e:
            self.logger.error(f"Auto-review workflow failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get current review statistics.

        Returns:
            Dictionary with review statistics
        """
        stats = self.review_service.get_review_stats()
        return {
            "total": stats["total"],
            "pending": stats["pending"],
            "approved": stats["approved"],
            "rejected": stats["rejected"],
            "auto_approved": stats["auto_approved"],
            "approval_rate": stats["approval_rate"]
        }

    def get_pending_articles(self, limit: int = 100) -> list:
        """Get articles pending auto-review.

        Args:
            limit: Maximum number of articles to return

        Returns:
            List of pending reviews
        """
        return self.review_service.get_pending_reviews(limit=limit)
