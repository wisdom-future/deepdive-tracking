"""DataSource model for managing news sources."""

from sqlalchemy import String, Integer, Boolean, DateTime, JSON, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from src.models.base import Base, BaseModel


class DataSource(BaseModel, Base):
    """Information source configuration."""

    __tablename__ = "data_sources"

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Access config
    url: Mapped[Optional[str]] = mapped_column(String(2048))
    method: Mapped[str] = mapped_column(String(10), default="GET")
    headers: Mapped[dict] = mapped_column(JSON, default={})
    params: Mapped[dict] = mapped_column(JSON, default={})
    auth_type: Mapped[Optional[str]] = mapped_column(String(50))
    auth_token: Mapped[Optional[str]] = mapped_column(String(1024))

    # Parser config (for crawlers)
    css_selectors: Mapped[Optional[dict]] = mapped_column(JSON)
    xpath_patterns: Mapped[Optional[dict]] = mapped_column(JSON)

    # Running strategy
    priority: Mapped[int] = mapped_column(Integer, default=5)
    refresh_interval: Mapped[int] = mapped_column(Integer, default=30)  # minutes
    max_items_per_run: Mapped[int] = mapped_column(Integer, default=50)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Status tracking
    last_check_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)

    # Capabilities
    supports_pagination: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_filter: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=[])

    # Metadata defaults
    default_author: Mapped[Optional[str]] = mapped_column(String(255))

    # Meta
    created_by: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    raw_news = relationship("RawNews", back_populates="data_source")

    __table_args__ = (
        CheckConstraint(
            "type IN ('rss', 'crawler', 'api', 'twitter', 'email')",
            name="valid_source_type",
        ),
        CheckConstraint("priority BETWEEN 1 AND 10", name="valid_priority"),
    )
