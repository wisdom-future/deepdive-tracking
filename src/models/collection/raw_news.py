"""RawNews model for raw collected news."""

from sqlalchemy import String, Integer, Boolean, Float, Text, DateTime, LargeBinary, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from src.models.base import Base, BaseModel


class RawNews(BaseModel, Base):
    """原始新闻数据表."""

    __tablename__ = "raw_news"

    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), unique=False, nullable=False)  # Allow duplicate URLs for tracking
    content: Mapped[Optional[str]] = mapped_column(Text)
    html_content: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    language: Mapped[str] = mapped_column(String(10), default="en")
    hash: Mapped[str] = mapped_column(String(64), unique=False, nullable=False, index=True)  # Allow duplicates for tracking, keep index for performance
    author: Mapped[Optional[str]] = mapped_column(String(255))
    source_name: Mapped[Optional[str]] = mapped_column(String(255))
    published_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetched_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="raw")
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    next_retry_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_score: Mapped[Optional[Float]] = mapped_column(Float)

    # Relationships
    data_source = relationship("DataSource", back_populates="raw_news")
    processed_news = relationship("ProcessedNews", back_populates="raw_news", uselist=False)
    published_content = relationship("PublishedContent", foreign_keys="PublishedContent.raw_news_id")

    __table_args__ = (
        CheckConstraint(
            "status IN ('raw', 'processing', 'processed', 'failed', 'duplicate')",
            name="valid_raw_news_status",
        ),
    )
