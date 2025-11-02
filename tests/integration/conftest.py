"""Pytest configuration for integration tests."""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models to register them with Base
from src.models import (
    Base,
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
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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
        name="Integration Test Source",
        type="rss",
        url="https://example.com/rss.xml",
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
        title="Integration Test News",
        url="https://example.com/news/integration",
        content="Test news content for integration tests",
        hash="integration_test_hash",
        source_name=sample_data_source.name,
        published_at=datetime.now(),
        fetched_at=datetime.now(),
        status="raw",
    )
    test_session.add(raw_news)
    test_session.commit()
    test_session.refresh(raw_news)
    return raw_news
