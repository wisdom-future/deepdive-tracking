"""PublishedContent model for published content."""

from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    JSON,
    CheckConstraint,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from src.models.base import Base, BaseModel


class PublishedContent(BaseModel, Base):
    """已发布内容表."""

    __tablename__ = "published_content"

    processed_news_id: Mapped[int] = mapped_column(
        ForeignKey("processed_news.id"), nullable=False
    )
    content_review_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("content_review.id")
    )
    raw_news_id: Mapped[int] = mapped_column(ForeignKey("raw_news.id"), nullable=False)

    # Publish status
    publish_status: Mapped[str] = mapped_column(String(50), default="draft")

    # Publish channels
    channels: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=[])

    # Final content
    final_title: Mapped[Optional[str]] = mapped_column(String(512))
    final_summary_pro: Mapped[Optional[str]] = mapped_column(Text)
    final_summary_sci: Mapped[Optional[str]] = mapped_column(Text)
    final_keywords: Mapped[Optional[List[str]]] = mapped_column(JSON)

    # Publish time
    scheduled_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    # Channel-specific URLs
    wechat_msg_id: Mapped[Optional[str]] = mapped_column(String(255))
    wechat_url: Mapped[Optional[str]] = mapped_column(String(2048))
    xiaohongshu_post_id: Mapped[Optional[str]] = mapped_column(String(255))
    xiaohongshu_url: Mapped[Optional[str]] = mapped_column(String(2048))
    web_url: Mapped[Optional[str]] = mapped_column(String(2048))

    # Version info
    content_version: Mapped[int] = mapped_column(Integer, default=1)

    # Publishing info
    published_by: Mapped[Optional[str]] = mapped_column(String(255))
    publish_error: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_retry_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    # Generated media
    featured_image_url: Mapped[Optional[str]] = mapped_column(String(2048))
    images: Mapped[Optional[dict]] = mapped_column(JSON)

    # Relationships
    processed_news = relationship("ProcessedNews", back_populates="published_content")
    content_review = relationship("ContentReview", back_populates="published_content")
    raw_news = relationship("RawNews", viewonly=True, overlaps="published_content")
    content_stats = relationship("ContentStats", back_populates="published_content")

    __table_args__ = (
        CheckConstraint(
            "publish_status IN ('draft', 'scheduled', 'published', 'archived', 'failed')",
            name="valid_publish_status",
        ),
    )
