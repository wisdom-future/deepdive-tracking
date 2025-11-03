"""Data models for AI scoring service."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class CategoryEnum(str, Enum):
    """8 major news categories."""

    COMPANY_NEWS = "company_news"
    TECH_BREAKTHROUGH = "tech_breakthrough"
    APPLICATIONS = "applications"
    INFRASTRUCTURE = "infrastructure"
    POLICY = "policy"
    MARKET_TRENDS = "market_trends"
    EXPERT_OPINIONS = "expert_opinions"
    LEARNING_RESOURCES = "learning_resources"


class EntityInfo(BaseModel):
    """Named entities extracted from news."""

    companies: List[str] = Field(default_factory=list, description="Company names mentioned")
    technologies: List[str] = Field(default_factory=list, description="Technology names")
    people: List[str] = Field(default_factory=list, description="Person names mentioned")


class ScoringResponse(BaseModel):
    """Response from AI scoring API."""

    score: int = Field(
        ge=0,
        le=100,
        description="Score from 0 to 100"
    )
    score_reasoning: str = Field(description="Explanation of the score")
    category: CategoryEnum = Field(description="Primary category")
    sub_categories: List[str] = Field(
        default_factory=list,
        max_length=3,
        description="Sub-categories (optional)"
    )
    confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence score from 0 to 1"
    )
    key_points: List[str] = Field(
        min_length=3,
        max_length=5,
        description="Key points from the article"
    )
    keywords: List[str] = Field(
        min_length=4,
        max_length=8,
        description="Keywords sorted by importance"
    )
    entities: EntityInfo = Field(description="Named entities")
    impact_analysis: str = Field(description="Impact analysis of the news")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "score": 85,
                "score_reasoning": "OpenAI GPT-4o的发布是AI领域的重大进展，具有广泛的影响力。",
                "category": "tech_breakthrough",
                "sub_categories": ["model_release", "capability_advancement"],
                "confidence": 0.95,
                "key_points": [
                    "GPT-4o是多模态模型，支持文本、语音和视觉处理",
                    "性能比GPT-4提升50%，成本降低50%",
                    "将加速AI在各行业的落地应用"
                ],
                "keywords": ["GPT-4o", "OpenAI", "多模态", "大语言模型", "AI能力"],
                "entities": {
                    "companies": ["OpenAI", "Google", "Anthropic"],
                    "technologies": ["GPT-4o", "多模态", "Transformer"],
                    "people": ["Sam Altman"]
                },
                "impact_analysis": "GPT-4o的发布将推动整个AI行业发展，促进更多应用落地。"
            }
        }


class SummaryRequest(BaseModel):
    """Request for summary generation."""

    title: str = Field(description="Article title")
    content: str = Field(description="Article content")
    score: int = Field(ge=0, le=100, description="Article score")
    category: str = Field(description="Article category")
    key_points: List[str] = Field(description="Key points from scoring")


class SummaryResponse(BaseModel):
    """Response from summary generation."""

    summary_pro: str = Field(
        min_length=100,
        max_length=1000,
        description="Professional summary for tech decision makers (Chinese)"
    )
    summary_sci: str = Field(
        min_length=100,
        max_length=1000,
        description="Scientific summary for general audience (Chinese)"
    )
    summary_pro_en: str = Field(
        min_length=100,
        max_length=1000,
        description="Professional summary for tech decision makers (English)"
    )
    summary_sci_en: str = Field(
        min_length=100,
        max_length=1000,
        description="Scientific summary for general audience (English)"
    )


class ProcessingMetadata(BaseModel):
    """Metadata about processing."""

    ai_models_used: List[str] = Field(default_factory=list, description="AI models used")
    processing_time_ms: int = Field(description="Processing time in milliseconds")
    cost: float = Field(description="API cost in USD")
    cost_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Cost breakdown by operation"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "ai_models_used": ["gpt-4o"],
                "processing_time_ms": 1250,
                "cost": 0.035,
                "cost_breakdown": {
                    "scoring": 0.025,
                    "summary_pro": 0.005,
                    "summary_sci": 0.005
                }
            }
        }


class FullScoringResult(BaseModel):
    """Complete result of scoring and summarization."""

    raw_news_id: int = Field(description="ID of the raw news")
    scoring: ScoringResponse = Field(description="Scoring result")
    summaries: SummaryResponse = Field(description="Summaries")
    metadata: ProcessingMetadata = Field(description="Processing metadata")
    quality_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Quality score of the processing result"
    )
    quality_notes: Optional[str] = Field(
        default=None,
        description="Notes about quality"
    )
