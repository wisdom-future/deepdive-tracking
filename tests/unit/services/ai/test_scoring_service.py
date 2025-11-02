"""Tests for AI scoring service."""

import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

import pytest
from sqlalchemy.orm import Session

from src.services.ai import (
    ScoringService,
    ScoringResponse,
    CategoryEnum,
)
from src.models import RawNews, ProcessedNews, DataSource


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Mock()
    settings.openai_api_key = "test-key"
    settings.openai_model = "gpt-4o"
    return settings


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = Mock(spec=Session)
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def mock_raw_news():
    """Create mock raw news."""
    news = Mock(spec=RawNews)
    news.id = 1
    news.title = "OpenAI releases GPT-4o"
    news.content = (
        "OpenAI today announced GPT-4o, a new AI model with improved capabilities. "
        "The model features multimodal understanding and is 50% faster than GPT-4."
    )
    news.url = "https://openai.com/blog/gpt-4o"
    news.source_id = 1
    news.status = "raw"
    return news


@pytest.fixture
def scoring_service(mock_settings, mock_db_session):
    """Create scoring service with mocked dependencies."""
    with patch("src.services.ai.scoring_service.OpenAI"):
        service = ScoringService(mock_settings, mock_db_session)
        service.client = Mock()
        return service


class TestScoringService:
    """Test ScoringService class."""

    @pytest.mark.asyncio
    async def test_score_news_success(self, scoring_service, mock_raw_news):
        """Test successful news scoring."""
        # Mock API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 85,
            "score_reasoning": "GPT-4o is a major breakthrough",
            "category": "tech_breakthrough",
            "sub_categories": ["model_release"],
            "confidence": 0.95,
            "key_points": [
                "Multimodal capabilities",
                "50% faster than GPT-4",
                "Lower cost"
            ],
            "keywords": ["GPT-4o", "OpenAI", "AI", "Model"],
            "entities": {
                "companies": ["OpenAI"],
                "technologies": ["GPT-4o", "Transformer"],
                "people": ["Sam Altman"]
            },
            "impact_analysis": "Will significantly impact AI industry"
        })
        mock_response.usage.prompt_tokens = 500
        mock_response.usage.completion_tokens = 300

        scoring_service.client.chat.completions.create.return_value = mock_response

        # Execute
        result = await scoring_service.score_news(mock_raw_news)

        # Verify
        assert result.scoring.score == 85
        assert result.scoring.category == CategoryEnum.TECH_BREAKTHROUGH
        assert result.scoring.confidence == 0.95
        assert len(result.scoring.key_points) == 3
        assert result.metadata.cost > 0
        assert result.metadata.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_score_news_invalid_json(self, scoring_service, mock_raw_news):
        """Test scoring with invalid API response."""
        # Mock API response with invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON"

        scoring_service.client.chat.completions.create.return_value = mock_response

        # Execute and verify exception
        with pytest.raises(ValueError, match="Invalid API response format"):
            await scoring_service.score_news(mock_raw_news)

    @pytest.mark.asyncio
    async def test_batch_score(self, scoring_service, mock_raw_news):
        """Test batch scoring of multiple articles."""
        # Create multiple mock news
        news_list = [mock_raw_news] * 3

        # Mock scoring for each
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 75,
            "score_reasoning": "Important news",
            "category": "company_news",
            "sub_categories": [],
            "confidence": 0.8,
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "keywords": ["tech", "news", "ai", "model"],
            "entities": {
                "companies": ["Company"],
                "technologies": ["Tech"],
                "people": []
            },
            "impact_analysis": "Some impact"
        })
        mock_response.usage.prompt_tokens = 400
        mock_response.usage.completion_tokens = 200

        scoring_service.client.chat.completions.create.return_value = mock_response

        # Execute
        results, errors = await scoring_service.batch_score(news_list)

        # Verify
        assert len(results) == 3
        assert len(errors) == 0
        assert all(r.scoring.score == 75 for r in results)

    @pytest.mark.asyncio
    async def test_batch_score_with_errors(self, scoring_service, mock_raw_news):
        """Test batch scoring with some failures."""
        news_list = [mock_raw_news] * 2

        # Mock first call fails, second succeeds
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 80,
            "score_reasoning": "Good",
            "category": "applications",
            "sub_categories": [],
            "confidence": 0.85,
            "key_points": ["P1", "P2", "P3"],
            "keywords": ["a", "b", "c", "d"],
            "entities": {
                "companies": [],
                "technologies": [],
                "people": []
            },
            "impact_analysis": "Impact"
        })
        mock_response.usage.prompt_tokens = 300
        mock_response.usage.completion_tokens = 150

        # First call raises error, second succeeds
        scoring_service.client.chat.completions.create.side_effect = [
            Exception("API Error"),
            mock_response
        ]

        # Execute
        results, errors = await scoring_service.batch_score(
            news_list, skip_errors=True
        )

        # Verify
        assert len(results) == 1
        assert len(errors) == 1
        assert errors[0]["error"] == "API Error"

    def test_save_to_database(
        self, scoring_service, mock_raw_news, mock_db_session
    ):
        """Test saving scoring result to database."""
        # Create a valid scoring result
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 90,
            "score_reasoning": "Major breakthrough",
            "category": "tech_breakthrough",
            "sub_categories": [],
            "confidence": 0.92,
            "key_points": ["K1", "K2", "K3"],
            "keywords": ["kw1", "kw2", "kw3", "kw4"],
            "entities": {
                "companies": ["OpenAI"],
                "technologies": ["GPT-4o"],
                "people": []
            },
            "impact_analysis": "Significant"
        })
        mock_response.usage.prompt_tokens = 500
        mock_response.usage.completion_tokens = 300

        scoring_service.client.chat.completions.create.return_value = mock_response

        # Create scoring result
        import asyncio
        result = asyncio.run(scoring_service.score_news(mock_raw_news))

        # Save to database
        processed = scoring_service.save_to_database(mock_raw_news, result)

        # Verify database calls
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
        assert mock_raw_news.status == "processed"

    def test_calculate_quality_score(self, scoring_service):
        """Test quality score calculation."""
        # Create mock scoring response
        mock_scoring = Mock(spec=ScoringResponse)
        mock_scoring.confidence = 0.9
        mock_scoring.entities = Mock()
        mock_scoring.entities.companies = ["Company1", "Company2"]
        mock_scoring.entities.technologies = ["Tech1", "Tech2", "Tech3"]
        mock_scoring.entities.people = ["Person1"]
        mock_scoring.keywords = ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6", "kw7", "kw8"]

        # Calculate quality score
        quality = ScoringService._calculate_quality_score(mock_scoring)

        # Verify
        assert 0 <= quality <= 1
        assert quality > 0.8  # Should be high with good confidence and entities

    def test_extract_tech_terms(self, scoring_service):
        """Test technology terms extraction."""
        keywords = ["Python", "ML", "AI", "NLP", "Transformer"]

        terms = ScoringService._extract_tech_terms(keywords)

        assert "terms" in terms
        assert "count" in terms
        assert len(terms["terms"]) <= 5

    def test_extract_infrastructure_tags(self, scoring_service):
        """Test infrastructure tags extraction."""
        # Test for infrastructure category
        tags = ScoringService._extract_infrastructure_tags("infrastructure")
        assert "compute" in tags or "storage" in tags

        # Test for policy category
        tags = ScoringService._extract_infrastructure_tags("policy")
        assert "compliance" in tags or "privacy" in tags

        # Test for unknown category
        tags = ScoringService._extract_infrastructure_tags("unknown")
        assert len(tags) == 0


