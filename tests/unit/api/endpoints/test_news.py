"""Tests for news API endpoints."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import create_app
from src.database import SessionLocal
from src.models import DataSource, RawNews, ProcessedNews




class TestNewsEndpoints:
    """Tests for news endpoints."""

    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Welcome" in response.json()["message"]

    def test_get_news_items_empty(self, client: TestClient):
        """Test getting news items when database is empty."""
        response = client.get("/api/v1/news/items")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_get_news_items_with_data(
        self, client: TestClient, test_session: Session, sample_data_source: DataSource, sample_raw_news: RawNews
    ):
        """Test getting news items with data."""
        response = client.get("/api/v1/news/items")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert data["items"][0]["title"] == "Sample News Title"

    def test_get_news_items_pagination(
        self, client: TestClient, test_session: Session, sample_data_source: DataSource
    ):
        """Test news pagination."""
        # Create multiple news items
        for i in range(25):
            raw = RawNews(
                source_id=sample_data_source.id,
                title=f"News {i}",
                url=f"https://example.com/news/{i}",
                hash=f"hash{i}",
                published_at=datetime.now(),
                fetched_at=datetime.now(),
            )
            test_session.add(raw)
        test_session.commit()

        # Test first page
        response = client.get("/api/v1/news/items?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 1

        # Test second page
        response = client.get("/api/v1/news/items?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 2

    def test_get_news_item_detail(
        self, client: TestClient, test_session: Session, sample_raw_news: RawNews
    ):
        """Test getting detailed news item."""
        response = client.get(f"/api/v1/news/items/{sample_raw_news.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["raw_news"]["id"] == sample_raw_news.id
        assert data["raw_news"]["title"] == sample_raw_news.title

    def test_get_news_item_detail_not_found(self, client: TestClient):
        """Test getting non-existent news item."""
        response = client.get("/api/v1/news/items/99999")
        assert response.status_code == 404

    def test_get_news_item_with_processed_data(
        self, client: TestClient, test_session: Session, sample_processed_news: ProcessedNews
    ):
        """Test getting news item with processed data."""
        raw_news_id = sample_processed_news.raw_news_id
        response = client.get(f"/api/v1/news/items/{raw_news_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["processed_news"] is not None
        assert data["processed_news"]["score"] == sample_processed_news.score

    def test_get_unprocessed_news(
        self, client: TestClient, test_session: Session, sample_data_source: DataSource
    ):
        """Test getting unprocessed news items."""
        # Create both processed and unprocessed items
        raw1 = RawNews(
            source_id=sample_data_source.id,
            title="Unprocessed News",
            url="https://example.com/unprocessed",
            hash="hash_unprocessed",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            status="raw",
        )
        raw2 = RawNews(
            source_id=sample_data_source.id,
            title="Processed News",
            url="https://example.com/processed",
            hash="hash_processed",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            status="processed",
        )
        test_session.add_all([raw1, raw2])
        test_session.commit()

        response = client.get("/api/v1/news/unprocessed")
        assert response.status_code == 200
        data = response.json()
        # Should only return items with 'raw' status
        assert all(item["status"] == "raw" for item in data["items"])

    def test_get_news_by_source(
        self, client: TestClient, test_session: Session, sample_data_source: DataSource, sample_raw_news: RawNews
    ):
        """Test getting news by source."""
        response = client.get(f"/api/v1/news/by-source/{sample_data_source.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(item["source_name"] == sample_data_source.name for item in data["items"])

    def test_filter_by_status(
        self, client: TestClient, test_session: Session, sample_data_source: DataSource
    ):
        """Test filtering news by status."""
        # Create items with different statuses
        raw1 = RawNews(
            source_id=sample_data_source.id,
            title="Raw News",
            url="https://example.com/raw",
            hash="hash_raw",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            status="raw",
        )
        raw2 = RawNews(
            source_id=sample_data_source.id,
            title="Failed News",
            url="https://example.com/failed",
            hash="hash_failed",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            status="failed",
        )
        test_session.add_all([raw1, raw2])
        test_session.commit()

        response = client.get("/api/v1/news/items?status_filter=raw")
        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "raw" for item in data["items"])
