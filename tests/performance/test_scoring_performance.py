"""Performance benchmarks and cost analysis for AI scoring service.

Measures:
- Execution time for single and batch scoring
- API token usage and costs
- Database operations performance
- Memory usage patterns
"""

import pytest
import json
import time
from datetime import datetime
from unittest.mock import Mock
from sqlalchemy.orm import Session

from src.models import DataSource, RawNews
from src.services.ai import ScoringService
from src.config.settings import Settings


@pytest.fixture
def performance_settings():
    """Get settings for performance tests."""
    return Settings()


@pytest.fixture
def large_news_batch(test_session: Session, sample_data_source: DataSource):
    """Create a batch of 50 news items for performance testing."""
    news_items = []
    for i in range(50):
        raw_news = RawNews(
            source_id=sample_data_source.id,
            title=f"Performance Test News {i}",
            url=f"https://example.com/perf-test/{i}",
            content=f"This is test news item {i} with sample content for performance testing.",
            source_name=sample_data_source.name,
            hash=f"perf_test_hash_{i:03d}",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            status="raw",
        )
        test_session.add(raw_news)
        news_items.append(raw_news)

    test_session.commit()
    for item in news_items:
        test_session.refresh(item)

    return news_items


class TestScoringPerformance:
    """Performance tests for scoring service."""

    @pytest.mark.asyncio
    async def test_single_news_scoring_performance(
        self,
        test_session: Session,
        sample_raw_news: RawNews,
        performance_settings: Settings,
    ):
        """Benchmark single news scoring performance."""
        from unittest.mock import patch

        with patch("src.services.ai.scoring_service.OpenAI"):
            service = ScoringService(performance_settings, test_session)
            service.client = Mock()

            # Mock response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "score": 85,
                "score_reasoning": "Benchmark test",
                "category": "tech_breakthrough",
                "sub_categories": [],
                "confidence": 0.92,
                "key_points": ["P1", "P2", "P3"],
                "keywords": ["test", "bench", "mark", "perf", "score"],
                "entities": {"companies": [], "technologies": [], "people": []},
                "impact_analysis": "Test impact"
            })
            mock_response.usage.prompt_tokens = 500
            mock_response.usage.completion_tokens = 300

            # Create summary responses
            mock_summary_pro = Mock()
            mock_summary_pro.choices = [Mock()]
            mock_summary_pro.choices[0].message.content = json.dumps({
                "summary_pro": "Professional summary for performance benchmark test of AI scoring system capabilities and functionality analysis."
            })
            mock_summary_pro.usage.prompt_tokens = 200
            mock_summary_pro.usage.completion_tokens = 100

            mock_summary_sci = Mock()
            mock_summary_sci.choices = [Mock()]
            mock_summary_sci.choices[0].message.content = json.dumps({
                "summary_sci": "Scientific summary explaining performance benchmark test results for general audience understanding."
            })
            mock_summary_sci.usage.prompt_tokens = 200
            mock_summary_sci.usage.completion_tokens = 100

            service.client.chat.completions.create.side_effect = [
                mock_response,
                mock_summary_pro,
                mock_summary_sci,
            ]

            # Measure execution time
            start_time = time.time()
            result = await service.score_news(sample_raw_news)
            execution_time = time.time() - start_time

            # Assertions
            assert result.scoring.score == 85
            assert result.metadata.processing_time_ms >= 0

            # Performance assertions
            assert execution_time < 1.0  # Should complete in less than 1 second (mock)
            assert result.metadata.cost > 0

            print(f"Single news scoring:")
            print(f"  - Execution time: {execution_time*1000:.2f}ms")
            print(f"  - Processing time (reported): {result.metadata.processing_time_ms}ms")
            print(f"  - Token usage: {mock_response.usage.prompt_tokens + mock_response.usage.completion_tokens}")
            print(f"  - Estimated cost: ${result.metadata.cost:.6f}")

    @pytest.mark.asyncio
    async def test_batch_scoring_performance(
        self,
        test_session: Session,
        large_news_batch,
        performance_settings: Settings,
    ):
        """Benchmark batch scoring performance with 50 items."""
        from unittest.mock import patch

        with patch("src.services.ai.scoring_service.OpenAI"):
            service = ScoringService(performance_settings, test_session)
            service.client = Mock()

            # Create mock responses
            mock_scoring = Mock()
            mock_scoring.choices = [Mock()]
            mock_scoring.choices[0].message.content = json.dumps({
                "score": 70,
                "score_reasoning": "Batch test",
                "category": "company_news",
                "sub_categories": [],
                "confidence": 0.8,
                "key_points": ["P1", "P2", "P3"],
                "keywords": ["batch", "test", "perf", "score", "analyze"],
                "entities": {"companies": [], "technologies": [], "people": []},
                "impact_analysis": "Batch impact"
            })
            mock_scoring.usage.prompt_tokens = 400
            mock_scoring.usage.completion_tokens = 200

            mock_summary = Mock()
            mock_summary.choices = [Mock()]
            mock_summary.choices[0].message.content = json.dumps({
                "summary_pro": "Batch performance test summary demonstrating key findings and analysis results. This test measures processing efficiency and cost metrics for large-scale news item evaluation and categorization."
            })
            mock_summary.usage.prompt_tokens = 200
            mock_summary.usage.completion_tokens = 100

            # Prepare responses for batch
            responses = []
            for _ in range(len(large_news_batch)):
                responses.extend([mock_scoring, mock_summary, mock_summary])

            service.client.chat.completions.create.side_effect = responses

            # Measure batch execution time
            start_time = time.time()
            results, errors = await service.batch_score(large_news_batch)
            execution_time = time.time() - start_time

            # Assertions
            assert len(results) == len(large_news_batch)
            assert len(errors) == 0
            assert all(r.scoring.score == 70 for r in results)

            # Calculate statistics
            total_cost = sum(r.metadata.cost for r in results)
            avg_cost_per_item = total_cost / len(results)
            total_tokens = sum(
                r.metadata.cost_breakdown.get("scoring", 0) * 1000 / 0.000005  # Rough estimate
                for r in results
            )

            print(f"\nBatch scoring ({len(large_news_batch)} items):")
            print(f"  - Total execution time: {execution_time:.2f}s")
            print(f"  - Time per item: {execution_time/len(large_news_batch)*1000:.2f}ms")
            print(f"  - Total estimated cost: ${total_cost:.6f}")
            print(f"  - Cost per item: ${avg_cost_per_item:.6f}")
            print(f"  - Items/second: {len(large_news_batch)/execution_time:.1f}")

    def test_cost_analysis(self, performance_settings: Settings):
        """Analyze API costs for different scenarios."""
        # GPT-4o pricing (as of knowledge cutoff)
        # Input: $0.005 per 1K tokens
        # Output: $0.015 per 1K tokens

        scenarios = [
            {
                "name": "Small article (500 words)",
                "input_tokens": 750,
                "output_tokens": 300,
                "count": 1,
            },
            {
                "name": "Medium article (1000 words)",
                "input_tokens": 1500,
                "output_tokens": 300,
                "count": 1,
            },
            {
                "name": "Large article (2000 words)",
                "input_tokens": 3000,
                "output_tokens": 300,
                "count": 1,
            },
            {
                "name": "Daily batch (100 medium articles)",
                "input_tokens": 1500,
                "output_tokens": 300,
                "count": 100,
            },
            {
                "name": "Weekly batch (700 medium articles)",
                "input_tokens": 1500,
                "output_tokens": 300,
                "count": 700,
            },
            {
                "name": "Monthly batch (3000 medium articles)",
                "input_tokens": 1500,
                "output_tokens": 300,
                "count": 3000,
            },
        ]

        print("\n\nCost Analysis for Different Scenarios:")
        print("=" * 70)

        for scenario in scenarios:
            # Cost per call (scoring + 2 summaries)
            cost_per_call = (
                (scenario["input_tokens"] * 0.000005) +
                (scenario["output_tokens"] * 0.000015) +
                (200 * 0.000005 + 100 * 0.000015) * 2  # 2 summaries
            )
            total_cost = cost_per_call * scenario["count"]

            print(f"\n{scenario['name']}:")
            print(f"  - Tokens per call: {scenario['input_tokens'] + scenario['output_tokens']}")
            print(f"  - Cost per call: ${cost_per_call:.6f}")
            print(f"  - Total items: {scenario['count']}")
            print(f"  - Total cost: ${total_cost:.2f}")
            if scenario["count"] > 1:
                print(f"  - Cost per item: ${total_cost/scenario['count']:.6f}")

    def test_database_operation_performance(
        self,
        test_session: Session,
        large_news_batch,
    ):
        """Benchmark database operations."""
        import time

        # Test 1: Query raw news by status
        start = time.time()
        result = test_session.query(RawNews).filter(RawNews.status == "raw").all()
        query_time = time.time() - start

        print(f"\n\nDatabase Performance:")
        print(f"  - Query 50 raw news items: {query_time*1000:.2f}ms")
        assert len(result) >= 50

        # Test 2: Batch add/commit
        test_batch = []
        for i in range(100):
            news = RawNews(
                source_id=1,  # Assume exists
                title=f"DB Test {i}",
                url=f"https://example.com/db-test/{i}",
                hash=f"db_test_{i}",
                published_at=datetime.now(),
                fetched_at=datetime.now(),
                status="raw",
            )
            test_batch.append(news)

        start = time.time()
        test_session.add_all(test_batch)
        test_session.commit()
        insert_time = time.time() - start

        print(f"  - Insert 100 items: {insert_time*1000:.2f}ms")
