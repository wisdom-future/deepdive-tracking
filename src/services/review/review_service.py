"""Review service for content review and approval."""

import logging
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from src.models import ContentReview, ProcessedNews, RawNews

logger = logging.getLogger(__name__)


class ReviewService:
    """Service for managing content review and editorial decisions."""

    def __init__(self, db_session: Session):
        """Initialize review service.

        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db_session = db_session
        self.logger = logger

    def create_review(self, processed_news_id: int) -> ContentReview:
        """Create a new content review record.

        Args:
            processed_news_id: ID of the processed news to review

        Returns:
            ContentReview record

        Raises:
            ValueError: If processed news not found or already reviewed
        """
        # Check if processed news exists
        processed_news = self.db_session.query(ProcessedNews).filter(
            ProcessedNews.id == processed_news_id
        ).first()

        if not processed_news:
            raise ValueError(f"Processed news {processed_news_id} not found")

        # Check if already reviewed
        existing_review = self.db_session.query(ContentReview).filter(
            ContentReview.processed_news_id == processed_news_id
        ).first()

        if existing_review:
            return existing_review

        # Create new review
        review = ContentReview(
            processed_news_id=processed_news_id,
            status="pending"
        )

        self.db_session.add(review)
        self.db_session.commit()

        self.logger.info(f"Created review for processed_news {processed_news_id}")
        return review

    def get_pending_reviews(self, limit: int = 100) -> List[ContentReview]:
        """Get pending content reviews.

        Args:
            limit: Maximum number of reviews to return

        Returns:
            List of pending ContentReview records
        """
        reviews = self.db_session.query(ContentReview).filter(
            ContentReview.status.in_(["pending", "needs_edit"])
        ).order_by(ContentReview.created_at).limit(limit).all()

        return reviews

    def approve_review(
        self,
        review_id: int,
        reviewer_name: str = "system",
        reviewer_confidence: Optional[float] = None,
        reviewer_tags: Optional[List[str]] = None
    ) -> ContentReview:
        """Approve a content review.

        Args:
            review_id: ID of the review
            reviewer_name: Name of the reviewer
            reviewer_confidence: Confidence score (0-1)
            reviewer_tags: Tags added by reviewer

        Returns:
            Updated ContentReview

        Raises:
            ValueError: If review not found
        """
        review = self.db_session.query(ContentReview).filter(
            ContentReview.id == review_id
        ).first()

        if not review:
            raise ValueError(f"Review {review_id} not found")

        review.status = "approved"
        review.review_decision = "approved"
        review.reviewed_by = reviewer_name
        review.reviewed_at = datetime.utcnow()
        review.reviewer_confidence = reviewer_confidence or 0.95
        review.reviewer_tags = reviewer_tags or []

        self.db_session.commit()

        self.logger.info(f"Approved review {review_id}")
        return review

    def reject_review(
        self,
        review_id: int,
        reviewer_name: str = "system",
        review_notes: str = "",
        reason: str = "quality"
    ) -> ContentReview:
        """Reject a content review.

        Args:
            review_id: ID of the review
            reviewer_name: Name of the reviewer
            review_notes: Notes about rejection
            reason: Reason for rejection

        Returns:
            Updated ContentReview

        Raises:
            ValueError: If review not found
        """
        review = self.db_session.query(ContentReview).filter(
            ContentReview.id == review_id
        ).first()

        if not review:
            raise ValueError(f"Review {review_id} not found")

        review.status = "rejected"
        review.review_decision = "rejected"
        review.reviewed_by = reviewer_name
        review.reviewed_at = datetime.utcnow()
        review.review_notes = review_notes
        review.reviewer_tags = [reason]

        self.db_session.commit()

        self.logger.info(f"Rejected review {review_id}: {reason}")
        return review

    def request_edit(
        self,
        review_id: int,
        editor_notes: str,
        editor_name: str = "system"
    ) -> ContentReview:
        """Request edits for content.

        Args:
            review_id: ID of the review
            editor_notes: Notes about requested edits
            editor_name: Name of the editor

        Returns:
            Updated ContentReview

        Raises:
            ValueError: If review not found
        """
        review = self.db_session.query(ContentReview).filter(
            ContentReview.id == review_id
        ).first()

        if not review:
            raise ValueError(f"Review {review_id} not found")

        review.status = "needs_edit"
        review.editor_notes = editor_notes
        review.edited_by = editor_name
        review.send_back_count = (review.send_back_count or 0) + 1

        self.db_session.commit()

        self.logger.info(f"Requested edits for review {review_id}")
        return review

    def submit_edits(
        self,
        review_id: int,
        title_edited: Optional[str] = None,
        summary_pro_edited: Optional[str] = None,
        summary_sci_edited: Optional[str] = None,
        keywords_edited: Optional[List[str]] = None,
        category_edited: Optional[str] = None,
        editor_name: str = "system"
    ) -> ContentReview:
        """Submit edited content.

        Args:
            review_id: ID of the review
            title_edited: Edited title
            summary_pro_edited: Edited professional summary
            summary_sci_edited: Edited scientific summary
            keywords_edited: Edited keywords
            category_edited: Edited category
            editor_name: Name of the editor

        Returns:
            Updated ContentReview

        Raises:
            ValueError: If review not found
        """
        review = self.db_session.query(ContentReview).filter(
            ContentReview.id == review_id
        ).first()

        if not review:
            raise ValueError(f"Review {review_id} not found")

        # Store edits
        if title_edited:
            review.title_edited = title_edited
        if summary_pro_edited:
            review.summary_pro_edited = summary_pro_edited
        if summary_sci_edited:
            review.summary_sci_edited = summary_sci_edited
        if keywords_edited:
            review.keywords_edited = keywords_edited
        if category_edited:
            review.category_edited = category_edited

        review.edited_by = editor_name
        review.edited_at = datetime.utcnow()
        review.status = "in_review"

        self.db_session.commit()

        self.logger.info(f"Submitted edits for review {review_id}")
        return review

    def auto_approve_reviews(
        self,
        score_threshold: int = 50,
        max_reviews: int = 100
    ) -> Tuple[int, int]:
        """Automatically approve reviews based on score threshold.

        This method implements automatic review workflow:
        - Reviews pending articles
        - Approves articles with score >= score_threshold
        - Marks as auto-approved by system

        Args:
            score_threshold: Minimum score to auto-approve (0-100)
            max_reviews: Maximum number of reviews to process in one batch

        Returns:
            Tuple of (approved_count, skipped_count)
        """
        # Get pending reviews
        pending_reviews = self.db_session.query(ContentReview).filter(
            ContentReview.status.in_(["pending", "needs_edit"])
        ).limit(max_reviews).all()

        approved_count = 0
        skipped_count = 0

        for review in pending_reviews:
            try:
                # Get the associated processed news to check score
                processed_news = self.db_session.query(ProcessedNews).filter(
                    ProcessedNews.id == review.processed_news_id
                ).first()

                if not processed_news:
                    self.logger.warning(
                        f"Processed news {review.processed_news_id} not found for review {review.id}"
                    )
                    skipped_count += 1
                    continue

                # Check if score meets threshold
                if processed_news.score is not None and processed_news.score >= score_threshold:
                    # Auto-approve high-scoring articles
                    review.status = "approved"
                    review.review_decision = "approved"
                    review.reviewed_by = "system_auto"
                    review.reviewed_at = datetime.utcnow()
                    review.reviewer_confidence = 0.85  # Auto-approve confidence
                    review.reviewer_tags = ["auto_approved", f"score_{processed_news.score}"]

                    self.db_session.commit()
                    approved_count += 1

                    self.logger.info(
                        f"Auto-approved review {review.id} for processed_news {review.processed_news_id} "
                        f"(score: {processed_news.score})"
                    )
                else:
                    skipped_count += 1
                    self.logger.debug(
                        f"Skipped auto-approval for review {review.id} "
                        f"(score: {processed_news.score}, threshold: {score_threshold})"
                    )

            except Exception as e:
                self.logger.error(
                    f"Error auto-approving review {review.id}: {str(e)}"
                )
                skipped_count += 1

        self.logger.info(
            f"Auto-review complete: {approved_count} approved, {skipped_count} skipped"
        )
        return approved_count, skipped_count

    def auto_approve_by_processed_news_id(
        self,
        processed_news_id: int,
        score_threshold: int = 50
    ) -> ContentReview:
        """Auto-approve a specific processed news item if it meets score threshold.

        Args:
            processed_news_id: ID of the processed news
            score_threshold: Minimum score to auto-approve

        Returns:
            Updated ContentReview

        Raises:
            ValueError: If processed news or review not found
        """
        # Get or create review
        review = self.db_session.query(ContentReview).filter(
            ContentReview.processed_news_id == processed_news_id
        ).first()

        if not review:
            # Create new review if it doesn't exist
            review = self.create_review(processed_news_id)

        # Get processed news to check score
        processed_news = self.db_session.query(ProcessedNews).filter(
            ProcessedNews.id == processed_news_id
        ).first()

        if not processed_news:
            raise ValueError(f"Processed news {processed_news_id} not found")

        # Auto-approve if score meets threshold
        if processed_news.score is not None and processed_news.score >= score_threshold:
            review.status = "approved"
            review.review_decision = "approved"
            review.reviewed_by = "system_auto"
            review.reviewed_at = datetime.utcnow()
            review.reviewer_confidence = 0.85
            review.reviewer_tags = ["auto_approved", f"score_{processed_news.score}"]

            self.db_session.commit()

            self.logger.info(
                f"Auto-approved review {review.id} for processed_news {processed_news_id} "
                f"(score: {processed_news.score})"
            )
        else:
            self.logger.debug(
                f"Could not auto-approve review {review.id}: "
                f"score {processed_news.score} below threshold {score_threshold}"
            )

        return review

    def get_review_stats(self) -> dict:
        """Get review statistics.

        Returns:
            Dictionary with review statistics
        """
        total = self.db_session.query(ContentReview).count()
        pending = self.db_session.query(ContentReview).filter(
            ContentReview.status.in_(["pending", "needs_edit"])
        ).count()
        approved = self.db_session.query(ContentReview).filter(
            ContentReview.status == "approved"
        ).count()
        rejected = self.db_session.query(ContentReview).filter(
            ContentReview.status == "rejected"
        ).count()
        auto_approved = self.db_session.query(ContentReview).filter(
            ContentReview.reviewed_by == "system_auto"
        ).count()

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "auto_approved": auto_approved,
            "approval_rate": approved / total * 100 if total > 0 else 0
        }
