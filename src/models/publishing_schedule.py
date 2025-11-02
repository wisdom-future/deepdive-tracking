"""PublishingSchedule model for publishing schedules."""

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Text,
    DateTime,
    JSON,
    CheckConstraint,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from src.models.base import Base, BaseModel


class PublishingSchedule(BaseModel, Base):
    """定时发布任务管理表."""

    __tablename__ = "publishing_schedules"

    # Publishing plan
    schedule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_ids: Mapped[List[int]] = mapped_column(JSON, nullable=False)

    # Plan time
    scheduled_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    execution_window_start: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True)
    )
    execution_window_end: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Execution info
    status: Mapped[str] = mapped_column(String(50), default="pending")
    executed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    # Publishing channels
    target_channels: Mapped[List[str]] = mapped_column(JSON, nullable=False)

    # Template and config
    template_id: Mapped[Optional[int]] = mapped_column(Integer)
    template_variables: Mapped[Optional[dict]] = mapped_column(JSON)

    # Execution result
    result: Mapped[Optional[dict]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON)

    # Retry mechanism
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    next_retry_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    # Rollback info
    can_rollback: Mapped[bool] = mapped_column(Boolean, default=True)
    rollback_deadline: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    rolled_back: Mapped[bool] = mapped_column(Boolean, default=False)
    rollback_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    # Creator info
    created_by: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    cost_logs = relationship("CostLog", back_populates="publishing_schedule")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="valid_schedule_status",
        ),
    )
