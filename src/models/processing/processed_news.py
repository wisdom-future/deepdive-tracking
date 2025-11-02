"""ProcessedNews model for AI-processed news."""

from sqlalchemy import (
    String,
    Integer,
    Float,
    Text,
    DateTime,
    JSON,
    CheckConstraint,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from src.models.base import Base, BaseModel


class ProcessedNews(BaseModel, Base):
    """AI处理结果表."""

    __tablename__ = "processed_news"

    raw_news_id: Mapped[int] = mapped_column(
        ForeignKey("raw_news.id"), unique=True, nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    score_breakdown: Mapped[Optional[dict]] = mapped_column(JSON)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    sub_categories: Mapped[Optional[List[str]]] = mapped_column(JSON, default=[])
    confidence: Mapped[Optional[float]] = mapped_column(Float)

    # Content generation
    summary_pro: Mapped[str] = mapped_column(Text, nullable=False)
    summary_sci: Mapped[str] = mapped_column(Text, nullable=False)

    # Key information
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSON, default=[])
    entities: Mapped[Optional[dict]] = mapped_column(JSON)

    # Technical related
    tech_terms: Mapped[Optional[dict]] = mapped_column(JSON)
    infrastructure_tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=[])
    company_mentions: Mapped[Optional[List[str]]] = mapped_column(JSON, default=[])

    # Analysis metadata
    readability_score: Mapped[Optional[float]] = mapped_column(Float)
    sentiment: Mapped[Optional[str]] = mapped_column(String(50))
    word_count: Mapped[Optional[int]] = mapped_column(Integer)

    # AI processing info
    ai_models_used: Mapped[Optional[List[str]]] = mapped_column(JSON, default=[])
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    cost: Mapped[Optional[float]] = mapped_column(Float)
    cost_breakdown: Mapped[Optional[dict]] = mapped_column(JSON)

    # Version control
    version: Mapped[int] = mapped_column(Integer, default=1)
    previous_id: Mapped[Optional[int]] = mapped_column(ForeignKey("processed_news.id"))

    # Quality metrics
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    quality_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    raw_news = relationship("RawNews", back_populates="processed_news", uselist=False)
    content_review = relationship("ContentReview", back_populates="processed_news", uselist=False)
    published_content = relationship("PublishedContent", back_populates="processed_news")
    cost_logs = relationship("CostLog", back_populates="processed_news")

    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 100", name="valid_processed_score"),
        CheckConstraint(
            "category IN ("
            "'company_news', 'tech_breakthrough', 'applications', "
            "'infrastructure', 'policy', 'market_trends', "
            "'expert_opinions', 'learning_resources')",
            name="valid_category",
        ),
    )
