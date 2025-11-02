"""API endpoints for statistics."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.api.v1.dependencies import get_db
from src.models import RawNews, ProcessedNews, DataSource

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/")
async def get_statistics(db: Session = Depends(get_db)) -> dict:
    """Get overall statistics.

    Returns:
        Dictionary with statistics:
        - total_raw_news: Total raw news in database
        - total_processed: Total processed news
        - total_sources: Number of data sources
        - avg_score: Average score of processed news
        - processing_rate: Percentage of processed news
        - by_category: Count by category
    """
    # Get counts
    total_raw = db.query(func.count(RawNews.id)).scalar() or 0
    total_processed = db.query(func.count(ProcessedNews.id)).scalar() or 0
    total_sources = db.query(func.count(DataSource.id)).scalar() or 0

    # Get average score
    avg_score_result = db.query(func.avg(ProcessedNews.score)).scalar()
    avg_score = float(avg_score_result) if avg_score_result else None

    # Calculate processing rate
    processing_rate = (
        (total_processed / total_raw * 100) if total_raw > 0 else 0
    )

    # Get counts by category
    by_category = {}
    category_results = db.query(
        ProcessedNews.category,
        func.count(ProcessedNews.id).label("count")
    ).group_by(ProcessedNews.category).all()

    for category, count in category_results:
        by_category[category] = count

    return {
        "total_raw_news": total_raw,
        "total_processed": total_processed,
        "total_sources": total_sources,
        "avg_score": avg_score,
        "processing_rate_percent": round(processing_rate, 2),
        "by_category": by_category,
    }


@router.get("/by-category")
async def get_category_statistics(db: Session = Depends(get_db)) -> dict:
    """Get statistics grouped by category.

    Returns:
        Dictionary with category statistics:
        - category_name: {count, avg_score, min_score, max_score}
    """
    categories = db.query(ProcessedNews.category).distinct().all()
    stats = {}

    for (category,) in categories:
        category_stats = db.query(ProcessedNews).filter(
            ProcessedNews.category == category
        )

        count = category_stats.count()
        avg_score = db.query(func.avg(ProcessedNews.score)).filter(
            ProcessedNews.category == category
        ).scalar()
        min_score = db.query(func.min(ProcessedNews.score)).filter(
            ProcessedNews.category == category
        ).scalar()
        max_score = db.query(func.max(ProcessedNews.score)).filter(
            ProcessedNews.category == category
        ).scalar()

        stats[category] = {
            "count": count,
            "avg_score": float(avg_score) if avg_score else None,
            "min_score": float(min_score) if min_score else None,
            "max_score": float(max_score) if max_score else None,
        }

    return stats


@router.get("/by-source")
async def get_source_statistics(db: Session = Depends(get_db)) -> dict:
    """Get statistics grouped by data source.

    Returns:
        Dictionary with source statistics:
        - source_name: {total_collected, processed, avg_score}
    """
    sources = db.query(DataSource).all()
    stats = {}

    for source in sources:
        total_collected = db.query(func.count(RawNews.id)).filter(
            RawNews.source_id == source.id
        ).scalar() or 0

        processed = db.query(func.count(ProcessedNews.id)).join(
            RawNews
        ).filter(RawNews.source_id == source.id).scalar() or 0

        avg_score = db.query(func.avg(ProcessedNews.score)).join(
            RawNews
        ).filter(RawNews.source_id == source.id).scalar()

        stats[source.name] = {
            "total_collected": total_collected,
            "total_processed": processed,
            "avg_score": float(avg_score) if avg_score else None,
            "enabled": source.is_enabled,
            "last_check": (
                source.last_check_at.isoformat()
                if source.last_check_at else None
            ),
        }

    return stats


@router.get("/score-distribution")
async def get_score_distribution(db: Session = Depends(get_db)) -> dict:
    """Get score distribution statistics.

    Returns:
        Dictionary with score ranges and counts:
        - 90-100: High importance
        - 70-89: Medium-high importance
        - 50-69: Medium importance
        - 30-49: Low-medium importance
        - 0-29: Low importance
    """
    ranges = {
        "90-100": (90, 100),
        "70-89": (70, 89),
        "50-69": (50, 69),
        "30-49": (30, 49),
        "0-29": (0, 29),
    }

    distribution = {}
    for range_name, (min_score, max_score) in ranges.items():
        count = db.query(func.count(ProcessedNews.id)).filter(
            ProcessedNews.score >= min_score,
            ProcessedNews.score <= max_score
        ).scalar() or 0
        distribution[range_name] = count

    return distribution
