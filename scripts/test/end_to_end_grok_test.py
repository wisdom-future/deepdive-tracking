#!/usr/bin/env python3
"""
End-to-End Grok Scoring Test

This script executes the complete workflow to test Grok scoring and diversity selection:
1. Clear old GPT-4o scored data
2. Collect fresh news articles (100 articles)
3. Score articles with Grok (50 articles)
4. Analyze and verify source diversity
5. Publish TOP 10 to GitHub with diversity selection

Usage:
    python scripts/test/end_to_end_grok_test.py
"""

import sys
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_session
from src.models import ProcessedNews, CostLog, RawNews
from src.config import get_settings


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def run_script(script_path, *args):
    """Run a Python script and return exit code"""
    cmd = [sys.executable, str(script_path)] + list(args)
    print(f"\n🔧 Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


async def main():
    """Execute end-to-end workflow test"""
    print_section("END-TO-END GROK SCORING TEST")

    settings = get_settings()
    start_time = datetime.now()

    print(f"\n📅 Test started at: {start_time.isoformat()}")
    print(f"🤖 AI Provider: {settings.ai_provider.upper()}")
    print(f"🔧 Model: {settings.xai_model if settings.ai_provider == 'grok' else settings.openai_model}")

    # Step 1: Clear old data
    print_section("STEP 1: Clear Old Scoring Data")
    print("Removing all GPT-4o scored data to start fresh...")

    session = get_session()
    try:
        processed_count = session.query(ProcessedNews).count()
        cost_count = session.query(CostLog).count()

        print(f"Current data: {processed_count} processed news, {cost_count} cost logs")

        if processed_count > 0:
            # Delete all processed news and cost logs
            session.query(CostLog).delete()
            session.query(ProcessedNews).delete()

            # Reset raw_news status
            updated = session.query(RawNews).filter(
                RawNews.status == "processed"
            ).update({"status": "collected"})

            session.commit()
            print(f"✅ Cleared: {processed_count} processed news, {cost_count} cost logs")
            print(f"✅ Reset: {updated} raw news status to 'collected'")
        else:
            print("✅ No old data to clear")

    except Exception as e:
        session.rollback()
        print(f"❌ Error clearing data: {e}")
        return 1
    finally:
        session.close()

    # Step 2: Collect fresh news
    print_section("STEP 2: Collect Fresh News Articles")
    print("Collecting 100 recent articles from multiple sources...")

    collection_script = project_root / "scripts" / "collection" / "collect_news.py"
    if not collection_script.exists():
        print(f"❌ Collection script not found: {collection_script}")
        return 1

    exit_code = run_script(collection_script)
    if exit_code != 0:
        print(f"❌ Collection failed with exit code {exit_code}")
        return exit_code

    print("✅ Collection completed")

    # Step 3: Score with Grok
    print_section("STEP 3: Score Articles with Grok")
    print("Scoring 50 articles using Grok API...")

    scoring_script = project_root / "scripts" / "evaluation" / "score_collected_news.py"
    if not scoring_script.exists():
        print(f"❌ Scoring script not found: {scoring_script}")
        return 1

    exit_code = run_script(scoring_script, "50")
    if exit_code != 0:
        print(f"❌ Scoring failed with exit code {exit_code}")
        return exit_code

    print("✅ Scoring completed")

    # Step 4: Analyze diversity
    print_section("STEP 4: Analyze Source Diversity")
    print("Checking if multiple sources achieved high scores...")

    session = get_session()
    try:
        # Query scored articles grouped by source
        from sqlalchemy import func

        diversity_query = session.query(
            RawNews.source_name,
            func.count(ProcessedNews.id).label('count'),
            func.avg(ProcessedNews.score).label('avg_score'),
            func.max(ProcessedNews.score).label('max_score')
        ).join(
            ProcessedNews, ProcessedNews.raw_news_id == RawNews.id
        ).group_by(
            RawNews.source_name
        ).order_by(
            func.avg(ProcessedNews.score).desc()
        ).all()

        print("\n📊 Scoring Results by Source:")
        print(f"{'Source':<30} {'Count':>8} {'Avg Score':>12} {'Max Score':>12}")
        print("-" * 70)

        sources_above_60 = 0
        for source_name, count, avg_score, max_score in diversity_query:
            print(f"{source_name[:28]:<30} {count:>8} {avg_score:>12.1f} {max_score:>12.1f}")
            if max_score >= 60:
                sources_above_60 += 1

        print("\n📈 Diversity Metrics:")
        print(f"   Total sources scored: {len(diversity_query)}")
        print(f"   Sources with score ≥60: {sources_above_60}")

        if sources_above_60 >= 3:
            print("   ✅ PASS: Multiple sources have high-quality content")
        elif sources_above_60 >= 2:
            print("   ⚠️  WARNING: Only 2 sources have high-quality content")
        else:
            print("   ❌ FAIL: Insufficient source diversity")

    except Exception as e:
        print(f"❌ Error analyzing diversity: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

    # Step 5: Publish with diversity selection
    print_section("STEP 5: Publish TOP News with Diversity Selection")
    print("Publishing TOP 10 articles using diversity-aware selection...")

    github_script = project_root / "scripts" / "publish" / "send_top_ai_news_to_github.py"
    if not github_script.exists():
        print(f"⚠️  GitHub publishing script not found: {github_script}")
        print("Skipping publishing step")
    else:
        exit_code = run_script(github_script)
        if exit_code != 0:
            print(f"⚠️  Publishing failed with exit code {exit_code}")
        else:
            print("✅ Publishing completed")

    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print_section("TEST COMPLETED")
    print(f"🕐 Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"🎯 Results:")
    print(f"   - Old data cleared: ✅")
    print(f"   - News collected: ✅")
    print(f"   - Articles scored with {settings.ai_provider.upper()}: ✅")
    print(f"   - Source diversity: {'✅' if sources_above_60 >= 3 else '⚠️'}")
    print()
    print("Next steps:")
    print("  1. Check email for published content")
    print("  2. Verify source diversity in published articles")
    print("  3. If satisfactory, commit and push code to main branch")
    print()

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
