"""
Generic web crawler collector for configurable content extraction.

This collector allows extracting content from any website by configuring
CSS selectors for list pages and article pages.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import aiohttp
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

try:
    from newspaper import Article as NewspaperArticle
except ImportError:
    NewspaperArticle = None

try:
    from langdetect import detect
except ImportError:
    detect = None

from src.services.collection.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class CrawlerCollector(BaseCollector):
    """
    Generic web crawler that extracts content using CSS selectors.

    Configuration (in DataSource.config JSON field):
    {
        "list_url": "https://example.com/news",
        "list_selector": ".news-item",
        "title_selector": ".title",
        "url_selector": "a[href]",
        "date_selector": ".date",
        "content_selector": ".article-content",  # Optional, for detail page
        "pagination": {
            "enabled": true,
            "type": "url_param",  # or "next_link"
            "param_name": "page",  # for url_param type
            "next_selector": ".pagination .next",  # for next_link type
            "start": 1,
            "max_pages": 5
        },
        "fetch_detail": true,  # Whether to fetch detail page
        "use_newspaper": true  # Use newspaper3k for content extraction
    }
    """

    def __init__(self, data_source):
        """Initialize crawler collector.

        Args:
            data_source: DataSource instance with crawler configuration
        """
        super().__init__(data_source)
        self.config = data_source.config or {}
        self.session: Optional[aiohttp.ClientSession] = None

    async def collect(self) -> List[Dict[str, Any]]:
        """Collect articles from configured website.

        Returns:
            List of article dictionaries
        """
        # Validate required configuration
        list_url = self.config.get("list_url")
        if not list_url:
            raise ValueError(f"Missing 'list_url' in config for {self.data_source.name}")

        try:
            # Create aiohttp session
            async with aiohttp.ClientSession() as self.session:
                articles = []
                pagination_config = self.config.get("pagination", {})
                max_items = self.data_source.max_items_per_run or 50

                if pagination_config.get("enabled", False):
                    # Crawl with pagination
                    articles = await self._crawl_with_pagination(
                        list_url, pagination_config, max_items
                    )
                else:
                    # Crawl single page
                    page_articles = await self._crawl_list_page(list_url)
                    articles.extend(page_articles[:max_items])

                self.log_collection_attempt(True, f"Collected {len(articles)} articles")
                return articles

        except Exception as e:
            self.log_collection_attempt(False, str(e), e)
            raise

    async def _crawl_with_pagination(
        self, base_url: str, pagination_config: Dict, max_items: int
    ) -> List[Dict[str, Any]]:
        """Crawl multiple pages with pagination.

        Args:
            base_url: Base URL for list pages
            pagination_config: Pagination configuration
            max_items: Maximum items to collect

        Returns:
            List of articles from all pages
        """
        articles = []
        pagination_type = pagination_config.get("type", "url_param")

        if pagination_type == "url_param":
            # Pagination via URL parameter (e.g., ?page=1)
            param_name = pagination_config.get("param_name", "page")
            start_page = pagination_config.get("start", 1)
            max_pages = pagination_config.get("max_pages", 5)

            for page_num in range(start_page, start_page + max_pages):
                page_url = self._build_paginated_url(base_url, param_name, page_num)
                self.logger.info(f"Crawling page {page_num}: {page_url}")

                try:
                    page_articles = await self._crawl_list_page(page_url)
                    articles.extend(page_articles)

                    if len(articles) >= max_items:
                        break

                except Exception as e:
                    self.logger.warning(f"Failed to crawl page {page_num}: {e}")
                    continue

                # Rate limiting
                await asyncio.sleep(1)

        elif pagination_type == "next_link":
            # Pagination via "Next" link
            next_selector = pagination_config.get("next_selector", ".pagination .next")
            max_pages = pagination_config.get("max_pages", 5)
            current_url = base_url

            for page_num in range(max_pages):
                self.logger.info(f"Crawling page {page_num + 1}: {current_url}")

                try:
                    page_articles = await self._crawl_list_page(current_url)
                    articles.extend(page_articles)

                    if len(articles) >= max_items:
                        break

                    # Find next page link
                    html = await self._fetch_url(current_url)
                    soup = BeautifulSoup(html, 'html.parser')
                    next_link = soup.select_one(next_selector)

                    if not next_link or not next_link.get('href'):
                        self.logger.info("No more pages found")
                        break

                    current_url = urljoin(current_url, next_link['href'])

                except Exception as e:
                    self.logger.warning(f"Failed to crawl page {page_num + 1}: {e}")
                    break

                # Rate limiting
                await asyncio.sleep(1)

        return articles[:max_items]

    async def _crawl_list_page(self, url: str) -> List[Dict[str, Any]]:
        """Crawl a single list page and extract articles.

        Args:
            url: URL of the list page

        Returns:
            List of article dictionaries
        """
        html = await self._fetch_url(url)
        soup = BeautifulSoup(html, 'html.parser')

        list_selector = self.config.get("list_selector")
        if not list_selector:
            raise ValueError(f"Missing 'list_selector' in config")

        items = soup.select(list_selector)
        self.logger.debug(f"Found {len(items)} items with selector '{list_selector}'")

        articles = []
        for item in items:
            try:
                article = await self._extract_article_from_list_item(item, url)
                if article:
                    articles.append(article)
            except Exception as e:
                self.logger.warning(f"Failed to extract article from list item: {e}")
                continue

        return articles

    async def _extract_article_from_list_item(
        self, item, base_url: str
    ) -> Optional[Dict[str, Any]]:
        """Extract article data from a list item element.

        Args:
            item: BeautifulSoup element (list item)
            base_url: Base URL for resolving relative URLs

        Returns:
            Article dictionary or None if extraction fails
        """
        # Extract title
        title_selector = self.config.get("title_selector", "h2, h3, .title")
        title_elem = item.select_one(title_selector)
        if not title_elem:
            self.logger.debug(f"No title found with selector '{title_selector}'")
            return None
        title = title_elem.get_text(strip=True)

        # Extract URL
        url_selector = self.config.get("url_selector", "a[href]")
        url_elem = item.select_one(url_selector)
        if not url_elem or not url_elem.get('href'):
            self.logger.debug(f"No URL found with selector '{url_selector}'")
            return None
        article_url = urljoin(base_url, url_elem['href'])

        # Extract date
        published_at = self._extract_date(item)

        # Extract content
        content = ""
        html_content = ""

        if self.config.get("fetch_detail", True):
            # Fetch detail page for full content
            content, html_content = await self._fetch_article_detail(article_url)
        else:
            # Extract summary from list page
            content_selector = self.config.get("content_selector", ".summary, .excerpt")
            content_elem = item.select_one(content_selector)
            if content_elem:
                content = content_elem.get_text(strip=True)
                html_content = str(content_elem)

        # Detect language
        language = self._detect_language(content)

        # Extract author (optional)
        author = self._extract_author(item)

        return {
            "title": title,
            "url": article_url,
            "content": content,
            "html_content": html_content.encode('utf-8') if html_content else None,
            "author": author,
            "published_at": published_at,
            "language": language,
            "content_source": "crawler",
            "is_full_text": bool(content and len(content) > 500),
        }

    async def _fetch_article_detail(self, url: str) -> tuple[str, str]:
        """Fetch and extract content from article detail page.

        Args:
            url: Article URL

        Returns:
            Tuple of (text_content, html_content)
        """
        use_newspaper = self.config.get("use_newspaper", True)

        if use_newspaper and NewspaperArticle:
            # Use newspaper3k for smart extraction
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, self._extract_with_newspaper, url
                )
                if result:
                    return result["text"], result["html"]
            except Exception as e:
                self.logger.warning(f"Newspaper extraction failed for {url}: {e}")

        # Fallback: use CSS selector
        content_selector = self.config.get("content_selector")
        if content_selector:
            try:
                html = await self._fetch_url(url)
                soup = BeautifulSoup(html, 'html.parser')
                content_elem = soup.select_one(content_selector)

                if content_elem:
                    text = content_elem.get_text(strip=True)
                    html_str = str(content_elem)
                    return text, html_str
            except Exception as e:
                self.logger.warning(f"CSS selector extraction failed for {url}: {e}")

        return "", ""

    @staticmethod
    def _extract_with_newspaper(url: str) -> Optional[Dict[str, str]]:
        """Extract article using newspaper3k.

        Args:
            url: Article URL

        Returns:
            Dict with 'text' and 'html', or None if fails
        """
        if not NewspaperArticle:
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
            logger.debug(f"Newspaper extraction error: {e}")

        return None

    def _extract_date(self, item) -> datetime:
        """Extract published date from list item.

        Args:
            item: BeautifulSoup element

        Returns:
            datetime object (current time if not found)
        """
        date_selector = self.config.get("date_selector", "time, .date, .published")
        date_elem = item.select_one(date_selector)

        if date_elem:
            # Try datetime attribute first
            date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)

            try:
                return date_parser.parse(date_str)
            except Exception as e:
                self.logger.debug(f"Failed to parse date '{date_str}': {e}")

        # Fallback to current time
        return datetime.now(timezone.utc)

    def _extract_author(self, item) -> Optional[str]:
        """Extract author from list item.

        Args:
            item: BeautifulSoup element

        Returns:
            Author name or None
        """
        author_selector = self.config.get("author_selector", ".author, .byline")
        author_elem = item.select_one(author_selector)

        if author_elem:
            return author_elem.get_text(strip=True)

        return None

    @staticmethod
    def _detect_language(text: str) -> str:
        """Detect language from text.

        Args:
            text: Content text

        Returns:
            Two-letter language code
        """
        if not text or len(text) < 10:
            return "unknown"

        if not detect:
            return "en"

        try:
            lang = detect(text)
            return lang[:2].lower() if isinstance(lang, str) else "unknown"
        except Exception:
            return "unknown"

    async def _fetch_url(self, url: str) -> str:
        """Fetch URL content.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string
        """
        if not self.session:
            raise RuntimeError("Session not initialized")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }

        async with self.session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status != 200:
                raise ValueError(f"HTTP {response.status} for {url}")

            return await response.text()

    @staticmethod
    def _build_paginated_url(base_url: str, param_name: str, page_num: int) -> str:
        """Build URL with pagination parameter.

        Args:
            base_url: Base URL
            param_name: Parameter name (e.g., 'page')
            page_num: Page number

        Returns:
            URL with pagination parameter
        """
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)
        query_params[param_name] = [str(page_num)]

        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)

        return urlunparse(new_parsed)
