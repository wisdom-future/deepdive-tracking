"""Data sources configuration.

This module defines all available AI news data sources for collection.
Sources are centralized here for easy management and updates.
"""

# High-priority AI news sources
DATA_SOURCES = [
    {
        'name': 'Google DeepMind Blog',
        'description': 'Official blog of Google DeepMind',
        'type': 'rss',
        'url': 'https://deepmind.google/feed.xml',
        'method': 'GET',
        'priority': 9,
        'is_enabled': True,
    },
    {
        'name': 'Meta AI Research',
        'description': 'Meta AI research and updates',
        'type': 'rss',
        'url': 'https://ai.facebook.com/feed.xml',
        'method': 'GET',
        'priority': 8,
        'is_enabled': True,
    },
    {
        'name': 'Microsoft AI Blog',
        'description': 'Microsoft AI and Research blog',
        'type': 'rss',
        'url': 'https://www.microsoft.com/en-us/ai/ai-update-feed',
        'method': 'GET',
        'priority': 8,
        'is_enabled': True,
    },
    {
        'name': 'NVIDIA AI Blog',
        'description': 'NVIDIA AI and deep learning blog',
        'type': 'rss',
        'url': 'https://blogs.nvidia.com/ai/feed/',
        'method': 'GET',
        'priority': 8,
        'is_enabled': True,
    },
    {
        'name': 'TechCrunch AI',
        'description': 'TechCrunch AI news and analysis',
        'type': 'rss',
        'url': 'https://techcrunch.com/category/artificial-intelligence/feed/',
        'method': 'GET',
        'priority': 7,
        'is_enabled': True,
    },
    {
        'name': 'The Verge AI',
        'description': 'The Verge AI and technology news',
        'type': 'rss',
        'url': 'https://www.theverge.com/rss/index.xml',
        'method': 'GET',
        'priority': 7,
        'is_enabled': True,
    },
    {
        'name': 'MIT Technology Review',
        'description': 'MIT Technology Review AI and science',
        'type': 'rss',
        'url': 'https://www.technologyreview.com/ai/feed/',
        'method': 'GET',
        'priority': 8,
        'is_enabled': True,
    },
    {
        'name': 'VentureBeat AI',
        'description': 'VentureBeat AI news and insights',
        'type': 'rss',
        'url': 'https://venturebeat.com/category/ai/feed/',
        'method': 'GET',
        'priority': 7,
        'is_enabled': True,
    },
    {
        'name': 'ArXiv CS.AI',
        'description': 'ArXiv computer science AI papers',
        'type': 'api',
        'url': 'https://arxiv.org/list/cs.AI/recent',
        'method': 'GET',
        'priority': 9,
        'is_enabled': True,
    },
    {
        'name': 'Papers with Code',
        'description': 'Latest papers with code implementation',
        'type': 'api',
        'url': 'https://paperswithcode.com/api/papers',
        'method': 'GET',
        'priority': 8,
        'is_enabled': True,
    },
    {
        'name': 'JiQiZhiXin',
        'description': 'China - AI news and research',
        'type': 'rss',
        'url': 'https://www.jiqizhixin.com/rss',
        'method': 'GET',
        'priority': 7,
        'is_enabled': True,
    },
    {
        'name': 'QuantumBit',
        'description': 'China - AI and quantum computing news',
        'type': 'rss',
        'url': 'https://www.qbitai.com/feed',
        'method': 'GET',
        'priority': 7,
        'is_enabled': True,
    },
]


def get_data_sources():
    """Get list of all data sources.

    Returns:
        list: List of data source configurations.
    """
    return DATA_SOURCES
