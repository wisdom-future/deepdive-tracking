"""AI scoring service for news articles."""

import json
import logging
import time
from typing import Optional, Tuple
from datetime import datetime

from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from sqlalchemy.orm import Session

from src.models import RawNews, ProcessedNews, CostLog
from src.services.ai.models import (
    ScoringResponse,
    SummaryResponse,
    ProcessingMetadata,
    FullScoringResult,
)
from src.services.ai.prompt_templates import (
    get_scoring_prompt,
    get_summary_prompt,
    SCORING_SYSTEM_PROMPT,
)
from src.config.settings import Settings
from src.utils.api_response import strip_markdown_code_blocks

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for AI-powered news scoring and classification."""

    def __init__(self, settings: Settings, db_session: Optional[Session] = None):
        """Initialize scoring service.

        Args:
            settings: Application settings containing AI provider config
            db_session: SQLAlchemy session for database operations
        """
        self.settings = settings
        self.db_session = db_session

        # Select AI provider based on configuration
        self.provider = settings.ai_provider.lower()
        self.logger = logger

        # Initialize BOTH providers for automatic fallback
        # Primary provider (Grok or OpenAI)
        if self.provider == "grok":
            # Initialize Grok (xAI) client - uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=settings.xai_api_key,
                base_url=settings.xai_base_url
            )
            self.model = settings.xai_model
            self.provider_name = "grok"

            # Initialize OpenAI as fallback
            self.fallback_client = OpenAI(api_key=settings.openai_api_key)
            self.fallback_model = settings.openai_model
            self.fallback_provider_name = "openai"

            if self.logger:
                self.logger.info(f"Initialized Grok scoring service with model {self.model}")
                self.logger.info(f"OpenAI fallback available with model {self.fallback_model}")
        else:
            # Default to OpenAI (no fallback needed)
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_model
            self.provider_name = "openai"
            self.fallback_client = None
            self.fallback_model = None
            self.fallback_provider_name = None

            if self.logger:
                self.logger.info(f"Initialized OpenAI scoring service with model {self.model}")

    async def score_news(self, raw_news: RawNews) -> FullScoringResult:
        """Score and classify a single news item.

        Args:
            raw_news: Raw news article to score

        Returns:
            Complete scoring result including summaries and metadata

        Raises:
            ValueError: If API call fails after retries
            APIError: If OpenAI API returns error
        """
        import asyncio

        start_time = time.time()
        costs = {}

        try:
            # Step 1: Score and classify
            self.logger.info(f"Scoring news {raw_news.id}: {raw_news.title}")
            scoring, score_cost = await self._call_scoring_api(raw_news)
            costs["scoring"] = score_cost

            # Steps 2-5: Generate bilingual summaries (4 versions) in parallel
            self.logger.info(
                f"Generating bilingual summaries for {raw_news.id} "
                "(professional/scientific × Chinese/English)"
            )

            # Parallelize all 4 summary generations
            summary_results = await asyncio.gather(
                self._generate_summary(raw_news, scoring, version="professional"),
                self._generate_summary(raw_news, scoring, version="scientific"),
                self._generate_summary(raw_news, scoring, version="professional_en"),
                self._generate_summary(raw_news, scoring, version="scientific_en"),
                return_exceptions=False,
            )

            summary_pro, summary_pro_cost = summary_results[0]
            summary_sci, summary_sci_cost = summary_results[1]
            summary_pro_en, summary_pro_en_cost = summary_results[2]
            summary_sci_en, summary_sci_en_cost = summary_results[3]

            costs["summary_pro"] = summary_pro_cost
            costs["summary_sci"] = summary_sci_cost
            costs["summary_pro_en"] = summary_pro_en_cost
            costs["summary_sci_en"] = summary_sci_en_cost

            # Calculate total cost and quality score
            total_cost = sum(costs.values())
            processing_time = int((time.time() - start_time) * 1000)

            # Quality score: higher score = better quality
            quality_score = self._calculate_quality_score(scoring)

            result = FullScoringResult(
                raw_news_id=raw_news.id,
                scoring=scoring,
                summaries=SummaryResponse(
                    summary_pro=summary_pro,
                    summary_sci=summary_sci,
                    summary_pro_en=summary_pro_en,
                    summary_sci_en=summary_sci_en,
                ),
                metadata=ProcessingMetadata(
                    ai_models_used=[self.model],
                    processing_time_ms=processing_time,
                    cost=total_cost,
                    cost_breakdown=costs,
                ),
                quality_score=quality_score,
            )

            self.logger.info(
                f"Successfully scored news {raw_news.id}: score={scoring.score}, "
                f"cost=${total_cost:.4f}, time={processing_time}ms"
            )
            return result

        except (APIError, APIConnectionError, RateLimitError) as e:
            self.logger.error(f"API error while scoring {raw_news.id}: {str(e)}")
            raise ValueError(f"Failed to score news: {str(e)}") from e
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error for {raw_news.id}: {str(e)}")
            raise ValueError(f"Invalid API response format: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error scoring {raw_news.id}: {str(e)}")
            raise

    async def batch_score(
        self, raw_news_list: list[RawNews], skip_errors: bool = True
    ) -> Tuple[list[FullScoringResult], list[dict]]:
        """Score multiple news items.

        Args:
            raw_news_list: List of raw news to score
            skip_errors: Whether to skip failed items or raise error

        Returns:
            Tuple of (successful results, failed items with errors)
        """
        results = []
        errors = []

        for i, raw_news in enumerate(raw_news_list, 1):
            try:
                result = await self.score_news(raw_news)
                results.append(result)
                self.logger.info(f"[{i}/{len(raw_news_list)}] Scored: {raw_news.title}")

            except Exception as e:
                error_info = {
                    "raw_news_id": raw_news.id,
                    "title": raw_news.title,
                    "error": str(e),
                }
                errors.append(error_info)

                if skip_errors:
                    self.logger.warning(f"[{i}/{len(raw_news_list)}] Error scoring: {str(e)}")
                else:
                    raise

        self.logger.info(
            f"Batch scoring complete: {len(results)} successful, "
            f"{len(errors)} failed"
        )
        return results, errors

    async def save_to_database(
        self, raw_news: RawNews, scoring_result: FullScoringResult
    ) -> ProcessedNews:
        """Save scoring result to database.

        Args:
            raw_news: Original raw news
            scoring_result: Complete scoring result

        Returns:
            Saved ProcessedNews record

        Raises:
            ValueError: If database session not available
        """
        if not self.db_session:
            raise ValueError("Database session not configured")

        try:
            # Create ProcessedNews record
            processed_news = ProcessedNews(
                raw_news_id=raw_news.id,
                score=scoring_result.scoring.score,
                score_breakdown={
                    "reasoning": scoring_result.scoring.score_reasoning,
                    "impact": scoring_result.scoring.impact_analysis,
                },
                category=scoring_result.scoring.category.value,
                sub_categories=scoring_result.scoring.sub_categories,
                confidence=scoring_result.scoring.confidence,
                summary_pro=scoring_result.summaries.summary_pro,
                summary_sci=scoring_result.summaries.summary_sci,
                summary_pro_en=scoring_result.summaries.summary_pro_en,
                summary_sci_en=scoring_result.summaries.summary_sci_en,
                keywords=scoring_result.scoring.keywords,
                entities=scoring_result.scoring.entities.model_dump(),
                tech_terms=self._extract_tech_terms(
                    scoring_result.scoring.keywords
                ),
                company_mentions=scoring_result.scoring.entities.companies,
                infrastructure_tags=self._extract_infrastructure_tags(
                    scoring_result.scoring.category.value
                ),
                ai_models_used=scoring_result.metadata.ai_models_used,
                processing_time_ms=scoring_result.metadata.processing_time_ms,
                cost=scoring_result.metadata.cost,
                cost_breakdown=scoring_result.metadata.cost_breakdown,
                quality_score=scoring_result.quality_score,
                quality_notes=scoring_result.quality_notes,
                version=1,
            )

            self.db_session.add(processed_news)
            self.db_session.commit()

            # Log cost
            cost_log = CostLog(
                processed_news_id=processed_news.id,
                service=self.provider_name,  # Use dynamic provider name (openai or grok)
                operation="scoring_and_summarization",
                model=self.model,
                total_cost=scoring_result.metadata.cost,
                extra_metadata=scoring_result.metadata.cost_breakdown,
            )
            self.db_session.add(cost_log)
            self.db_session.commit()

            # Update raw news status
            raw_news.status = "processed"
            self.db_session.commit()

            self.logger.info(
                f"Saved processed news {processed_news.id} "
                f"for raw_news {raw_news.id}"
            )
            return processed_news

        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"Failed to save to database: {str(e)}")
            raise

    # Private methods

    async def _call_scoring_api(self, raw_news: RawNews) -> Tuple[ScoringResponse, float]:
        """Call AI API for scoring and classification with automatic fallback.

        Args:
            raw_news: Raw news to score

        Returns:
            Tuple of (ScoringResponse, API cost)
        """
        prompt = get_scoring_prompt(raw_news.title, raw_news.content or "")

        # Try primary provider first
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SCORING_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            # Parse response
            response_text = response.choices[0].message.content

            # Add debug logging to help troubleshoot API response issues
            self.logger.debug(f"Raw API response: {repr(response_text[:500])}")

            if not response_text or not response_text.strip():
                raise ValueError("API returned empty response")

            # Strip markdown code blocks if present
            response_text = strip_markdown_code_blocks(response_text)

            response_json = json.loads(response_text)

            # Calculate cost (rough estimate)
            # GPT-4o: ~$0.005 per 1K input tokens, ~$0.015 per 1K output tokens
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 0.000005 + output_tokens * 0.000015)

            scoring = ScoringResponse(**response_json)
            return scoring, cost

        except (APIError, APIConnectionError, RateLimitError) as e:
            error_msg = str(e)
            self.logger.warning(f"{self.provider_name} API error: {error_msg}")

            # Try fallback to OpenAI if available
            if self.fallback_client:
                self.logger.warning(f"Attempting fallback to {self.fallback_provider_name}...")
                try:
                    response = self.fallback_client.chat.completions.create(
                        model=self.fallback_model,
                        messages=[
                            {"role": "system", "content": SCORING_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.7,
                        max_tokens=1000,
                    )

                    response_text = response.choices[0].message.content
                    response_text = strip_markdown_code_blocks(response_text)
                    response_json = json.loads(response_text)

                    input_tokens = response.usage.prompt_tokens
                    output_tokens = response.usage.completion_tokens
                    cost = (input_tokens * 0.000005 + output_tokens * 0.000015)

                    scoring = ScoringResponse(**response_json)
                    self.logger.info(f"✅ Fallback to {self.fallback_provider_name} successful")
                    return scoring, cost

                except Exception as fallback_error:
                    self.logger.error(f"Fallback to {self.fallback_provider_name} also failed: {str(fallback_error)}")
                    raise ValueError(f"Both {self.provider_name} and {self.fallback_provider_name} failed") from fallback_error
            else:
                # No fallback available
                raise ValueError(f"{self.provider_name} API error: {error_msg}") from e

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in API response: {str(e)}")
            self.logger.error(f"Response text was: {repr(response_text[:500])}")
            raise ValueError(f"API returned invalid JSON: {str(e)}") from e

    async def _generate_summary(
        self, raw_news: RawNews, scoring: ScoringResponse, version: str
    ) -> Tuple[str, float]:
        """Generate summary for the news.

        Args:
            raw_news: Raw news article
            scoring: Scoring result
            version: "professional", "scientific", "professional_en", or "scientific_en"

        Returns:
            Tuple of (summary text, API cost)
        """
        prompts = get_summary_prompt(
            raw_news.title,
            raw_news.content or "",
            scoring.score,
            scoring.category.value,
            scoring.key_points,
        )

        prompt = prompts[version]

        # Choose system prompt based on language
        if version.endswith("_en"):
            system_prompt = (
                "You are a professional summary writer who can generate "
                "high-quality summaries for different audiences in English."
            )
        else:
            system_prompt = (
                "你是一个专业的摘要写手，能够为不同受众生成高质量的摘要。"
            )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=300,
            )

            response_text = response.choices[0].message.content

            # Strip markdown code blocks if present
            response_text_clean = strip_markdown_code_blocks(response_text)

            response_json = json.loads(response_text_clean)

            # Build expected key: summary_pro, summary_sci, summary_pro_en, summary_sci_en
            if version == "professional":
                summary_key = "summary_pro"
            elif version == "scientific":
                summary_key = "summary_sci"
            elif version == "professional_en":
                summary_key = "summary_pro_en"
            elif version == "scientific_en":
                summary_key = "summary_sci_en"
            else:
                summary_key = f"summary_{version[:3]}"

            summary = response_json.get(summary_key, response_text_clean)

            # Validate summary content
            if not summary or len(str(summary).strip()) < 10:
                self.logger.warning(f"Summary for {version} is too short, using fallback")
                summary = response_text_clean if response_text_clean else "Summary generation failed"

            # Calculate cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 0.000005 + output_tokens * 0.000015)

            return summary, cost

        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"JSON parse error for {version}: {str(e)}")
            self.logger.warning(f"Raw response: {response_text[:200] if 'response_text' in locals() else 'N/A'}...")

            # Try to extract meaningful content from raw response
            if 'response_text' in locals():
                # If response looks like JSON but failed parsing, return it as-is
                if response_text.startswith('{') or response_text.startswith('['):
                    self.logger.warning(f"Response looks like JSON but parsing failed")
                    return response_text, 0.005

                # If response is plain text, use it as summary
                if len(response_text.strip()) > 10:
                    self.logger.warning(f"Using plain text response as fallback summary")
                    return response_text, 0.005

            # Last resort: generate a fallback summary
            self.logger.error(f"Could not extract summary from response for {version}")
            return f"Summary generation failed for {version}", 0.005

        except (APIError, APIConnectionError, RateLimitError) as e:
            self.logger.error(f"API error while generating summary for {version}: {str(e)}")
            return f"API error: {str(e)[:100]}", 0.005

        except Exception as e:
            self.logger.error(f"Unexpected error generating summary for {version}: {str(e)}")
            return f"Error: {str(e)[:100]}", 0.005

    @staticmethod
    def _calculate_quality_score(scoring: ScoringResponse) -> float:
        """Calculate quality score of the scoring result.

        Args:
            scoring: Scoring response

        Returns:
            Quality score from 0 to 1
        """
        # Quality score based on:
        # 1. Confidence in classification
        # 2. Completeness of entities
        # 3. Keyword extraction quality
        entity_completeness = (
            (len(scoring.entities.companies) +
             len(scoring.entities.technologies) +
             len(scoring.entities.people)) / 10
        )
        entity_completeness = min(entity_completeness, 1.0)

        keyword_quality = len(scoring.keywords) / 8  # Target 8 keywords

        quality = (
            scoring.confidence * 0.6 +
            entity_completeness * 0.2 +
            keyword_quality * 0.2
        )

        return min(quality, 1.0)

    @staticmethod
    def _extract_tech_terms(keywords: list[str]) -> dict:
        """Extract technology terms from keywords.

        Args:
            keywords: List of keywords

        Returns:
            Dictionary of tech terms
        """
        tech_keywords = [kw for kw in keywords if len(kw) > 2]
        return {
            "terms": tech_keywords[:5],
            "count": len(tech_keywords),
        }

    @staticmethod
    def _extract_infrastructure_tags(category: str) -> list[str]:
        """Extract infrastructure-related tags.

        Args:
            category: News category

        Returns:
            List of infrastructure tags
        """
        infrastructure_categories = {
            "infrastructure": ["compute", "storage", "networking"],
            "applications": ["deployment", "integration"],
            "policy": ["compliance", "privacy"],
        }
        return infrastructure_categories.get(category, [])
