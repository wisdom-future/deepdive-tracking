"""Schemas for news-related API endpoints."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class NewsItemBase(BaseModel):
    """Base schema for news items."""

    title: str = Field(..., description="News title", min_length=1, max_length=512)
    url: str = Field(..., description="Source URL", max_length=2048)
    content: Optional[str] = Field(None, description="Article content")
    language: str = Field("en", description="Content language (en, zh, etc.)")


class RawNewsCreate(NewsItemBase):
    """Schema for creating raw news."""

    source_id: int = Field(..., description="Data source ID")
    author: Optional[str] = Field(None, description="Author name")
    published_at: datetime = Field(..., description="Publication datetime")


class RawNewsResponse(NewsItemBase):
    """Schema for raw news response."""

    id: int = Field(..., description="News ID")
    source_id: int = Field(..., description="Data source ID")
    hash: str = Field(..., description="Content hash for deduplication")
    status: str = Field(..., description="Processing status")
    is_duplicate: bool = Field(False, description="Is duplicate")
    is_spam: bool = Field(False, description="Is spam")
    quality_score: Optional[float] = Field(None, description="Quality score (0-100)")
    author: Optional[str] = Field(None, description="Author name")
    source_name: Optional[str] = Field(None, description="Source name")
    published_at: datetime = Field(..., description="Publication datetime")
    fetched_at: datetime = Field(..., description="Fetch datetime")
    created_at: datetime = Field(..., description="Created datetime")
    updated_at: datetime = Field(..., description="Updated datetime")

    class Config:
        from_attributes = True


class ProcessedNewsResponse(BaseModel):
    """Schema for processed news response."""

    id: int = Field(..., description="Processed news ID")
    raw_news_id: int = Field(..., description="Raw news ID")
    score: float = Field(..., description="AI score (0-100)")
    category: str = Field(..., description="Content category")
    confidence: Optional[float] = Field(None, description="Classification confidence")
    summary_pro: str = Field(..., description="Professional summary")
    summary_sci: str = Field(..., description="Scientific summary")
    keywords: List[str] = Field(default=[], description="Keywords")
    sentiment: Optional[str] = Field(None, description="Sentiment analysis")
    version: int = Field(1, description="Version number")
    created_at: datetime = Field(..., description="Created datetime")

    class Config:
        from_attributes = True


class NewsItemDetailResponse(BaseModel):
    """Schema for detailed news item with all related data."""

    raw_news: RawNewsResponse = Field(..., description="Raw news data")
    processed_news: Optional[ProcessedNewsResponse] = Field(None, description="Processed news data")


class NewsListResponse(BaseModel):
    """Schema for news list response with pagination."""

    total: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    page_size: int = Field(20, description="Page size")
    items: List[RawNewsResponse] = Field(default=[], description="News items")


class CollectionStatsResponse(BaseModel):
    """Schema for collection statistics."""

    total_collected: int = Field(..., description="Total items collected")
    total_new: int = Field(..., description="Total new items")
    total_duplicates: int = Field(..., description="Total duplicate items")
    errors: List[str] = Field(default=[], description="Collection errors")
    by_source: dict = Field(default={}, description="Stats by source")
