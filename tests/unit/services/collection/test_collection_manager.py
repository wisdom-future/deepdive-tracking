"""Tests for collection manager."""

import pytest
from datetime import datetime
from pytz import UTC
from sqlalchemy.orm import Session

from src.models import DataSource, RawNews
from src.services.collection import CollectionManager


class TestCollectionManager:
    """Tests for CollectionManager class."""

    def test_init(self, test_session: Session):
        """Test manager initialization."""
        manager = CollectionManager(test_session)
        assert manager.db == test_session
        assert manager.logger is not None

    def test_generate_hash(self):
        """Test hash generation for deduplication."""
        hash1 = CollectionManager._generate_hash("Test Title", "https://example.com/article")
        hash2 = CollectionManager._generate_hash("Test Title", "https://example.com/article")
        hash3 = CollectionManager._generate_hash("Different Title", "https://example.com/article")

        # Same input should produce same hash
        assert hash1 == hash2

        # Different input should produce different hash
        assert hash1 != hash3

        # Hash should be 64 characters (SHA256)
        assert len(hash1) == 64

    def test_get_collection_stats_empty(self, test_session: Session):
        """Test getting stats when no data exists."""
        manager = CollectionManager(test_session)
        stats = manager.get_collection_stats()

        assert stats["total_raw_news"] == 0
        assert stats["total_duplicates"] == 0
        assert stats["by_source"] == {}
        assert stats["last_collection_times"] == {}

    def test_get_collection_stats_with_data(
        self, test_session: Session, sample_data_source: DataSource, sample_raw_news: RawNews
    ):
        """Test getting stats with existing data."""
        manager = CollectionManager(test_session)
        stats = manager.get_collection_stats()

        assert stats["total_raw_news"] >= 1
        assert sample_data_source.name in stats["by_source"]

    def test_get_collector_rss(self, test_session: Session, sample_data_source: DataSource):
        """Test getting RSS collector."""
        manager = CollectionManager(test_session)
        sample_data_source.type = "rss"
        test_session.commit()

        collector = manager._get_collector(sample_data_source)
        assert collector is not None
        assert collector.__class__.__name__ == "RSSCollector"

    def test_get_collector_api_not_implemented(self, test_session: Session):
        """Test that API collector shows not implemented warning."""
        manager = CollectionManager(test_session)
        source = DataSource(
            name="Test API",
            type="api",
            url="https://api.example.com",
        )
        test_session.add(source)
        test_session.commit()

        collector = manager._get_collector(source)
        assert collector is None

    def test_get_collector_crawler_not_implemented(self, test_session: Session):
        """Test that crawler collector shows not implemented warning."""
        manager = CollectionManager(test_session)
        source = DataSource(
            name="Test Crawler",
            type="crawler",
            url="https://example.com",
        )
        test_session.add(source)
        test_session.commit()

        collector = manager._get_collector(source)
        assert collector is None
