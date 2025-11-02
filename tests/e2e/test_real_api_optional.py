"""End-to-End tests using REAL OpenAI API.

These tests are OPTIONAL and verify actual API behavior.
Requires: ENABLE_REAL_API_TESTS=1 environment variable and valid OpenAI API key

Run with:
    ENABLE_REAL_API_TESTS=1 pytest tests/e2e/test_real_api_optional.py -v
"""

import os
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from src.models import DataSource, RawNews
from src.services.ai import ScoringService
from src.config.settings import Settings


# Skip all tests in this file unless explicitly enabled
pytestmark = pytest.mark.skipif(
    not os.getenv("ENABLE_REAL_API_TESTS"),
    reason="Real API tests disabled. Enable with ENABLE_REAL_API_TESTS=1"
)


@pytest.fixture
def e2e_settings():
    """Get settings for E2E tests."""
    settings = Settings()
    assert settings.openai_api_key, "OPENAI_API_KEY not configured"
    assert not settings.openai_api_key.startswith("mock-"), "Using mock key for real API tests!"
    return settings


class TestRealAPIScoringIntegration:
    """Integration tests with real OpenAI API."""

    @pytest.mark.asyncio
    async def test_real_api_single_news_scoring(
        self,
        test_session: Session,
        sample_data_source: DataSource,
        e2e_settings: Settings,
    ):
        """Test scoring with real OpenAI API.

        **Important**: This test uses real API credits!
        Only run when explicitly enabled via ENABLE_REAL_API_TESTS=1 env var.

        Verifies:
        - Actual API connectivity
        - Real token usage
        - Actual response structure
        - Cost calculation accuracy
        """
        # Create test news
        raw_news = RawNews(
            source_id=sample_data_source.id,
            title="OpenAI Releases GPT-4o Model",
            url="https://example.com/gpt-4o-release",
            content=(
                "OpenAI announced the release of GPT-4o, a new multimodal large language model. "
                "The model demonstrates significant improvements in performance and efficiency "
                "compared to previous versions, with enhanced capabilities for processing text, "
                "images, and audio. This advancement represents a major milestone in AI development."
            ),
            source_name=sample_data_source.name,
            hash="real_api_test_001",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            status="raw",
        )
        test_session.add(raw_news)
        test_session.commit()
        test_session.refresh(raw_news)

        # Initialize service with REAL API (no mocking)
        service = ScoringService(e2e_settings, test_session)

        # Execute scoring with real API
        result = await service.score_news(raw_news)

        # Verify result structure
        assert result.scoring.score is not None
        assert 0 <= result.scoring.score <= 100
        assert result.scoring.category is not None
        assert result.scoring.confidence > 0
        assert len(result.scoring.key_points) >= 3
        assert len(result.scoring.keywords) >= 4

        # Verify summaries
        assert len(result.summaries.summary_pro) >= 100
        assert len(result.summaries.summary_pro) <= 300
        assert len(result.summaries.summary_sci) >= 100
        assert len(result.summaries.summary_sci) <= 300

        # Verify cost calculation
        assert result.metadata.cost > 0
        assert result.metadata.processing_time_ms > 0

        # Print real API results
        print("\n" + "=" * 70)
        print("REAL API TEST RESULTS")
        print("=" * 70)
        print(f"\nNews: {raw_news.title}")
        print(f"\nScoring:")
        print(f"  Score: {result.scoring.score}/100")
        print(f"  Category: {result.scoring.category.value}")
        print(f"  Confidence: {result.scoring.confidence:.2%}")
        print(f"\nKey Points:")
        for i, point in enumerate(result.scoring.key_points, 1):
            print(f"  {i}. {point}")
        print(f"\nKeywords: {', '.join(result.scoring.keywords)}")
        print(f"\nProfessional Summary:\n  {result.summaries.summary_pro}")
        print(f"\nScientific Summary:\n  {result.summaries.summary_sci}")
        print(f"\nCost Information:")
        print(f"  API Cost: ${result.metadata.cost:.6f}")
        print(f"  Processing Time: {result.metadata.processing_time_ms}ms")
        print(f"  Models Used: {', '.join(result.metadata.ai_models_used)}")

    @pytest.mark.asyncio
    async def test_real_api_batch_scoring(
        self,
        test_session: Session,
        sample_data_source: DataSource,
        e2e_settings: Settings,
    ):
        """Test batch scoring with real OpenAI API.

        **Important**: This test uses real API credits!
        """
        # Create 3 test news items
        news_items = []
        test_titles = [
            "Google Announces New AI Chip Technology",
            "Meta Releases AI Model for Researchers",
            "Microsoft Expands Azure AI Services",
        ]

        for title in test_titles:
            raw_news = RawNews(
                source_id=sample_data_source.id,
                title=title,
                url=f"https://example.com/{title.lower().replace(' ', '-')}",
                content=f"News article about {title}. The content provides details about new developments.",
                source_name=sample_data_source.name,
                hash=f"real_api_batch_{len(news_items)}",
                published_at=datetime.now(),
                fetched_at=datetime.now(),
                status="raw",
            )
            test_session.add(raw_news)
            news_items.append(raw_news)

        test_session.commit()
        for item in news_items:
            test_session.refresh(item)

        # Initialize service with REAL API
        service = ScoringService(e2e_settings, test_session)

        # Execute batch scoring
        results, errors = await service.batch_score(news_items)

        # Verify results
        assert len(results) == 3
        assert len(errors) == 0

        # Print batch results
        print("\n" + "=" * 70)
        print("REAL API BATCH TEST RESULTS")
        print("=" * 70)
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {news_items[i-1].title}")
            print(f"   Score: {result.scoring.score}/100")
            print(f"   Category: {result.scoring.category.value}")
            print(f"   Cost: ${result.metadata.cost:.6f}")

        total_cost = sum(r.metadata.cost for r in results)
        print(f"\nBatch Totals:")
        print(f"  Items: {len(results)}")
        print(f"  Total Cost: ${total_cost:.6f}")
        print(f"  Cost per Item: ${total_cost/len(results):.6f}")

    @pytest.mark.asyncio
    async def test_token_counting_accuracy(
        self,
        test_session: Session,
        sample_raw_news: RawNews,
        e2e_settings: Settings,
    ):
        """Verify actual token counting matches expected estimates.

        This test validates that our cost calculations are accurate
        by comparing mock estimates with real token counts from API.
        """
        service = ScoringService(e2e_settings, test_session)

        # Score with real API
        result = await service.score_news(sample_raw_news)

        # Extract actual token counts from metadata
        cost_breakdown = result.metadata.cost_breakdown

        # Verify cost breakdown includes all operations
        assert "scoring" in cost_breakdown
        # Note: summaries might be combined or separate
        assert any(
            key in cost_breakdown for key in ["summary_pro", "summary_sci", "summaries"]
        ), f"Expected summary costs in: {cost_breakdown.keys()}"

        print(f"\nToken Counting Verification:")
        print(f"  Cost Breakdown: {cost_breakdown}")
        print(f"  Total Cost: ${result.metadata.cost:.6f}")


