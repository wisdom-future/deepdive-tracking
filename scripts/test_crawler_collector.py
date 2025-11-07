"""
Test script for CrawlerCollector functionality.

Tests CSS selector-based web crawling and content extraction.
"""
import asyncio
import logging
from src.services.collection.crawler_collector import CrawlerCollector
from src.models import DataSource

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_simple_list():
    """Test simple list page crawling (no pagination)."""
    logger.info("=" * 80)
    logger.info("Test 1: Simple List Page (No Pagination)")
    logger.info("=" * 80)

    # Example: TechCrunch homepage (adjust selectors based on current structure)
    source = DataSource(
        id=1,
        name="Test TechCrunch",
        type="crawler",
        url="https://techcrunch.com",
        max_items_per_run=5,
        config={
            "list_url": "https://techcrunch.com/",
            "list_selector": "article",
            "title_selector": "h2, h3",
            "url_selector": "a[href]",
            "date_selector": "time",
            "fetch_detail": False,  # Quick test, don't fetch details
            "use_newspaper": False
        },
        is_enabled=True
    )

    collector = CrawlerCollector(source)

    try:
        articles = await collector.collect()
        logger.info(f"✅ Collected {len(articles)} articles")

        for i, article in enumerate(articles[:3], 1):
            logger.info(f"\nArticle {i}:")
            logger.info(f"  Title: {article['title'][:80]}...")
            logger.info(f"  URL: {article['url']}")
            logger.info(f"  Published: {article['published_at']}")
            logger.info(f"  Language: {article['language']}")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")


async def test_with_pagination():
    """Test crawling with URL parameter pagination."""
    logger.info("\n" + "=" * 80)
    logger.info("Test 2: Pagination (URL Parameters)")
    logger.info("=" * 80)

    # Example with pagination
    source = DataSource(
        id=2,
        name="Test with Pagination",
        type="crawler",
        url="https://example.com",
        max_items_per_run=10,
        config={
            "list_url": "https://hn.algolia.com/",  # Hacker News API frontend
            "list_selector": ".Story",
            "title_selector": ".Story_title a",
            "url_selector": ".Story_title a[href]",
            "date_selector": ".Story_meta time",
            "pagination": {
                "enabled": True,
                "type": "url_param",
                "param_name": "page",
                "start": 0,
                "max_pages": 2
            },
            "fetch_detail": False
        },
        is_enabled=True
    )

    collector = CrawlerCollector(source)

    try:
        articles = await collector.collect()
        logger.info(f"✅ Collected {len(articles)} articles across pages")

        # Group by page (rough estimation)
        logger.info(f"\nFirst 3 articles:")
        for i, article in enumerate(articles[:3], 1):
            logger.info(f"{i}. {article['title'][:60]}...")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")


async def test_with_newspaper():
    """Test content extraction using newspaper3k."""
    logger.info("\n" + "=" * 80)
    logger.info("Test 3: Content Extraction with newspaper3k")
    logger.info("=" * 80)

    source = DataSource(
        id=3,
        name="Test Newspaper Extraction",
        type="crawler",
        url="https://techcrunch.com",
        max_items_per_run=2,  # Only 2 for speed
        config={
            "list_url": "https://techcrunch.com/",
            "list_selector": "article",
            "title_selector": "h2, h3",
            "url_selector": "a[href]",
            "fetch_detail": True,  # Fetch full content
            "use_newspaper": True  # Use newspaper3k
        },
        is_enabled=True
    )

    collector = CrawlerCollector(source)

    try:
        articles = await collector.collect()
        logger.info(f"✅ Collected {len(articles)} articles with full content")

        for i, article in enumerate(articles, 1):
            logger.info(f"\nArticle {i}:")
            logger.info(f"  Title: {article['title'][:60]}...")
            logger.info(f"  URL: {article['url']}")
            logger.info(f"  Content Length: {len(article.get('content', ''))} chars")
            logger.info(f"  Is Full Text: {article.get('is_full_text', False)}")
            logger.info(f"  Content Source: {article.get('content_source', 'unknown')}")

            if article.get('content'):
                logger.info(f"  Preview: {article['content'][:150]}...")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")


