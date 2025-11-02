"""Unit tests for database models."""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

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


class TestDataSource:
    """Tests for DataSource model."""

    def test_create_data_source(self, test_session: Session):
        """Test creating a data source."""
        source = DataSource(
            name="Test Source",
            type="rss",
            url="https://example.com/feed",
            priority=5,
        )
        test_session.add(source)
        test_session.commit()
        test_session.refresh(source)

        assert source.id is not None
        assert source.name == "Test Source"
        assert source.type == "rss"
        assert source.is_enabled is True
        assert source.created_at is not None

    def test_data_source_constraints(self, test_session: Session):
        """Test data source constraints."""
        # Test invalid type
        source = DataSource(
            name="Invalid Type",
            type="invalid_type",
            url="https://example.com",
        )
        test_session.add(source)
        with pytest.raises(Exception):  # Will fail constraint check
            test_session.commit()

    def test_data_source_priority_validation(self, test_session: Session):
        """Test data source priority validation."""
        source = DataSource(
            name="Test",
            type="rss",
            priority=15,  # Out of range
        )
        test_session.add(source)
        with pytest.raises(Exception):
            test_session.commit()


class TestRawNews:
    """Tests for RawNews model."""

    def test_create_raw_news(
        self, test_session: Session, sample_data_source: DataSource
    ):
        """Test creating raw news."""
        raw = RawNews(
            source_id=sample_data_source.id,
            title="News Title",
            url="https://example.com/article",
            hash="hash123",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
        )
        test_session.add(raw)
        test_session.commit()
        test_session.refresh(raw)

        assert raw.id is not None
        assert raw.status == "raw"
        assert raw.title == "News Title"
        assert raw.source_id == sample_data_source.id

    def test_raw_news_foreign_key(
        self, test_session: Session, sample_data_source: DataSource
    ):
        """Test raw news foreign key relationship with valid source."""
        raw = RawNews(
            source_id=sample_data_source.id,
            title="Test",
            url="https://example.com/test",
            hash="hash456",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
        )
        test_session.add(raw)
        test_session.commit()
        test_session.refresh(raw)

        # Verify relationship works
        assert raw.data_source is not None
        assert raw.data_source.id == sample_data_source.id

    def test_raw_news_unique_constraints(
        self, test_session: Session, sample_raw_news: RawNews
    ):
        """Test raw news unique constraints."""
        # Try to create another with same URL
        duplicate = RawNews(
            source_id=sample_raw_news.source_id,
            title="Different Title",
            url=sample_raw_news.url,  # Same URL
            hash="different_hash",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
        )
        test_session.add(duplicate)
        with pytest.raises(Exception):  # Unique constraint
            test_session.commit()


class TestProcessedNews:
    """Tests for ProcessedNews model."""

    def test_create_processed_news(
        self, test_session: Session, sample_raw_news: RawNews
    ):
        """Test creating processed news."""
        processed = ProcessedNews(
            raw_news_id=sample_raw_news.id,
            score=90.5,
            category="tech_breakthrough",
            summary_pro="Professional summary",
            summary_sci="Scientific summary",
        )
        test_session.add(processed)
        test_session.commit()
        test_session.refresh(processed)

        assert processed.id is not None
        assert processed.score == 90.5
        assert processed.category == "tech_breakthrough"
        assert processed.version == 1

    def test_processed_news_score_validation(
        self, test_session: Session, sample_raw_news: RawNews
    ):
        """Test processed news score validation."""
        processed = ProcessedNews(
            raw_news_id=sample_raw_news.id,
            score=150.0,  # Out of range (0-100)
            category="tech_breakthrough",
            summary_pro="Test",
            summary_sci="Test",
        )
        test_session.add(processed)
        with pytest.raises(Exception):
            test_session.commit()

    def test_processed_news_category_validation(
        self, test_session: Session, sample_raw_news: RawNews
    ):
        """Test processed news category validation."""
        processed = ProcessedNews(
            raw_news_id=sample_raw_news.id,
            score=75.0,
            category="invalid_category",
            summary_pro="Test",
            summary_sci="Test",
        )
        test_session.add(processed)
        with pytest.raises(Exception):
            test_session.commit()


