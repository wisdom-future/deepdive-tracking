"""ContentStats model for content statistics."""

from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    JSON,
    CheckConstraint,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from src.models.base import Base, BaseModel


class ContentStats(BaseModel, Base):
    """内容统计表."""

    __tablename__ = "content_stats"

    published_content_id: Mapped[int] = mapped_column(
        ForeignKey("published_content.id"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(50), nullable=False)

    # Read data
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_viewers: Mapped[int] = mapped_column(Integer, default=0)
    read_count: Mapped[int] = mapped_column(Integer, default=0)
    completion_rate: Mapped[Optional[float]] = mapped_column(Float)
    avg_read_time: Mapped[Optional[int]] = mapped_column(Integer)

    # Interaction data
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    collection_count: Mapped[int] = mapped_column(Integer, default=0)

    # Deep metrics
    click_through_rate: Mapped[Optional[float]] = mapped_column(Float)
    social_share_rate: Mapped[Optional[float]] = mapped_column(Float)

    # User feedback
    nps_score: Mapped[Optional[int]] = mapped_column(Integer)
    nps_feedback_count: Mapped[int] = mapped_column(Integer, default=0)
    average_rating: Mapped[Optional[float]] = mapped_column(Float)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)

    # Traffic source
    referrer_stats: Mapped[Optional[dict]] = mapped_column(JSON)

    # Time series
    last_activity_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    published_content = relationship("PublishedContent", back_populates="content_stats")

    __table_args__ = (
        CheckConstraint(
            "channel IN ('wechat', 'xiaohongshu', 'web', 'email')",
            name="valid_channel",
        ),
    )
