"""Base collector class for different data sources."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import hashlib
import logging

from src.models import RawNews, DataSource

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""

    def __init__(self, data_source: DataSource):
        """Initialize collector with data source configuration.

        Args:
            data_source: DataSource model instance with configuration
        """
        self.data_source = data_source
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """Collect raw news items from the source.

        Returns:
            List of dictionaries with news data:
            - title (str): News title
            - url (str): Source URL
            - content (Optional[str]): Article content
            - author (Optional[str]): Author name
            - published_at (datetime): Publication datetime
            - language (str): Content language (en, zh, etc.)
            - html_content (Optional[bytes]): Raw HTML if applicable
        """
        pass

    def generate_hash(self, title: str, url: str) -> str:
        """Generate unique hash for content deduplication.

        Args:
            title: Article title
            url: Article URL

        Returns:
            SHA256 hash string
        """
        content = f"{title}|{url}".lower()
        return hashlib.sha256(content.encode()).hexdigest()

    def create_raw_news_item(
        self,
        title: str,
        url: str,
        published_at: datetime,
        content: Optional[str] = None,
        author: Optional[str] = None,
        html_content: Optional[bytes] = None,
        language: str = "en",
    ) -> RawNews:
        """Create RawNews model instance from collected data.

        Args:
            title: News title
            url: Source URL
            published_at: Publication datetime
            content: Article content (optional)
            author: Author name (optional)
            html_content: Raw HTML (optional)
            language: Content language

        Returns:
            RawNews model instance
        """
        news_hash = self.generate_hash(title, url)

        return RawNews(
            source_id=self.data_source.id,
            title=title,
            url=url,
            content=content,
            html_content=html_content,
            language=language,
            hash=news_hash,
            author=author,
            source_name=self.data_source.name,
            published_at=published_at,
            fetched_at=datetime.now(published_at.tzinfo if published_at.tzinfo else None),
            status="raw",
        )

    def log_collection_attempt(self, success: bool, message: str = "", error: Optional[Exception] = None) -> None:
        """Log collection attempt for monitoring.

        Args:
            success: Whether collection was successful
            message: Additional message
            error: Exception if failed
        """
        if success:
            self.logger.info(
                f"Collection successful for {self.data_source.name}: {message}",
                extra={"source_id": self.data_source.id},
            )
        else:
            self.logger.error(
                f"Collection failed for {self.data_source.name}: {message}",
                exc_info=error,
                extra={"source_id": self.data_source.id},
            )
