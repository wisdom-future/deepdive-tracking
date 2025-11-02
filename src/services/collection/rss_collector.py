"""RSS feed collector implementation."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import feedparser
import aiohttp
from pytz import UTC

from src.models import DataSource, RawNews
from src.services.collection.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class RSSCollector(BaseCollector):
    """Collector for RSS feeds."""

    async def collect(self) -> List[Dict[str, Any]]:
        """Collect articles from RSS feed.

        Returns:
            List of raw news dictionaries
        """
        if not self.data_source.url:
            raise ValueError(f"RSS feed URL not configured for {self.data_source.name}")

        try:
            feed_data = await self._fetch_feed(self.data_source.url)
            articles = await self._parse_feed(feed_data)
            self.log_collection_attempt(True, f"Collected {len(articles)} articles")
            return articles
        except Exception as e:
            self.log_collection_attempt(False, str(e), e)
            raise

    async def _fetch_feed(self, url: str) -> str:
        """Fetch RSS feed content.

        Args:
            url: Feed URL

        Returns:
            Feed XML content as string
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"User-Agent": "DeepDive Tracking RSS Collector"},
            ) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to fetch feed: HTTP {response.status}")
                return await response.text()

    async def _parse_feed(self, feed_content: str) -> List[Dict[str, Any]]:
        """Parse RSS feed content.

        Args:
            feed_content: Raw RSS XML content

        Returns:
            List of parsed articles
        """
        # Parse in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        parsed = await loop.run_in_executor(None, lambda: feedparser.parse(feed_content))

        articles = []
        max_items = self.data_source.max_items_per_run or 50

        for entry in parsed.entries[:max_items]:
            try:
                article = {
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "content": entry.get("summary", ""),
                    "author": entry.get("author", ""),
                    "published_at": self._parse_published_date(entry),
                    "language": "en",
                    "html_content": None,
                }

                # Validate required fields
                if not article["title"] or not article["url"]:
                    self.logger.warning(f"Skipping entry with missing title or URL: {entry}")
                    continue

                articles.append(article)

            except Exception as e:
                self.logger.warning(f"Failed to parse RSS entry: {e}")
                continue

        return articles

    @staticmethod
    def _parse_published_date(entry: Dict[str, Any]) -> datetime:
        """Parse published date from RSS entry.

        Args:
            entry: Parsed RSS entry

        Returns:
            datetime object (UTC)
        """
        # Try different date fields
        date_tuple = None

        if hasattr(entry, "published_parsed") and entry.get("published_parsed"):
            date_tuple = entry.published_parsed
        elif hasattr(entry, "updated_parsed") and entry.get("updated_parsed"):
            date_tuple = entry.updated_parsed

        if date_tuple:
            return datetime(*date_tuple[:6]).replace(tzinfo=UTC)

        # Fallback to current time if date not found
        return datetime.now(UTC)
