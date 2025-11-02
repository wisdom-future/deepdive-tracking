"""RSS feed collector implementation."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import feedparser
import aiohttp
from pytz import UTC

try:
    from langdetect import detect, LangDetectException
except ImportError:
    # Fallback if langdetect not installed
    detect = None
    LangDetectException = Exception

from src.models import DataSource, RawNews
from src.services.collection.base_collector import BaseCollector
from src.utils.html_cleaner import HTMLCleaner

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
                # Extract content with fallback strategy
                content = self._extract_content(entry)

                # Detect language from content
                language = self._detect_language(content)

                # Extract author with multiple sources
                author = self._extract_author(entry)

                article = {
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "content": content,
                    "author": author,
                    "published_at": self._parse_published_date(entry),
                    "language": language,
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
    def _extract_content(entry: Dict[str, Any]) -> str:
        """Extract full article content with HTML cleaning.

        Tries multiple content sources with fallback strategy:
        1. content (Atom format - usually HTML)
        2. summary (RSS format - may contain HTML)
        3. description (RSS format - may contain HTML)

        All content is cleaned to remove HTML tags and convert to plain text.

        Args:
            entry: Parsed RSS entry from feedparser

        Returns:
            Cleaned article content string (plain text)
        """
        raw_content = ""

        # Try content (Atom format - highest priority)
        if "content" in entry and entry.content:
            content_list = entry.get("content", [])
            if content_list and isinstance(content_list, list):
                raw_content = content_list[0].get("value", "").strip()
                if raw_content:
                    return HTMLCleaner.clean(raw_content)

        # Try summary (RSS format - second priority)
        summary = entry.get("summary", "").strip()
        if summary:
            return HTMLCleaner.clean(summary)

        # Fallback to description
        description = entry.get("description", "").strip()
        if description:
            return HTMLCleaner.clean(description)

        # Return empty string if nothing found
        return ""

    def _extract_author(self, entry: Dict[str, Any]) -> str:
        """Extract author with fallback to data source default.

        Args:
            entry: Parsed RSS entry from feedparser

        Returns:
            Author name string, or empty string if not found
        """
        # Try direct author field
        author = entry.get("author", "").strip()
        if author:
            return author

        # Try author_detail object
        if "author_detail" in entry:
            author_detail = entry.get("author_detail", {})
            if isinstance(author_detail, dict):
                author = author_detail.get("name", "").strip()
                if author:
                    return author

        # Try contributors
        contributors = entry.get("contributors", [])
        if contributors and isinstance(contributors, list):
            for contributor in contributors:
                if isinstance(contributor, dict) and "name" in contributor:
                    author = contributor.get("name", "").strip()
                    if author:
                        return author

        # Fallback to data source's default author
        if self.data_source and self.data_source.default_author:
            return self.data_source.default_author

        # Return empty string if no author found
        return ""

    @staticmethod
    def _detect_language(text: str) -> str:
        """Auto-detect language from text.

        Args:
            text: Text content to detect language from

        Returns:
            Two-letter language code (e.g., 'en', 'zh', 'fr')
            Returns 'unknown' if detection fails or text is too short
        """
        # Need minimum text length for reliable detection
        if not text or len(text) < 10:
            return "unknown"

        try:
            if detect is None:
                # langdetect not available, default to 'en'
                return "en"

            lang = detect(text)

            # Ensure we have 2-letter code
            if isinstance(lang, str) and len(lang) >= 2:
                return lang[:2].lower()

            return "unknown"

        except Exception as e:
            # Log detection failure but don't break processing
            logger.debug(f"Language detection failed: {e}")
            return "unknown"

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
