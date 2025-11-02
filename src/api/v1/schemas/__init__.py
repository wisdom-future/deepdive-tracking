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

__all__ = [
    "NewsItemBase",
    "RawNewsCreate",
    "RawNewsResponse",
    "ProcessedNewsResponse",
    "NewsItemDetailResponse",
    "NewsListResponse",
    "CollectionStatsResponse",
]
