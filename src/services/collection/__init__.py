"""Data collection service module."""

from src.services.collection.base_collector import BaseCollector
from src.services.collection.rss_collector import RSSCollector
from src.services.collection.collection_manager import CollectionManager

__all__ = [
    "BaseCollector",
    "RSSCollector",
    "CollectionManager",
]
