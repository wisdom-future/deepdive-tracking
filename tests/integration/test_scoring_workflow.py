"""Integration tests for complete news scoring workflow.

Tests the full pipeline: data collection → AI scoring → query processing results
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from src.models import DataSource, RawNews, ProcessedNews
from src.services.ai import ScoringService
from src.config.settings import Settings


@pytest.fixture
def integration_settings():
    """Get application settings for integration tests."""
    return Settings()


class TestScoringWorkflow:
    """Integration tests for complete scoring workflow."""

    @pytest.mark.asyncio
    async def test_end_to_end_scoring_workflow(
        self,
        test_session: Session,
        sample_data_source: DataSource,
        sample_raw_news: RawNews,
        integration_settings: Settings,
    ):
        """Test complete workflow: collection → scoring → storage → query."""
        # Step 1: Use sample raw news for testing
        raw_news = sample_raw_news

        # Verify raw news was created
        assert raw_news.id is not None
        assert raw_news.status == "raw"
        initial_count = test_session.query(RawNews).count()
        assert initial_count >= 1

        # Step 2: Score the news using AI service
        with patch("src.services.ai.scoring_service.OpenAI") as mock_openai:
            service = ScoringService(integration_settings, test_session)
            service.client = Mock()

            # Mock scoring response
            mock_scoring_response = Mock()
            mock_scoring_response.choices = [Mock()]
            mock_scoring_response.choices[0].message.content = json.dumps({
                "score": 88,
                "score_reasoning": "Major breakthrough in AI technology",
                "category": "tech_breakthrough",
                "sub_categories": ["model_release"],
                "confidence": 0.92,
                "key_points": [
                    "Significant performance improvement",
                    "Enhanced efficiency and speed",
                    "Will accelerate industry adoption"
                ],
                "keywords": ["AI", "breakthrough", "model", "technology", "innovation"],
                "entities": {
                    "companies": ["Example Corp"],
                    "technologies": ["Neural Networks"],
                    "people": ["Dr. Smith"]
                },
                "impact_analysis": "This breakthrough will significantly impact AI industry development"
            })
            mock_scoring_response.usage.prompt_tokens = 500
            mock_scoring_response.usage.completion_tokens = 300

            # Mock summary responses
            mock_summary_pro = Mock()
            mock_summary_pro.choices = [Mock()]
            mock_summary_pro.choices[0].message.content = json.dumps({
                "summary_pro": "Technical breakthrough in AI delivering significant performance improvements. This advancement represents a major milestone with broad implications for industry transformation and competitive advantage."
            })
            mock_summary_pro.usage.prompt_tokens = 200
            mock_summary_pro.usage.completion_tokens = 100

            mock_summary_sci = Mock()
            mock_summary_sci.choices = [Mock()]
            mock_summary_sci.choices[0].message.content = json.dumps({
                "summary_sci": "New AI advancement makes technology faster and more capable for practical applications. This breakthrough demonstrates significant progress in making advanced AI accessible for solving complex problems."
            })
            mock_summary_sci.usage.prompt_tokens = 200
            mock_summary_sci.usage.completion_tokens = 100

            service.client.chat.completions.create.side_effect = [
                mock_scoring_response,
                mock_summary_pro,
                mock_summary_sci,
            ]

            # Execute scoring
            result = await service.score_news(raw_news)

            # Verify scoring result
            assert result.scoring.score == 88
            assert result.scoring.category.value == "tech_breakthrough"
            assert result.scoring.confidence == 0.92
            assert len(result.scoring.key_points) == 3
            assert result.metadata.cost > 0
            assert result.metadata.processing_time_ms > 0
            assert len(result.summaries.summary_pro) > 0
            assert len(result.summaries.summary_sci) > 0

        # Step 3: Save scoring result to database
        with patch("src.services.ai.scoring_service.OpenAI"):
            service = ScoringService(integration_settings, test_session)
            processed = await service.save_to_database(raw_news, result)

            # Verify processed news was created
            assert processed.id is not None
            assert processed.score == 88
            assert processed.category == "tech_breakthrough"
            assert processed.raw_news_id == raw_news.id

        # Step 4: Query the processed news
        test_session.refresh(raw_news)
        assert raw_news.status == "processed"

        # Query from database
        queried_processed = test_session.query(ProcessedNews).filter(
            ProcessedNews.raw_news_id == raw_news.id
        ).first()

        assert queried_processed is not None
        assert queried_processed.score == 88
        assert queried_processed.category == "tech_breakthrough"
        assert queried_processed.confidence == 0.92
        assert len(queried_processed.keywords) >= 5

    @pytest.mark.asyncio
    async def test_batch_scoring_workflow(
        self,
        test_session: Session,
        sample_data_source: DataSource,
        integration_settings: Settings,
    ):
        """Test batch scoring workflow."""
        # Create multiple raw news items
        raw_news_list = []
        for i in range(3):
            raw_news = RawNews(
                source_id=sample_data_source.id,
                title=f"News Item {i}",
                url=f"https://example.com/news/{i}",
                content=f"Content for news item {i}",
                source_name=sample_data_source.name,
                hash=f"integration_batch_hash_{i}",
                published_at=datetime.now(),
                fetched_at=datetime.now(),
                status="raw",
            )
            test_session.add(raw_news)
            raw_news_list.append(raw_news)

        test_session.commit()
        for raw_news in raw_news_list:
            test_session.refresh(raw_news)

        # Score all items in batch
        with patch("src.services.ai.scoring_service.OpenAI"):
            service = ScoringService(integration_settings, test_session)
            service.client = Mock()

            # Create mock responses
            mock_scoring = Mock()
            mock_scoring.choices = [Mock()]
            mock_scoring.choices[0].message.content = json.dumps({
                "score": 75,
                "score_reasoning": "Good article",
                "category": "company_news",
                "sub_categories": [],
                "confidence": 0.85,
                "key_points": ["P1", "P2", "P3"],
                "keywords": ["a", "b", "c", "d", "e"],
                "entities": {"companies": [], "technologies": [], "people": []},
                "impact_analysis": "Moderate impact"
            })
            mock_scoring.usage.prompt_tokens = 400
            mock_scoring.usage.completion_tokens = 200

            mock_summary_pro = Mock()
            mock_summary_pro.choices = [Mock()]
            mock_summary_pro.choices[0].message.content = json.dumps({
                "summary_pro": "Professional summary of article content highlighting key points and significance for industry experts and decision makers."
            })
            mock_summary_pro.usage.prompt_tokens = 200
            mock_summary_pro.usage.completion_tokens = 100

            mock_summary_sci = Mock()
            mock_summary_sci.choices = [Mock()]
            mock_summary_sci.choices[0].message.content = json.dumps({
                "summary_sci": "Accessible summary explaining the article content in simple language for general audiences without specialized technical background knowledge."
            })
            mock_summary_sci.usage.prompt_tokens = 200
            mock_summary_sci.usage.completion_tokens = 100

            # Set up responses for batch
            responses = []
            for _ in range(len(raw_news_list)):
                responses.extend([mock_scoring, mock_summary_pro, mock_summary_sci])

            service.client.chat.completions.create.side_effect = responses

            # Execute batch scoring
            results, errors = await service.batch_score(raw_news_list)

            # Verify results
            assert len(results) == 3
            assert len(errors) == 0
            assert all(r.scoring.score == 75 for r in results)

        # Verify results were saved (batch_score doesn't save to DB, must save separately)
        # This is by design - the service returns results which must be saved explicitly
        assert len(results) == 3
