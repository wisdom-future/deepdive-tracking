"""OperationLog model for operation audit logging."""

from sqlalchemy import String, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from src.models.base import Base, BaseModel


class OperationLog(BaseModel, Base):
    """操作审计日志表."""

    __tablename__ = "operation_logs"

    # Operation info
    operation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[int]] = mapped_column(Integer)

    # Operator info
    operator_id: Mapped[Optional[str]] = mapped_column(String(255))
    operator_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Action details
    action_detail: Mapped[Optional[str]] = mapped_column(Text)
    old_values: Mapped[Optional[dict]] = mapped_column(JSON)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON)

    # IP and environment
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    # Result
    status: Mapped[Optional[str]] = mapped_column(String(50))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
