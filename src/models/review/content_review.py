"""ContentReview model for content review and editing."""

from sqlalchemy import (
    String,
    Integer,
    Float,
    Text,
    DateTime,
    Boolean,
    JSON,
    CheckConstraint,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from src.models.base import Base, BaseModel


class ContentReview(BaseModel, Base):
    """内容审核和编辑表."""

    __tablename__ = "content_review"

    processed_news_id: Mapped[int] = mapped_column(
        ForeignKey("processed_news.id"), unique=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="pending")
    review_notes: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255))
    reviewed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    review_decision: Mapped[Optional[str]] = mapped_column(String(50))

    # Editing changes
    title_edited: Mapped[Optional[str]] = mapped_column(String(512))
    summary_pro_edited: Mapped[Optional[str]] = mapped_column(Text)
    summary_sci_edited: Mapped[Optional[str]] = mapped_column(Text)
    keywords_edited: Mapped[Optional[List[str]]] = mapped_column(JSON)
    category_edited: Mapped[Optional[str]] = mapped_column(String(50))

    editor_notes: Mapped[Optional[str]] = mapped_column(Text)
    edited_by: Mapped[Optional[str]] = mapped_column(String(255))
    edited_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    # Change history
    change_log: Mapped[Optional[dict]] = mapped_column(JSON)

    # Review rule checks
    checked_sensitive_words: Mapped[bool] = mapped_column(Boolean, default=False)
    has_sensitive_words: Mapped[bool] = mapped_column(Boolean, default=False)
    sensitive_words_detail: Mapped[Optional[str]] = mapped_column(Text)

    checked_copyright: Mapped[bool] = mapped_column(Boolean, default=False)
    copyright_issues: Mapped[Optional[str]] = mapped_column(Text)

    checked_technical_accuracy: Mapped[bool] = mapped_column(Boolean, default=False)
    technical_accuracy_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Reviewer feedback
    reviewer_confidence: Mapped[Optional[float]] = mapped_column(Float)
    reviewer_tags: Mapped[Optional[List[str]]] = mapped_column(JSON)

    # Process info
    send_back_count: Mapped[int] = mapped_column(Integer, default=0)
    final_decision_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    processed_news = relationship("ProcessedNews", back_populates="content_review")
    published_content = relationship("PublishedContent", back_populates="content_review")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'needs_edit', 'in_review')",
            name="valid_review_status",
        ),
    )
