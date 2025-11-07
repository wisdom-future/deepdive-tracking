"""
Test script for full article fetching functionality.

This script tests the newspaper3k integration to fetch full article content
from URLs when RSS feeds only provide summaries.
"""
import asyncio
import logging
from src.services.collection.rss_collector import RSSCollector
from src.models import DataSource

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_full_article_fetch():
    """Test full article fetching with sample URLs."""

    # Create a test data source
    test_source = DataSource(
        id=999,
        name="Test Source",
        type="rss",
        url="https://example.com/feed",
        max_items_per_run=10,
        is_enabled=True
    )

    collector = RSSCollector(test_source)

    # Test cases: (URL, short_content)
    test_cases = [
        {
            "url": "https://techcrunch.com/2024/11/01/openai-launches-gpt-4/",
            "short_content": "OpenAI announces GPT-4 with improved capabilities...",
            "description": "TechCrunch article (should fetch full text)"
        },
        {
            "url": "https://www.theverge.com/2024/11/01/ai-news",
            "short_content": "AI companies are racing to build better models...",
            "description": "The Verge article (should fetch full text)"
        },
        {
            "url": "https://example.com/full-content-in-rss",
            "short_content": "This is a long article content that exceeds 500 characters. " * 10,
            "description": "Long RSS content (should skip fetching)"
        },
    ]

    logger.info("=" * 80)
    logger.info("Testing Full Article Fetch Functionality")
    logger.info("=" * 80)

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\nTest Case {i}: {test_case['description']}")
        logger.info(f"URL: {test_case['url']}")
        logger.info(f"RSS Content Length: {len(test_case['short_content'])} chars")

        try:
            result = await collector._fetch_full_article(
                test_case['url'],
                test_case['short_content'],
                f"<p>{test_case['short_content']}</p>"  # Mock HTML
            )

            logger.info(f"✅ Result:")
            logger.info(f"  - Content Source: {result['content_source']}")
            logger.info(f"  - Is Full Text: {result['is_full_text']}")
            logger.info(f"  - Final Content Length: {len(result['content'])} chars")

            if result['content_source'] == 'fetched':
                logger.info(f"  - ✨ Successfully fetched full article!")
            elif result['content_source'] == 'rss':
                if len(test_case['short_content']) >= 500:
                    logger.info(f"  - ✅ Correctly skipped fetch (content sufficient)")
                else:
                    logger.info(f"  - ⚠️ Used RSS content (fetch may have failed)")

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")

    logger.info("\n" + "=" * 80)
    logger.info("Test completed!")
    logger.info("=" * 80)


async def test_content_extraction_methods():
    """Test different content extraction approaches."""

    logger.info("\n" + "=" * 80)
    logger.info("Testing Content Extraction Methods")
    logger.info("=" * 80)

    # Test newspaper3k availability
    try:
        from newspaper import Article
        logger.info("✅ newspaper3k is installed and available")

        # Test with a real article (if network is available)
        test_url = "https://techcrunch.com/"
        logger.info(f"\nTesting with real URL: {test_url}")

        try:
            article = Article(test_url)
            article.download()
            article.parse()

            logger.info(f"✅ Article downloaded and parsed successfully")
            logger.info(f"  - Title: {article.title[:80]}...")
            logger.info(f"  - Content Length: {len(article.text)} chars")
            logger.info(f"  - Authors: {', '.join(article.authors) if article.authors else 'None'}")

        except Exception as e:
            logger.warning(f"⚠️ Could not fetch test article: {e}")
            logger.warning("This is normal if network is restricted or site blocks scrapers")

    except ImportError:
        logger.error("❌ newspaper3k is NOT installed")
        logger.error("Install with: pip install newspaper3k")


if __name__ == "__main__":
    logger.info("Starting Full Article Fetch Tests\n")

    # Run tests
    asyncio.run(test_full_article_fetch())
    asyncio.run(test_content_extraction_methods())

    logger.info("\n✅ All tests completed!")
    logger.info("\nNext steps:")
    logger.info("1. Install dependencies: pip install -e .")
    logger.info("2. Run real collection: python scripts/collection/collect_news.py")
    logger.info("3. Check logs for 'Content quality' statistics")
