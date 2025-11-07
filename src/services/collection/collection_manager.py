"""Collection manager - coordinates all data collectors."""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models import DataSource, RawNews
from src.services.collection.base_collector import BaseCollector
from src.services.collection.rss_collector import RSSCollector
from src.services.collection.twitter_collector import TwitterCollector
from src.services.collection.crawler_collector import CrawlerCollector
from src.services.collection.deduplication import ContentDeduplicator

logger = logging.getLogger(__name__)


class CollectionManager:
    """Manages data collection from all configured sources."""

    def __init__(self, db_session: Session):
        """Initialize collection manager.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.logger = logger
        self.deduplicator = ContentDeduplicator()

    async def collect_all(self) -> Dict[str, Any]:
        """Collect data from all enabled sources.

        Returns:
            Dictionary with collection statistics:
            - total_collected: Total items collected
            - total_new: New items (after dedup)
            - total_duplicates: Duplicate items
            - errors: List of errors occurred
            - by_source: Stats per source
        """
        # Fetch all enabled sources
        sources = self.db.query(DataSource).filter(DataSource.is_enabled == True).order_by(DataSource.priority).all()

        if not sources:
            self.logger.warning("No enabled data sources found")
            return {
                "total_collected": 0,
                "total_new": 0,
                "total_duplicates": 0,
                "errors": ["No enabled sources"],
                "by_source": {},
            }

        # Collect from all sources concurrently
        tasks = [self._collect_from_source(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        stats = {
            "total_collected": 0,
            "total_new": 0,
            "total_duplicates": 0,
            "errors": [],
            "by_source": {},
        }

        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                stats["errors"].append(f"{source.name}: {str(result)}")
                stats["by_source"][source.name] = {"status": "error", "error": str(result)}
            else:
                collected, new, duplicates = result
                stats["total_collected"] += collected
                stats["total_new"] += new
                stats["total_duplicates"] += duplicates
                stats["by_source"][source.name] = {
                    "collected": collected,
                    "new": new,
                    "duplicates": duplicates,
                }
                self.logger.info(
                    f"Collection from {source.name}: {collected} collected, {new} new, {duplicates} duplicates"
                )

        return stats

    async def _collect_from_source(self, source: DataSource) -> Tuple[int, int, int]:
        """Collect data from a single source.

        Args:
            source: DataSource instance

        Returns:
            Tuple of (total_collected, new_items, duplicates)
        """
        collector = self._get_collector(source)
        if not collector:
            raise ValueError(f"No collector available for source type: {source.type}")

        # Collect articles
        articles = await collector.collect()
        total_collected = len(articles)

        # Check for duplicates and save new items
        new_count = 0
        duplicate_count = 0

        # Content quality statistics
        content_stats = {
            "rss": 0,  # Content from RSS feed
            "fetched": 0,  # Content fetched from source URL
            "total_content_length": 0,
            "min_length": float('inf'),
            "max_length": 0,
        }

        for article in articles:
            # Generate both URL/title hash and content simhash
            url_title_hash = self.deduplicator.compute_url_title_hash(
                article["title"], article["url"]
            )
            content_simhash = self.deduplicator.compute_simhash(
                article.get("content", "")
            )

            # 1. Check for exact match on URL/title
            existing_exact = self.db.query(RawNews).filter(
                RawNews.hash == url_title_hash
            ).first()

            if existing_exact:
                duplicate_count += 1
                self.logger.debug(
                    f"Duplicate found (exact): {article['title']} (id: {existing_exact.id})"
                )
                continue  # Skip this article, don't save it

            # 2. Check for similar content (only if content exists and simhash is valid)
            if content_simhash and article.get("content"):
                similar_items = self._find_similar_content(content_simhash, hamming_threshold=3)
                if similar_items:
                    duplicate_count += 1
                    self.logger.debug(
                        f"Duplicate found (similar content): {article['title']} "
                        f"(similar to id: {similar_items[0].id})"
                    )
                    continue  # Skip this article, don't save it

            # Only save non-duplicate articles
            raw_news = RawNews(
                source_id=source.id,
                title=article["title"],
                url=article["url"],
                content=article.get("content"),
                html_content=article.get("html_content"),
                language=article.get("language", "en"),
                hash=url_title_hash,
                content_simhash=content_simhash,  # Store simhash
                author=article.get("author"),
                source_name=source.name,
                published_at=article["published_at"],
                fetched_at=datetime.now(article["published_at"].tzinfo),
                status="raw",
                is_duplicate=False,  # Always False here (duplicates are skipped)
            )

            self.db.add(raw_news)
            new_count += 1

            # Track content quality statistics
            content = article.get("content", "")
            content_length = len(content)
            content_stats["total_content_length"] += content_length
            content_stats["min_length"] = min(content_stats["min_length"], content_length)
            content_stats["max_length"] = max(content_stats["max_length"], content_length)

            # Track content source (for RSS sources)
            if article.get("content_source") == "rss":
                content_stats["rss"] += 1
            elif article.get("content_source") == "fetched":
                content_stats["fetched"] += 1

        # Commit all new items
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        # Update source stats
        source.last_check_at = datetime.now()
        source.last_success_at = datetime.now() if new_count > 0 or duplicate_count > 0 else source.last_success_at
        source.error_count = 0
        source.consecutive_failures = 0
        self.db.commit()

        # Log content quality statistics
        if new_count > 0:
            avg_length = content_stats["total_content_length"] // new_count
            self.logger.info(
                f"Content quality for {source.name}: "
                f"RSS={content_stats['rss']}, "
                f"Fetched={content_stats['fetched']}, "
                f"AvgLength={avg_length}, "
                f"MinLength={content_stats['min_length']}, "
                f"MaxLength={content_stats['max_length']}"
            )

        return total_collected, new_count, duplicate_count

    def _find_similar_content(
        self,
        simhash: int,
        hamming_threshold: int = 3,
        time_window_days: int = 7
    ) -> List[RawNews]:
        """
        Find similar content based on Simhash Hamming distance.

        Args:
            simhash: Content simhash to check
            hamming_threshold: Maximum Hamming distance to consider similar (default 3)
            time_window_days: Only check records within recent N days (default 7)

        Returns:
            List of similar RawNews records

        Notes:
            - Hamming distance = number of differing bits in two simhashes
            - Distance <= 3 indicates high similarity (typically same content)
            - Time window optimization reduces query scope for performance
        """
        # Calculate time threshold
        time_threshold = datetime.now(timezone.utc) - timedelta(days=time_window_days)

        # Query recent records with valid simhash
        recent_items = self.db.query(RawNews).filter(
            RawNews.content_simhash.isnot(None),
            RawNews.fetched_at >= time_threshold
        ).all()

        # Calculate Hamming distance for each item
        similar_items = []
        for item in recent_items:
            if item.content_simhash:
                # XOR to find differing bits, count them
                hamming_distance = bin(simhash ^ item.content_simhash).count('1')
                if hamming_distance <= hamming_threshold:
                    similar_items.append(item)

        return similar_items

    def _get_collector(self, source: DataSource) -> Optional[BaseCollector]:
        """Get appropriate collector for source type.

        Args:
            source: DataSource instance

        Returns:
            Collector instance or None if type not supported
        """
        collectors = {
            "rss": RSSCollector,
            "twitter": TwitterCollector,
            "crawler": CrawlerCollector,
        }

        collector_class = collectors.get(source.type)
        if collector_class:
            return collector_class(source)

        if source.type == "api":
            # TODO: Implement API collector
            self.logger.warning(f"API collector not yet implemented for {source.name}")
            return None

        self.logger.warning(f"Unknown source type: {source.type}")
        return None

    @staticmethod
    def _generate_hash(title: str, url: str) -> str:
        """Generate hash for deduplication.

        Args:
            title: Article title
            url: Article URL

        Returns:
            SHA256 hash
        """
        content = f"{title}|{url}".lower().strip()
        return hashlib.sha256(content.encode()).hexdigest()

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get current collection statistics.

        Returns:
            Dictionary with stats:
            - total_raw_news: Total raw news in database
            - total_duplicates: Items marked as duplicates
            - by_source: Stats per source
            - last_collection_times: Last successful collection per source
        """
        stats = {
            "total_raw_news": self.db.query(func.count(RawNews.id)).scalar(),
            "total_duplicates": self.db.query(func.count(RawNews.id)).filter(RawNews.is_duplicate == True).scalar(),
            "by_source": {},
            "last_collection_times": {},
        }

        sources = self.db.query(DataSource).all()
        for source in sources:
            raw_count = self.db.query(func.count(RawNews.id)).filter(RawNews.source_id == source.id).scalar()
            dup_count = (
                self.db.query(func.count(RawNews.id))
                .filter(RawNews.source_id == source.id, RawNews.is_duplicate == True)
                .scalar()
            )
            stats["by_source"][source.name] = {
                "total": raw_count,
                "duplicates": dup_count,
                "enabled": source.is_enabled,
            }
            if source.last_success_at:
                stats["last_collection_times"][source.name] = source.last_success_at.isoformat()

        return stats
