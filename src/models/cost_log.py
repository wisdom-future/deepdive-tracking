"""CostLog model for cost tracking."""

from sqlalchemy import (
    String,
    Integer,
    Float,
    Text,
    JSON,
    CheckConstraint,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from src.models.base import Base, BaseModel


class CostLog(BaseModel, Base):
    """成本追踪表."""

    __tablename__ = "cost_logs"

    # Associations
    processed_news_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("processed_news.id")
    )
    publishing_schedule_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("publishing_schedules.id")
    )

    # Cost info
    service: Mapped[str] = mapped_column(String(100), nullable=False)
    operation: Mapped[str] = mapped_column(String(100), nullable=False)

    # Usage and cost
    usage_units: Mapped[Optional[int]] = mapped_column(Integer)
    unit_price: Mapped[Optional[float]] = mapped_column(Float)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)

    # Details
    request_id: Mapped[Optional[str]] = mapped_column(String(255))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON)

    # Relationships
    processed_news = relationship("ProcessedNews", back_populates="cost_logs")
    publishing_schedule = relationship("PublishingSchedule", back_populates="cost_logs")

    __table_args__ = (
        CheckConstraint("total_cost >= 0", name="positive_cost"),
    )
