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

try:
    from newspaper import Article as NewspaperArticle
except ImportError:
    # Fallback if newspaper3k not installed
    NewspaperArticle = None

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
                # Extract content with raw HTML and cleaned text from RSS
                rss_content, rss_html = self._extract_content(entry)

                # Validate content is not empty and meets minimum quality
                if not rss_content or len(rss_content.strip()) < 50:
                    self.logger.warning(
                        f"Skipping entry with insufficient content (len={len(rss_content)}): "
                        f"{entry.get('title', 'No title')}"
                    )
                    continue

                # Attempt to fetch full article if RSS content is too short
                article_url = entry.get("link", "")
                full_article = await self._fetch_full_article(
                    article_url, rss_content, rss_html
                )

                # Use fetched content (or fall back to RSS content)
                final_content = full_article["content"]
                final_html = full_article["html_content"]

                # Detect language from final content
                language = self._detect_language(final_content)

                # Extract author with multiple sources
                author = self._extract_author(entry)

                article = {
                    "title": entry.get("title", ""),
                    "url": article_url,
                    "content": final_content,
                    "author": author,
                    "published_at": self._parse_published_date(entry),
                    "language": language,
                    "html_content": final_html,
                    # Metadata about content source
                    "content_source": full_article["content_source"],
                    "is_full_text": full_article["is_full_text"],
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
    def _extract_content(entry: Dict[str, Any]) -> tuple[str, str]:
        """Extract full article content with HTML cleaning and raw HTML preservation.

        Tries multiple content sources with fallback strategy:
        1. content (Atom format - usually HTML)
        2. summary (RSS format - may contain HTML)
        3. description (RSS format - may contain HTML)

        All content is cleaned to remove HTML tags and convert to plain text,
        but the original HTML is preserved for future processing.

        Args:
            entry: Parsed RSS entry from feedparser

        Returns:
            Tuple of (cleaned_text, raw_html):
                - cleaned_text: Plain text content without HTML tags
                - raw_html: Original HTML content for secondary processing
        """
        raw_html = ""

        # Try content (Atom format - highest priority)
        if "content" in entry and entry.content:
            content_list = entry.get("content", [])
            if content_list and isinstance(content_list, list):
                raw_html = content_list[0].get("value", "").strip()
                if raw_html:
                    cleaned_text = HTMLCleaner.clean(raw_html)
                    return cleaned_text, raw_html

        # Try summary (RSS format - second priority)
        summary = entry.get("summary", "").strip()
        if summary:
            cleaned_text = HTMLCleaner.clean(summary)
            return cleaned_text, summary

        # Fallback to description
        description = entry.get("description", "").strip()
        if description:
            cleaned_text = HTMLCleaner.clean(description)
            return cleaned_text, description

        # Return empty strings if nothing found
        return "", ""

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

    async def _fetch_full_article(
        self, url: str, rss_content: str, rss_html: str
    ) -> Dict[str, Any]:
        """
        Fetch full article content when RSS only provides summary.

        This method determines if RSS content is insufficient (likely just a summary),
        and if so, fetches and extracts the full article from the source URL.

        Args:
            url: Article URL
            rss_content: Cleaned text content from RSS feed
            rss_html: Raw HTML content from RSS feed

        Returns:
            Dictionary with:
                - content: str - Full article text (or RSS content if fetch fails)
                - html_content: str - Raw HTML (or RSS HTML if fetch fails)
                - is_full_text: bool - Whether full text was successfully fetched
                - content_source: str - Source of content ('rss', 'fetched', 'failed')

        Strategy:
            1. If RSS content is long enough (>500 chars), assume it's full text
            2. Otherwise, try to fetch full article from URL using newspaper3k
            3. If fetch succeeds and yields more content, use fetched version
            4. Otherwise, fall back to RSS content
        """
        # Define threshold for "sufficient" content length
        MIN_FULL_TEXT_LENGTH = 500

        # Check if RSS content is already sufficient
        if len(rss_content) >= MIN_FULL_TEXT_LENGTH:
            self.logger.debug(
                f"RSS content sufficient ({len(rss_content)} chars), skipping fetch for {url}"
            )
            return {
                "content": rss_content,
                "html_content": rss_html,
                "is_full_text": True,
                "content_source": "rss",
            }

        # Check if newspaper3k is available
        if NewspaperArticle is None:
            self.logger.warning(
                "newspaper3k not installed, cannot fetch full article. "
                "Install with: pip install newspaper3k"
            )
            return {
                "content": rss_content,
                "html_content": rss_html,
                "is_full_text": False,
                "content_source": "rss",
            }

        # Attempt to fetch full article
        try:
            self.logger.info(
                f"RSS content short ({len(rss_content)} chars), fetching full article from {url}"
            )

            # Run newspaper3k in thread pool (it's CPU-bound)
            loop = asyncio.get_event_loop()
            article = await loop.run_in_executor(
                None, self._extract_with_newspaper, url
            )

            if article and article.get("text") and article.get("html"):
                fetched_text = article["text"]
                fetched_html = article["html"]

                # Only use fetched content if it's significantly longer than RSS content
                if len(fetched_text) > len(rss_content) * 1.5:
                    self.logger.info(
                        f"Successfully fetched full article ({len(fetched_text)} chars) "
                        f"vs RSS ({len(rss_content)} chars)"
                    )
                    return {
                        "content": fetched_text,
                        "html_content": fetched_html,
                        "is_full_text": True,
                        "content_source": "fetched",
                    }
                else:
                    self.logger.warning(
                        f"Fetched content not significantly longer, using RSS content"
                    )

        except Exception as e:
            self.logger.warning(f"Failed to fetch full article from {url}: {e}")

        # Fallback to RSS content
        return {
            "content": rss_content,
            "html_content": rss_html,
            "is_full_text": False,
            "content_source": "rss",
        }

    @staticmethod
    def _extract_with_newspaper(url: str) -> Optional[Dict[str, str]]:
        """
        Extract article content using newspaper3k.

        This is a synchronous method designed to be run in a thread pool.

        Args:
            url: Article URL

        Returns:
            Dictionary with 'text' and 'html' keys, or None if extraction fails
        """
        if NewspaperArticle is None:
            return None

        try:
            article = NewspaperArticle(url)
            article.download()
            article.parse()

            if article.text and article.html:
                return {
                    "text": article.text,
                    "html": article.html,
                }

        except Exception as e:
            logger.debug(f"Newspaper extraction failed for {url}: {e}")

        return None