class TestPromptTemplates:
    """Test prompt template generation."""

    def test_get_scoring_prompt(self):
        """Test scoring prompt generation."""
        from src.services.ai.prompt_templates import get_scoring_prompt

        prompt = get_scoring_prompt(
            title="Test Title",
            content="Test content here"
        )

        assert "Test Title" in prompt
        assert "Test content here" in prompt
        assert "评分规则" in prompt
        assert "分类规则" in prompt
        assert "JSON" in prompt

    def test_get_summary_prompts(self):
        """Test summary prompt generation."""
        from src.services.ai.prompt_templates import get_summary_prompt

        prompts = get_summary_prompt(
            title="Test Title",
            content="Test content",
            score=80,
            category="tech_breakthrough",
            key_points=["Point 1", "Point 2"]
        )

        assert "professional" in prompts
        assert "scientific" in prompts
        assert len(prompts["professional"]) > 0
        assert len(prompts["scientific"]) > 0


class TestScoringResponse:
    """Test ScoringResponse model."""

    def test_scoring_response_validation(self):
        """Test ScoringResponse Pydantic validation."""
        from src.services.ai.models import EntityInfo

        response_data = {
            "score": 85,
            "score_reasoning": "Good article",
            "category": "tech_breakthrough",
            "sub_categories": [],
            "confidence": 0.95,
            "key_points": ["P1", "P2", "P3"],
            "keywords": ["k1", "k2", "k3", "k4"],
            "entities": {
                "companies": ["OpenAI"],
                "technologies": ["GPT"],
                "people": []
            },
            "impact_analysis": "Significant impact"
        }

        response = ScoringResponse(**response_data)

        assert response.score == 85
        assert response.category == CategoryEnum.TECH_BREAKTHROUGH
        assert response.confidence == 0.95

    def test_scoring_response_invalid_score(self):
        """Test ScoringResponse with invalid score."""
        from pydantic import ValidationError

        response_data = {
            "score": 150,  # Invalid - should be 0-100
            "score_reasoning": "Test",
            "category": "company_news",
            "confidence": 0.9,
            "key_points": ["P1", "P2", "P3"],
            "keywords": ["k1", "k2", "k3", "k4"],
            "entities": {"companies": [], "technologies": [], "people": []},
            "impact_analysis": "Test"
        }

        with pytest.raises(ValidationError):
            ScoringResponse(**response_data)