async def test_css_selectors():
    """Test CSS selector validation."""
    logger.info("\n" + "=" * 80)
    logger.info("Test 4: CSS Selector Validation")
    logger.info("=" * 80)

    test_configs = [
        {
            "name": "Valid Config",
            "config": {
                "list_url": "https://example.com",
                "list_selector": ".item",
                "title_selector": "h2",
                "url_selector": "a",
            },
            "should_pass": True
        },
        {
            "name": "Missing list_url",
            "config": {
                "list_selector": ".item",
                "title_selector": "h2",
            },
            "should_pass": False
        },
        {
            "name": "Missing list_selector",
            "config": {
                "list_url": "https://example.com",
                "title_selector": "h2",
            },
            "should_pass": False
        }
    ]

    for test in test_configs:
        logger.info(f"\nTesting: {test['name']}")
        source = DataSource(
            id=99,
            name="Validation Test",
            type="crawler",
            url="https://example.com",
            config=test['config'],
            is_enabled=True
        )

        collector = CrawlerCollector(source)

        try:
            # Don't actually collect, just check config validation
            if not test['config'].get('list_url'):
                await collector.collect()
                if not test['should_pass']:
                    logger.error(f"  ❌ Should have failed but passed")
                else:
                    logger.info(f"  ✅ Passed as expected")
            else:
                logger.info(f"  ⏭️  Skipped (would require actual HTTP request)")

        except ValueError as e:
            if not test['should_pass']:
                logger.info(f"  ✅ Failed as expected: {e}")
            else:
                logger.error(f"  ❌ Should have passed but failed: {e}")
        except Exception as e:
            logger.warning(f"  ⚠️  Other error: {e}")


async def test_url_building():
    """Test paginated URL building."""
    logger.info("\n" + "=" * 80)
    logger.info("Test 5: Paginated URL Building")
    logger.info("=" * 80)

    from src.services.collection.crawler_collector import CrawlerCollector

    test_cases = [
        ("https://example.com/news", "page", 1, "https://example.com/news?page=1"),
        ("https://example.com/news?sort=date", "page", 2, "https://example.com/news?sort=date&page=2"),
        ("https://example.com/news", "p", 5, "https://example.com/news?p=5"),
    ]

    for base_url, param, page_num, expected in test_cases:
        result = CrawlerCollector._build_paginated_url(base_url, param, page_num)
        status = "✅" if param in result and str(page_num) in result else "❌"
        logger.info(f"{status} {base_url} + {param}={page_num}")
        logger.info(f"   Result: {result}")
        logger.info(f"   Expected: {expected}")


if __name__ == "__main__":
    logger.info("Starting CrawlerCollector Tests\n")

    # Run all tests
    tests = [
        ("Simple List", test_simple_list),
        ("With Pagination", test_with_pagination),
        ("With Newspaper3k", test_with_newspaper),
        ("CSS Selectors", test_css_selectors),
        ("URL Building", test_url_building),
    ]

    async def run_all_tests():
        for name, test_func in tests:
            try:
                await test_func()
            except Exception as e:
                logger.error(f"\n❌ Test '{name}' crashed: {e}")

            # Pause between tests
            await asyncio.sleep(2)

    asyncio.run(run_all_tests())

    logger.info("\n" + "=" * 80)
    logger.info("All Tests Completed!")
    logger.info("=" * 80)
    logger.info("\nNext steps:")
    logger.info("1. Create data source with crawler type in database")
    logger.info("2. Configure CSS selectors for your target website")
    logger.info("3. Run: python scripts/collection/collect_news.py")
    logger.info("4. Check logs for collection statistics")
