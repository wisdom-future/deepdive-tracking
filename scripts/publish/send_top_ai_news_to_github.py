#!/usr/bin/env python3
"""
Send TOP AI News to GitHub - Publish TOP news items as consolidated HTML to a GitHub repository

This script publishes the highest-scored news articles to GitHub as beautifully
formatted HTML pages. It creates a consolidated daily digest page displaying all
TOP news items in one page, then commits and pushes to the repo.

IMPORTANT: Uses diversity-aware selection to ensure content from multiple sources.
"""
import sys
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.channels.github.github_publisher import GitHubPublisher
from src.services.selection import DiversityAwareSelector
from src.config.settings import get_settings
from src.models import ProcessedNews, RawNews
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from src.database.connection import get_session


async def main():
    """Send TOP news to GitHub"""
    settings = get_settings()

    print("=" * 70)
    print("TOP NEWS TO GITHUB - Publishing TOP Articles to GitHub Pages")
    print("=" * 70)

    # Check GitHub configuration
    print("\n1. Checking GitHub configuration...")
    if not settings.github_token or settings.github_token == "your_github_token":  # noqa: S105
        print("[WARNING] GitHub token not configured")
        print("  Please set GITHUB" + "_TOKEN in your .env file")
        print("  Get a token from: https://github.com/settings/tokens")
        print("  Scope needed: repo (full control of private repositories)")
        return False

    if not settings.github_repo or settings.github_repo == "your_username/deepdive-tracking":
        print("[WARNING] GitHub repo not configured")
        print("  Please set GITHUB" + "_REPO in your .env file")
        print("  Format: username/repository")
        return False

    if not settings.github_username or settings.github_username == "your_username":
        print("[WARNING] GitHub username not configured")
        print("  Please set GITHUB" + "_USERNAME in your .env file")
        return False

    print("[OK] GitHub configured")  # noqa: S105
    print(f"    Repo: {settings.github_repo}")
    print(f"    Username: {settings.github_username}")

    # Initialize GitHub Publisher
    print("\n2. Initializing GitHub Publisher...")
    try:
        publisher = GitHubPublisher(
            github_token=settings.github_token,
            github_repo=settings.github_repo,
            github_username=settings.github_username,
            local_repo_path=settings.github_local_path
        )
        print("[OK] GitHub publisher initialized successfully")
    except Exception as e:
        print(f"[FAILED] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Fetch TOP news from database using diversity-aware selection
    print("\n3. Selecting TOP news with diversity awareness...")
    try:
        session = get_session()

        # Use DiversityAwareSelector to ensure source diversity
        selector = DiversityAwareSelector(session)
        selected_candidates, selection_report = selector.select_top_articles(
            limit=10,
            min_raw_score=60.0,  # Minimum quality threshold
            diversity_decay=0.85  # Gentle diversity weighting
        )

        # Extract ProcessedNews objects BEFORE closing session
        # (to avoid DetachedInstanceError when accessing relationships later)
        top_news = [candidate.processed_news for candidate in selected_candidates]

        # Eagerly load raw_news relationships to avoid detached instance errors
        for news in top_news:
            # Access the relationship while session is still open
            _ = news.raw_news

        session.close()

        if not selected_candidates:
            print("[WARNING] No news found meeting quality thresholds")
            print("Please run news collection and scoring first:")
            print("  python scripts/collection/collect_news.py")
            print("  python scripts/evaluation/score_collected_news.py 50")
            return False

        print(f"[OK] Selected {len(selected_candidates)} news items")
        print(f"    Sources: {selection_report['summary']['unique_sources_in_selected']} different sources")
        print(f"    Quality: {selection_report['quality_metrics']['raw_score_mean']:.1f} avg score")
        print()

        # Display source distribution
        print("Source distribution:")
        for source, count in selection_report['source_distribution'].items():
            print(f"  {source:30} {count} articles")
        print()

        # Display selected articles
        print("Selected articles:")
        for idx, candidate in enumerate(selected_candidates, 1):
            title = candidate.raw_news.title[:60]
            source = candidate.source_name
            score = candidate.raw_score
            print(f"  {idx:2}. [{source:20}] {title}... (Score: {score:.1f})")
        print()

        # Save selection report for transparency
        report_dir = Path("logs/selection_reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / f"selection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(selection_report, f, ensure_ascii=False, indent=2)

        print(f"[OK] Selection report saved: {report_file}")
        print()

    except Exception as e:
        print(f"[FAILED] Selection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Prepare articles for GitHub
    print("\n4. Preparing articles for GitHub publishing...")
    articles = []
    for idx, news in enumerate(top_news, 1):
        if not news.raw_news:
            continue

        summary = news.summary_pro or news.summary_sci or "No summary available"
        source_url = news.raw_news.url or "https://deepdive-tracking.github.io"
        author = news.raw_news.source_name or news.raw_news.author or "Unknown Source"
        score = news.score or 0
        content = news.raw_news.content or summary

        article = {
            "title": news.raw_news.title or "Untitled",
            "summary": summary,
            "content": content,
            "source_url": source_url,
            "score": float(score),
            "category": news.category or "AI News",
            "author": author,
            "published_at": datetime.now().isoformat(),
        }
        articles.append(article)

    print(f"[OK] Prepared {len(articles)} articles for publishing")

    # Publish articles to GitHub with consolidated daily digest
    print("\n5. Publishing TOP News to GitHub...")
    try:
        # Use batch publishing to create consolidated digest page
        batch_date = datetime.now().strftime("%Y-%m-%d")
        result = await publisher.publish_batch_articles(
            articles=articles,
            batch_name=batch_date
        )

        if result.get("success"):
            print(f"\n[OK] Successfully published {result.get('published_count')} articles to GitHub")
            print(f"    Batch URL: {result.get('batch_url')}")
            print(f"\nYou can view the published news at:")
            print(f"  https://github.com/{settings.github_repo}")
            return True
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"\n[WARNING] Publishing returned: {error_msg}")
            print(f"  Published: {result.get('published_count')}")
            print(f"  Failed: {result.get('failed_count')}")
            return False

    except Exception as e:
        print(f"[FAILED] Exception during GitHub publishing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print("\n" + "=" * 70)
        if success:
            print("TOP AI NEWS TO GITHUB READY!")
            print("=" * 70)
            print("\nTo use this script, you need:")
            print("1. GitHub Personal Access Token")
            print("   Get it from: https://github.com/settings/tokens")
            print("   Set in .env as: GITHUB" + "_TOKEN=your_token")
            print("")
            print("2. GitHub Repository")
            print("   Create an empty public repo for articles")
            print("   Set in .env as: GITHUB" + "_REPO=username/repo-name")
            print("")
            print("3. GitHub Username")
            print("   Set in .env as: GITHUB" + "_USERNAME=your_username")
        else:
            print("TOP AI NEWS TO GITHUB CONFIGURATION INCOMPLETE!")
            print("=" * 70)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