class TestContentReview:
    """Tests for ContentReview model."""

    def test_create_content_review(
        self, test_session: Session, sample_processed_news: ProcessedNews
    ):
        """Test creating content review."""
        review = ContentReview(
            processed_news_id=sample_processed_news.id,
            status="pending",
            review_notes="Please review",
        )
        test_session.add(review)
        test_session.commit()
        test_session.refresh(review)

        assert review.id is not None
        assert review.status == "pending"
        assert review.review_notes == "Please review"

    def test_content_review_relationship(
        self, test_session: Session, sample_content_review: ContentReview
    ):
        """Test content review relationships."""
        retrieved = (
            test_session.query(ContentReview)
            .filter_by(id=sample_content_review.id)
            .first()
        )
        assert retrieved is not None
        assert retrieved.processed_news.id == sample_content_review.processed_news_id


class TestPublishedContent:
    """Tests for PublishedContent model."""

    def test_create_published_content(
        self,
        test_session: Session,
        sample_processed_news: ProcessedNews,
        sample_raw_news: RawNews,
    ):
        """Test creating published content."""
        published = PublishedContent(
            processed_news_id=sample_processed_news.id,
            raw_news_id=sample_raw_news.id,
            publish_status="draft",
            channels=["wechat", "web"],
        )
        test_session.add(published)
        test_session.commit()
        test_session.refresh(published)

        assert published.id is not None
        assert published.publish_status == "draft"
        assert len(published.channels) == 2
        assert "wechat" in published.channels

    def test_published_content_status_validation(
        self,
        test_session: Session,
        sample_processed_news: ProcessedNews,
        sample_raw_news: RawNews,
    ):
        """Test published content status validation."""
        published = PublishedContent(
            processed_news_id=sample_processed_news.id,
            raw_news_id=sample_raw_news.id,
            publish_status="invalid_status",
            channels=["web"],
        )
        test_session.add(published)
        with pytest.raises(Exception):
            test_session.commit()


class TestContentStats:
    """Tests for ContentStats model."""

    def test_create_content_stats(
        self, test_session: Session, sample_published_content: PublishedContent
    ):
        """Test creating content stats."""
        stats = ContentStats(
            published_content_id=sample_published_content.id,
            channel="wechat",
            view_count=100,
            like_count=15,
            share_count=5,
        )
        test_session.add(stats)
        test_session.commit()
        test_session.refresh(stats)

        assert stats.id is not None
        assert stats.view_count == 100
        assert stats.like_count == 15
        assert stats.channel == "wechat"

    def test_content_stats_channel_validation(
        self, test_session: Session, sample_published_content: PublishedContent
    ):
        """Test content stats channel validation."""
        stats = ContentStats(
            published_content_id=sample_published_content.id,
            channel="invalid_channel",
            view_count=100,
        )
        test_session.add(stats)
        with pytest.raises(Exception):
            test_session.commit()


class TestPublishingSchedule:
    """Tests for PublishingSchedule model."""

    def test_create_publishing_schedule(self, test_session: Session):
        """Test creating publishing schedule."""
        schedule = PublishingSchedule(
            schedule_type="daily_brief",
            content_ids=[1, 2, 3],
            scheduled_at=datetime.now(),
            target_channels=["wechat", "web"],
        )
        test_session.add(schedule)
        test_session.commit()
        test_session.refresh(schedule)

        assert schedule.id is not None
        assert schedule.status == "pending"
        assert len(schedule.content_ids) == 3
        assert schedule.retry_count == 0

    def test_publishing_schedule_status_validation(self, test_session: Session):
        """Test publishing schedule status validation."""
        schedule = PublishingSchedule(
            schedule_type="daily_brief",
            content_ids=[1],
            scheduled_at=datetime.now(),
            target_channels=["web"],
            status="invalid_status",
        )
        test_session.add(schedule)
        with pytest.raises(Exception):
            test_session.commit()