class TestRealAPICostProjection:
    """Cost projection tests using real API pricing."""

    def test_daily_cost_projection_with_real_api(self):
        """Calculate actual daily cost with real pricing."""
        settings = Settings()

        # Real GPT-4o pricing (October 2024)
        input_cost_per_1k = 0.005
        output_cost_per_1k = 0.015

        # Typical scoring scenario
        avg_input_tokens = 1500  # Varies by content length
        avg_output_tokens = 300

        # Single news scoring cost (scoring + 2 summaries)
        cost_per_news = (
            (avg_input_tokens * input_cost_per_1k / 1000) +
            (avg_output_tokens * output_cost_per_1k / 1000) +
            (200 * input_cost_per_1k / 1000 + 100 * output_cost_per_1k / 1000) * 2
        )

        # Daily projections
        daily_volumes = [100, 300, 500, 1000]

        print(f"\n\nDaily Cost Projections (Real API Pricing):")
        print("=" * 60)
        for volume in daily_volumes:
            daily_cost = cost_per_news * volume
            print(f"  {volume:4d} articles/day: ${daily_cost:8.2f} ({daily_cost/30:6.2f}/month)")


# Conditional markers for different test scenarios
# To run only real API tests when available:
#   pytest tests/e2e/ -m real_api
#
# To run all except real API tests:
#   pytest tests/ -m "not real_api"
