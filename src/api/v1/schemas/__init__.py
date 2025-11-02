"""API v1 schemas module."""

from src.api.v1.schemas.news import (
    NewsItemBase,
    RawNewsCreate,
    RawNewsResponse,
    ProcessedNewsResponse,
    NewsItemDetailResponse,
    NewsListResponse,
    CollectionStatsResponse,
)
from src.api.v1.schemas.processed_news import (
    ProcessingResponse,
    ProcessingRequest,
    BatchProcessingRequest,
)

__all__ = [
    "NewsItemBase",
    "RawNewsCreate",
    "RawNewsResponse",
    "ProcessedNewsResponse",
    "NewsItemDetailResponse",
    "NewsListResponse",
    "CollectionStatsResponse",
    "ProcessingResponse",
    "ProcessingRequest",
    "BatchProcessingRequest",
]
