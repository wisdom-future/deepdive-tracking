"""Association table for PublishingSchedule and PublishedContent relationship."""

from sqlalchemy import ForeignKey, Table, Column, Integer
from src.models.base import Base

# Association table for many-to-many relationship
publishing_schedule_content = Table(
    "publishing_schedule_content",
    Base.metadata,
    Column("publishing_schedule_id", Integer, ForeignKey("publishing_schedules.id"), primary_key=True),
    Column("published_content_id", Integer, ForeignKey("published_content.id"), primary_key=True),
)
