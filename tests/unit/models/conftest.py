"""Pytest configuration for model tests."""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models import (
    DataSource,
    RawNews,
    ProcessedNews,
    ContentReview,
    PublishedContent,
    ContentStats,
    PublishingSchedule,
    CostLog,
    OperationLog,
)


@pytest.fixture
def test_engine():
    """Create test database engine (in-memory SQLite)."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine) -> Session:
    """Create test database session."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_data_source(test_session: Session) -> DataSource:
    """Create a sample data source."""
    source = DataSource(
        name="OpenAI Blog",
        type="rss",
        url="https://openai.com/blog/rss.xml",
        priority=10,
        is_enabled=True,
    )
    test_session.add(source)
    test_session.commit()
    test_session.refresh(source)
    return source


@pytest.fixture
def sample_raw_news(test_session: Session, sample_data_source: DataSource) -> RawNews:
    """Create a sample raw news."""
    raw_news = RawNews(
        source_id=sample_data_source.id,
        title="Sample News Title",
        url="https://example.com/news/1",
        content="Sample news content",
        hash="abc123def456",
        published_at=datetime.now(),
        fetched_at=datetime.now(),
        status="raw",
    )
    test_session.add(raw_news)
    test_session.commit()
    test_session.refresh(raw_news)
    return raw_news


@pytest.fixture
def sample_processed_news(
    test_session: Session, sample_raw_news: RawNews
) -> ProcessedNews:
    """Create a sample processed news."""
    processed = ProcessedNews(
        raw_news_id=sample_raw_news.id,
        score=85.5,
        category="tech_breakthrough",
        summary_pro="Professional summary of the news",
        summary_sci="Scientific summary of the news",
        keywords=["AI", "technology", "breakthrough"],
    )
    test_session.add(processed)
    test_session.commit()
    test_session.refresh(processed)
    return processed


@pytest.fixture
def sample_content_review(
    test_session: Session, sample_processed_news: ProcessedNews
) -> ContentReview:
    """Create a sample content review."""
    review = ContentReview(
        processed_news_id=sample_processed_news.id,
        status="pending",
        review_notes="Sample review notes",
    )
    test_session.add(review)
    test_session.commit()
    test_session.refresh(review)
    return review


@pytest.fixture
def sample_published_content(
    test_session: Session,
    sample_processed_news: ProcessedNews,
    sample_content_review: ContentReview,
    sample_raw_news: RawNews,
) -> PublishedContent:
    """Create a sample published content."""
    published = PublishedContent(
        processed_news_id=sample_processed_news.id,
        content_review_id=sample_content_review.id,
        raw_news_id=sample_raw_news.id,
        publish_status="draft",
        channels=["wechat", "web"],
        final_title="Final News Title",
    )
    test_session.add(published)
    test_session.commit()
    test_session.refresh(published)
    return published


@pytest.fixture
def sample_content_stats(
    test_session: Session, sample_published_content: PublishedContent
) -> ContentStats:
    """Create a sample content stats."""
    stats = ContentStats(
        published_content_id=sample_published_content.id,
        channel="wechat",
        view_count=100,
        like_count=10,
    )
    test_session.add(stats)
    test_session.commit()
    test_session.refresh(stats)
    return stats
