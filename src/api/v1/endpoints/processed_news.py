"""API endpoints for processed news."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_

from src.api.v1.dependencies import get_db
from src.api.v1.schemas.processed_news import (
    ProcessedNewsResponse,
    ProcessingResponse,
    ProcessingRequest,
    BatchProcessingRequest,
)
from src.models import ProcessedNews, RawNews
from src.services.ai import ScoringService
from src.config.settings import Settings

router = APIRouter(prefix="/processed-news", tags=["processed_news"], include_in_schema=True)


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


@router.get("", response_model=List[ProcessedNewsResponse])
async def list_processed_news(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(10, ge=1, le=100, description="Pagination limit"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum score"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum score"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1, description="Minimum confidence"),
    keyword: Optional[str] = Query(None, description="Search by keyword"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    db: Session = Depends(get_db),
) -> List[ProcessedNewsResponse]:
    """List processed news with filtering and sorting.

    Parameters:
    - skip: Number of items to skip (pagination)
    - limit: Maximum number of items to return
    - category: Filter by news category
    - min_score: Filter by minimum score (0-100)
    - max_score: Filter by maximum score (0-100)
    - min_confidence: Filter by minimum confidence (0-1)
    - keyword: Search by keyword in summary
    - sort_by: Sort by field (score, created_at, confidence)
    - sort_order: Sort order (asc, desc)

    Returns:
    List of processed news items.
    """
    query = db.query(ProcessedNews)

    # Apply filters
    filters = []

    if category:
        filters.append(ProcessedNews.category == category)

    if min_score is not None:
        filters.append(ProcessedNews.score >= min_score)

    if max_score is not None:
        filters.append(ProcessedNews.score <= max_score)

    if min_confidence is not None:
        filters.append(ProcessedNews.confidence >= min_confidence)

    if keyword:
        filters.append(
            (ProcessedNews.summary_pro.ilike(f"%{keyword}%")) |
            (ProcessedNews.summary_sci.ilike(f"%{keyword}%"))
        )

    if filters:
        query = query.filter(and_(*filters))

    # Apply sorting
    if sort_by == "score":
        sort_column = ProcessedNews.score
    elif sort_by == "confidence":
        sort_column = ProcessedNews.confidence
    else:  # default to created_at
        sort_column = ProcessedNews.created_at

    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Apply pagination
    items = query.offset(skip).limit(limit).all()

    return [ProcessedNewsResponse.model_validate(item) for item in items]


@router.get("/{news_id}", response_model=ProcessedNewsResponse)
async def get_processed_news(
    news_id: int,
    db: Session = Depends(get_db),
) -> ProcessedNewsResponse:
    """Get a specific processed news item.

    Args:
        news_id: ID of the processed news

    Returns:
        Processed news details
    """
    item = db.query(ProcessedNews).filter(ProcessedNews.id == news_id).first()

    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Processed news {news_id} not found"
        )

    return ProcessedNewsResponse.model_validate(item)


@router.post("/{raw_news_id}/score", response_model=ProcessingResponse)
async def score_single_news(
    raw_news_id: int,
    request: ProcessingRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ProcessingResponse:
    """Score a single raw news article.

    Args:
        raw_news_id: ID of raw news to score
        request: Processing request
        db: Database session
        settings: Application settings

    Returns:
        Processing result
    """
    # Get raw news
    raw_news = db.query(RawNews).filter(RawNews.id == raw_news_id).first()

    if not raw_news:
        raise HTTPException(
            status_code=404,
            detail=f"Raw news {raw_news_id} not found"
        )

    # Check if already processed
    existing = db.query(ProcessedNews).filter(
        ProcessedNews.raw_news_id == raw_news_id
    ).first()

    if existing and not request.force:
        raise HTTPException(
            status_code=409,
            detail=f"News {raw_news_id} already processed. Use force=true to reprocess."
        )

    # Score the news
    try:
        scoring_service = ScoringService(settings, db)
        result = await scoring_service.score_news(raw_news)
        scoring_service.save_to_database(raw_news, result)

        return ProcessingResponse(
            processed_count=1,
            failed_count=0,
            total_cost=result.metadata.cost,
            avg_processing_time_ms=result.metadata.processing_time_ms,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to score news: {str(e)}"
        )


@router.post("/batch/process", response_model=ProcessingResponse)
async def batch_process_news(
    request: BatchProcessingRequest = BatchProcessingRequest(),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ProcessingResponse:
    """Batch process raw news articles.

    Args:
        request: Batch processing request
        db: Database session
        settings: Application settings

    Returns:
        Processing result with statistics
    """
    # Get unprocessed news
    unprocessed = db.query(RawNews).filter(
        RawNews.status == "raw"
    ).limit(request.limit).all()

    if not unprocessed:
        return ProcessingResponse(
            processed_count=0,
            failed_count=0,
            total_cost=0,
            avg_processing_time_ms=0,
        )

    # Process all
    try:
        scoring_service = ScoringService(settings, db)
        results, errors = await scoring_service.batch_score(
            unprocessed,
            skip_errors=request.skip_errors
        )

        # Calculate totals
        total_cost = sum(r.metadata.cost for r in results)
        avg_time = (
            sum(r.metadata.processing_time_ms for r in results) / len(results)
            if results else 0
        )

        return ProcessingResponse(
            processed_count=len(results),
            failed_count=len(errors),
            total_cost=total_cost,
            avg_processing_time_ms=avg_time,
            errors=errors if errors else None,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch processing failed: {str(e)}"
        )
