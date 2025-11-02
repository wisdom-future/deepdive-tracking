"""News management API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.api.v1.dependencies import get_db
from src.api.v1.schemas.news import (
    RawNewsResponse,
    NewsListResponse,
    NewsItemDetailResponse,
    ProcessedNewsResponse,
)
from src.models import RawNews, ProcessedNews

router = APIRouter(prefix="/api/v1/news", tags=["news"])


@router.get(
    "/items",
    response_model=NewsListResponse,
    summary="Get news items with pagination",
    description="Retrieve raw news items with optional filtering and pagination",
)
async def get_news_items(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    language: Optional[str] = Query(None, description="Filter by language"),
) -> NewsListResponse:
    """Get paginated list of news items.

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - status_filter: Filter by processing status (raw, processing, processed, failed, duplicate)
    - language: Filter by language (en, zh, etc.)

    Returns:
        NewsListResponse with paginated items and total count
    """
    query = db.query(RawNews)

    # Apply filters
    if status_filter:
        query = query.filter(RawNews.status == status_filter)
    if language:
        query = query.filter(RawNews.language == language)

    # Get total count
    total = query.count()

    # Apply pagination
    items = (
        query.order_by(desc(RawNews.published_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return NewsListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[RawNewsResponse.model_validate(item) for item in items],
    )


@router.get(
    "/items/{item_id}",
    response_model=NewsItemDetailResponse,
    summary="Get detailed news item",
    description="Retrieve a single news item with all related data (raw + processed)",
)
async def get_news_item_detail(
    item_id: int,
    db: Session = Depends(get_db),
) -> NewsItemDetailResponse:
    """Get detailed information for a single news item.

    Path Parameters:
    - item_id: ID of the news item

    Returns:
        NewsItemDetailResponse with raw and processed news data

    Raises:
        HTTPException: 404 if news item not found
    """
    raw_news = db.query(RawNews).filter(RawNews.id == item_id).first()

    if not raw_news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News item {item_id} not found",
        )

    # Get processed news if exists
    processed_news = db.query(ProcessedNews).filter(ProcessedNews.raw_news_id == item_id).first()

    return NewsItemDetailResponse(
        raw_news=RawNewsResponse.model_validate(raw_news),
        processed_news=ProcessedNewsResponse.model_validate(processed_news) if processed_news else None,
    )


@router.get(
    "/unprocessed",
    response_model=NewsListResponse,
    summary="Get unprocessed news items",
    description="Get news items waiting for AI processing",
)
async def get_unprocessed_news(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> NewsListResponse:
    """Get news items with 'raw' status that need processing.

    Returns:
        NewsListResponse with unprocessed items
    """
    query = db.query(RawNews).filter(RawNews.status == "raw")

    total = query.count()
    items = (
        query.order_by(RawNews.published_at)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return NewsListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[RawNewsResponse.model_validate(item) for item in items],
    )


@router.get(
    "/by-source/{source_id}",
    response_model=NewsListResponse,
    summary="Get news by source",
    description="Retrieve news items from a specific source",
)
async def get_news_by_source(
    source_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> NewsListResponse:
    """Get news items from a specific data source.

    Path Parameters:
    - source_id: ID of the data source

    Returns:
        NewsListResponse with items from that source
    """
    query = db.query(RawNews).filter(RawNews.source_id == source_id)

    total = query.count()
    items = (
        query.order_by(desc(RawNews.published_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return NewsListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[RawNewsResponse.model_validate(item) for item in items],
    )
