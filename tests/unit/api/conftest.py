"""Pytest configuration for API tests."""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Use static pool for in-memory database
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
        source_name=sample_data_source.name,  # Add source_name from data_source
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
def client(test_session: Session):
    """Create test client with test database."""
    from fastapi.testclient import TestClient
    from src.main import create_app
    from src.api.v1.dependencies import get_db

    app = create_app()

    def override_get_db():
        return test_session

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
