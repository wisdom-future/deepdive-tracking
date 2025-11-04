"""
Diversity-Aware Article Selector

消除来源偏向性，确保发布内容的多样性，同时保持高质量标准。

核心原则：
1. 质量优先：设置最低质量阈值
2. 来源归一化：消除系统性差异
3. 温和多样性：鼓励但不强制多样性
4. 完全透明：记录所有决策理由
"""

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import statistics

from src.models import ProcessedNews, RawNews

logger = logging.getLogger(__name__)


@dataclass
class ArticleCandidate:
    """Article candidate with selection metadata."""

    processed_news: ProcessedNews
    raw_news: RawNews

    # Scores
    raw_score: float
    normalized_score: float
    final_score: float

    # Source info
    source_name: str
    source_rank_in_source: int  # 在该来源中的排名

    # Selection metadata
    diversity_factor: float = 1.0
    quality_threshold_passed: bool = True
    selection_reason: str = ""


@dataclass
class SourceStats:
    """Statistical information for a source."""

    source_name: str
    article_count: int
    mean_score: float
    std_score: float
    min_score: float
    max_score: float


class DiversityAwareSelector:
    """
    Select top articles with diversity awareness.

    Balances quality and diversity by:
    1. Normalizing scores within each source (z-score)
    2. Applying gentle diversity weighting
    3. Maintaining minimum quality thresholds
    """

    # Configuration
    MIN_RAW_SCORE = 60.0  # 最低原始分数
    MIN_NORMALIZED_SCORE = -1.0  # 最低归一化分数（-1 = 低于平均1个标准差）
    DIVERSITY_DECAY = 0.85  # 多样性衰减因子（温和）
    MAX_PER_SOURCE = 4  # 单一来源最大文章数
    MIN_SOURCES_REQUIRED = 3  # 至少需要的不同来源数

    def __init__(self, session):
        """Initialize selector with database session."""
        self.session = session
        self.logger = logger

    def select_top_articles(
        self,
        limit: int = 10,
        min_raw_score: Optional[float] = None,
        diversity_decay: Optional[float] = None
    ) -> Tuple[List[ArticleCandidate], Dict]:
        """
        Select top articles with diversity awareness.

        Args:
            limit: Number of articles to select
            min_raw_score: Override minimum raw score
            diversity_decay: Override diversity decay factor

        Returns:
            Tuple of (selected articles, selection report)
        """
        min_raw_score = min_raw_score or self.MIN_RAW_SCORE
        diversity_decay = diversity_decay or self.DIVERSITY_DECAY

        self.logger.info(f"Starting diversity-aware selection (limit={limit})")
        self.logger.info(f"Parameters: min_raw_score={min_raw_score}, diversity_decay={diversity_decay}")

        # Step 1: Load all processed news with raw news
        candidates = self._load_candidates(min_raw_score)
        self.logger.info(f"Loaded {len(candidates)} candidates (raw_score >= {min_raw_score})")

        if len(candidates) < limit:
            self.logger.warning(
                f"Only {len(candidates)} candidates available, less than requested {limit}"
            )

        # Step 2: Calculate source statistics
        source_stats = self._calculate_source_stats(candidates)
        self._log_source_stats(source_stats)

        # Step 3: Normalize scores within each source
        self._normalize_scores(candidates, source_stats)

        # Step 4: Greedy selection with diversity weighting
        selected = self._greedy_select(
            candidates,
            limit,
            diversity_decay,
            min_normalized_score=self.MIN_NORMALIZED_SCORE
        )

        # Step 5: Generate selection report
        report = self._generate_report(selected, candidates, source_stats)

        self.logger.info(f"Selected {len(selected)} articles from {len(set(a.source_name for a in selected))} sources")

        return selected, report

    def _load_candidates(self, min_raw_score: float) -> List[ArticleCandidate]:
        """Load all candidate articles from database."""
        candidates = []

        # Query: processed_news JOIN raw_news, filter by score
        processed_list = (
            self.session.query(ProcessedNews)
            .filter(ProcessedNews.score >= min_raw_score)
            .all()
        )

        for processed in processed_list:
            raw = (
                self.session.query(RawNews)
                .filter(RawNews.id == processed.raw_news_id)
                .first()
            )

            if not raw:
                self.logger.warning(f"Raw news not found for processed_news_id={processed.id}")
                continue

            candidate = ArticleCandidate(
                processed_news=processed,
                raw_news=raw,
                raw_score=processed.score,
                normalized_score=0.0,  # Will be calculated later
                final_score=0.0,
                source_name=raw.source_name or "Unknown",
                source_rank_in_source=0,
                quality_threshold_passed=True
            )

            candidates.append(candidate)

        return candidates

    def _calculate_source_stats(
        self,
        candidates: List[ArticleCandidate]
    ) -> Dict[str, SourceStats]:
        """Calculate statistical information for each source."""
        source_groups = defaultdict(list)

        for candidate in candidates:
            source_groups[candidate.source_name].append(candidate.raw_score)

        stats = {}
        for source_name, scores in source_groups.items():
            if len(scores) == 0:
                continue

            mean_score = statistics.mean(scores)
            std_score = statistics.stdev(scores) if len(scores) > 1 else 0.0

            stats[source_name] = SourceStats(
                source_name=source_name,
                article_count=len(scores),
                mean_score=mean_score,
                std_score=std_score if std_score > 0 else 1.0,  # Avoid division by zero
                min_score=min(scores),
                max_score=max(scores)
            )

        return stats

    def _normalize_scores(
        self,
        candidates: List[ArticleCandidate],
        source_stats: Dict[str, SourceStats]
    ):
        """Normalize scores within each source using z-score."""
        for candidate in candidates:
            stats = source_stats.get(candidate.source_name)

            if not stats:
                candidate.normalized_score = 0.0
                continue

            # Z-score normalization
            z_score = (candidate.raw_score - stats.mean_score) / stats.std_score
            candidate.normalized_score = z_score

        # Rank within source
        source_groups = defaultdict(list)
        for candidate in candidates:
            source_groups[candidate.source_name].append(candidate)

        for source_name, source_candidates in source_groups.items():
            sorted_candidates = sorted(
                source_candidates,
                key=lambda c: c.raw_score,
                reverse=True
            )
            for rank, candidate in enumerate(sorted_candidates, 1):
                candidate.source_rank_in_source = rank

    def _greedy_select(
        self,
        candidates: List[ArticleCandidate],
        limit: int,
        diversity_decay: float,
        min_normalized_score: float
    ) -> List[ArticleCandidate]:
        """
        Greedy selection with diversity weighting.

        Algorithm:
        1. Filter candidates by minimum normalized score
        2. Sort by normalized score
        3. Iteratively select best candidate considering:
           - Normalized score
           - Diversity factor (penalize over-represented sources)
           - Maximum per-source limit
        """
        # Filter by minimum normalized score
        eligible = [
            c for c in candidates
            if c.normalized_score >= min_normalized_score
        ]

        self.logger.info(
            f"Filtered to {len(eligible)} eligible candidates "
            f"(normalized_score >= {min_normalized_score})"
        )

        if len(eligible) == 0:
            self.logger.error("No eligible candidates after filtering!")
            return []

        selected = []
        source_counts = defaultdict(int)

        while len(selected) < limit and len(eligible) > 0:
            # Calculate final score for each candidate
            for candidate in eligible:
                # Diversity factor: penalize sources that already have many articles
                count = source_counts[candidate.source_name]
                diversity_factor = diversity_decay ** count

                # Final score = normalized_score * diversity_factor
                candidate.final_score = candidate.normalized_score * diversity_factor
                candidate.diversity_factor = diversity_factor

            # Sort by final score
            eligible.sort(key=lambda c: c.final_score, reverse=True)

            # Select best candidate
            best = eligible[0]

            # Check if source has reached maximum
            if source_counts[best.source_name] >= self.MAX_PER_SOURCE:
                self.logger.debug(
                    f"Source {best.source_name} reached max limit "
                    f"({self.MAX_PER_SOURCE}), skipping"
                )
                eligible.remove(best)
                continue

            # Select this candidate
            best.selection_reason = (
                f"Rank #{len(selected) + 1}: "
                f"raw={best.raw_score:.1f}, "
                f"norm={best.normalized_score:.2f}, "
                f"div={best.diversity_factor:.2f}, "
                f"final={best.final_score:.2f}"
            )

            selected.append(best)
            source_counts[best.source_name] += 1
            eligible.remove(best)

            self.logger.debug(
                f"Selected: {best.raw_news.title[:50]}... "
                f"(source={best.source_name}, {best.selection_reason})"
            )

        return selected

    def _generate_report(
        self,
        selected: List[ArticleCandidate],
        all_candidates: List[ArticleCandidate],
        source_stats: Dict[str, SourceStats]
    ) -> Dict:
        """Generate comprehensive selection report."""
        # Source distribution
        source_dist = defaultdict(int)
        for article in selected:
            source_dist[article.source_name] += 1

        # Quality metrics
        selected_raw_scores = [a.raw_score for a in selected]
        selected_norm_scores = [a.normalized_score for a in selected]

        report = {
            "summary": {
                "total_candidates": len(all_candidates),
                "selected": len(selected),
                "unique_sources_in_candidates": len(source_stats),
                "unique_sources_in_selected": len(source_dist),
                "diversity_achieved": len(source_dist) >= self.MIN_SOURCES_REQUIRED
            },
            "source_distribution": dict(source_dist),
            "quality_metrics": {
                "raw_score_mean": statistics.mean(selected_raw_scores) if selected_raw_scores else 0,
                "raw_score_min": min(selected_raw_scores) if selected_raw_scores else 0,
                "raw_score_max": max(selected_raw_scores) if selected_raw_scores else 0,
                "normalized_score_mean": statistics.mean(selected_norm_scores) if selected_norm_scores else 0,
                "normalized_score_min": min(selected_norm_scores) if selected_norm_scores else 0,
                "normalized_score_max": max(selected_norm_scores) if selected_norm_scores else 0,
            },
            "source_stats": {
                name: {
                    "count": stats.article_count,
                    "mean": stats.mean_score,
                    "std": stats.std_score,
                    "range": f"{stats.min_score:.1f}-{stats.max_score:.1f}"
                }
                for name, stats in source_stats.items()
            },
            "selected_articles": [
                {
                    "title": a.raw_news.title,
                    "source": a.source_name,
                    "raw_score": a.raw_score,
                    "normalized_score": round(a.normalized_score, 2),
                    "final_score": round(a.final_score, 2),
                    "diversity_factor": round(a.diversity_factor, 2),
                    "reason": a.selection_reason
                }
                for a in selected
            ]
        }

        return report

    def _log_source_stats(self, source_stats: Dict[str, SourceStats]):
        """Log source statistics for transparency."""
        self.logger.info(f"Source statistics for {len(source_stats)} sources:")

        for source_name, stats in sorted(
            source_stats.items(),
            key=lambda x: x[1].mean_score,
            reverse=True
        ):
            self.logger.info(
                f"  {source_name:30} | "
                f"Count: {stats.article_count:3} | "
                f"Mean: {stats.mean_score:5.1f} | "
                f"Std: {stats.std_score:5.1f} | "
                f"Range: {stats.min_score:5.1f}-{stats.max_score:5.1f}"
            )