class TestCostLog:
    """Tests for CostLog model."""

    def test_create_cost_log(self, test_session: Session):
        """Test creating cost log."""
        cost = CostLog(
            service="openai",
            operation="scoring",
            usage_units=1500,
            unit_price=0.0001,
            total_cost=0.15,
        )
        test_session.add(cost)
        test_session.commit()
        test_session.refresh(cost)

        assert cost.id is not None
        assert cost.service == "openai"
        assert cost.total_cost == 0.15

    def test_cost_log_positive_constraint(self, test_session: Session):
        """Test cost log positive cost constraint."""
        cost = CostLog(
            service="test",
            operation="test",
            total_cost=-10.0,  # Negative cost
        )
        test_session.add(cost)
        with pytest.raises(Exception):
            test_session.commit()


class TestOperationLog:
    """Tests for OperationLog model."""

    def test_create_operation_log(self, test_session: Session):
        """Test creating operation log."""
        log = OperationLog(
            operation_type="create",
            resource_type="raw_news",
            resource_id=1,
            operator_id="user_123",
            operator_name="John Doe",
            action_detail="Created new news entry",
            status="success",
        )
        test_session.add(log)
        test_session.commit()
        test_session.refresh(log)

        assert log.id is not None
        assert log.operation_type == "create"
        assert log.status == "success"
        assert log.created_at is not None


class TestModelRelationships:
    """Tests for model relationships."""

    def test_raw_news_to_processed_news_relationship(
        self, test_session: Session, sample_raw_news: RawNews
    ):
        """Test RawNews to ProcessedNews relationship."""
        processed = ProcessedNews(
            raw_news_id=sample_raw_news.id,
            score=80.0,
            category="tech_breakthrough",
            summary_pro="Test",
            summary_sci="Test",
        )
        test_session.add(processed)
        test_session.commit()

        # Verify relationship
        retrieved_raw = (
            test_session.query(RawNews).filter_by(id=sample_raw_news.id).first()
        )
        assert retrieved_raw.processed_news is not None
        assert retrieved_raw.processed_news.score == 80.0

    def test_processed_news_to_content_review_relationship(
        self, test_session: Session, sample_content_review: ContentReview
    ):
        """Test ProcessedNews to ContentReview relationship."""
        # Verify relationship
        retrieved = (
            test_session.query(ProcessedNews)
            .filter_by(id=sample_content_review.processed_news_id)
            .first()
        )
        assert retrieved is not None
        assert retrieved.content_review is not None
        assert retrieved.content_review.status == "pending"

    def test_data_source_to_raw_news_relationship(
        self, test_session: Session, sample_data_source: DataSource
    ):
        """Test DataSource to RawNews relationship."""
        raw = RawNews(
            source_id=sample_data_source.id,
            title="Test",
            url="https://test.com",
            hash="test123",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
        )
        test_session.add(raw)
        test_session.commit()

        # Verify relationship
        retrieved_source = (
            test_session.query(DataSource)
            .filter_by(id=sample_data_source.id)
            .first()
        )
        assert len(retrieved_source.raw_news) > 0


class TestModelTimestamps:
    """Tests for model timestamps."""

    def test_created_at_timestamp(self, test_session: Session):
        """Test created_at timestamp is automatically set."""
        source = DataSource(
            name="Test",
            type="rss",
        )
        test_session.add(source)
        test_session.commit()
        test_session.refresh(source)

        assert source.created_at is not None
        assert isinstance(source.created_at, datetime)

    def test_updated_at_timestamp(self, test_session: Session):
        """Test updated_at timestamp is automatically set."""
        source = DataSource(
            name="Test",
            type="rss",
        )
        test_session.add(source)
        test_session.commit()
        test_session.refresh(source)

        original_updated = source.updated_at
        assert original_updated is not None

        # Update the source
        source.priority = 8
        test_session.commit()
        test_session.refresh(source)

        # updated_at should be same or later (in test env with same second, it might be same)
        assert source.updated_at >= original_updated
