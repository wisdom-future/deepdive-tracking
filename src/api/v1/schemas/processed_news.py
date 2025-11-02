"""Schemas for processed news API."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ProcessedNewsResponse(BaseModel):
    """Response model for processed news."""

    id: int = Field(description="Record ID")
    raw_news_id: int = Field(description="Related raw news ID")
    score: float = Field(description="News importance score (0-100)")
    score_breakdown: Optional[Dict[str, str]] = Field(
        default=None,
        description="Score breakdown details"
    )
    category: str = Field(description="News category")
    sub_categories: Optional[List[str]] = Field(
        default=None,
        description="Sub-categories"
    )
    confidence: Optional[float] = Field(
        description="Classification confidence (0-1)"
    )
    summary_pro: str = Field(description="Professional summary")
    summary_sci: str = Field(description="Scientific summary for general audience")
    keywords: Optional[List[str]] = Field(description="Extracted keywords")
    quality_score: Optional[float] = Field(description="Quality score of processing")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "raw_news_id": 1,
                "score": 85,
                "category": "tech_breakthrough",
                "confidence": 0.95,
                "summary_pro": "OpenAI发布GPT-4o模型，具有多模态理解能力...",
                "summary_sci": "OpenAI推出一个新的AI模型，可以理解文字、语音和图像...",
                "keywords": ["GPT-4o", "OpenAI", "AI", "多模态"],
            }
        }


class ProcessingRequest(BaseModel):
    """Request to process news articles."""

    force: bool = Field(
        default=False,
        description="Force reprocessing even if already processed"
    )


class BatchProcessingRequest(BaseModel):
    """Request to batch process news."""

    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of articles to process"
    )
    skip_errors: bool = Field(
        default=True,
        description="Skip articles that fail processing"
    )


class ProcessingResponse(BaseModel):
    """Response from processing request."""

    processed_count: int = Field(description="Number of successfully processed articles")
    failed_count: int = Field(description="Number of failed articles")
    total_cost: float = Field(description="Total API cost in USD")
    avg_processing_time_ms: Optional[float] = Field(
        description="Average processing time per article"
    )
    errors: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of errors (if any failed)"
    )


class ProcessedNewsQuery(BaseModel):
    """Query parameters for processed news."""

    skip: int = Field(default=0, ge=0, description="Pagination offset")
    limit: int = Field(default=10, ge=1, le=100, description="Pagination limit")
    category: Optional[str] = Field(None, description="Filter by category")
    min_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum score")
    max_score: Optional[float] = Field(None, ge=0, le=100, description="Maximum score")
    min_confidence: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Minimum confidence score"
    )
    keyword: Optional[str] = Field(None, description="Search by keyword")
    sort_by: str = Field(
        default="created_at",
        description="Sort field: score, created_at, confidence"
    )
    sort_order: str = Field(
        default="desc",
        description="Sort order: asc or desc"
    )
