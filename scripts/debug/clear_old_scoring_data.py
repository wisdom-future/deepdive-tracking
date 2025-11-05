#!/usr/bin/env python3
"""
Clear Old Scoring Data - Remove GPT-4o scored data to prepare for Grok re-scoring

This script clears:
- processed_news table (all AI-scored articles)
- cost_log table (all cost records)
- Updates raw_news.status back to 'collected'

Use this to start fresh with Grok scoring.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_session
from src.models import ProcessedNews, CostLog, RawNews


def main():
    """Clear old scoring data"""
    print("\n" + "=" * 70)
    print("CLEAR OLD SCORING DATA")
    print("=" * 70)
    print()

    session = get_session()

    try:
        # Get counts before deletion
        print("1. Checking current data counts...")
        processed_count = session.query(ProcessedNews).count()
        cost_count = session.query(CostLog).count()
        raw_processed_count = session.query(RawNews).filter(
            RawNews.status == "processed"
        ).count()

        print(f"   ProcessedNews records: {processed_count}")
        print(f"   CostLog records: {cost_count}")
        print(f"   RawNews marked as 'processed': {raw_processed_count}")
        print()

        if processed_count == 0:
            print("✅ No data to clear. Database is already clean.")
            return 0

        # Delete processed news
        print("2. Deleting ProcessedNews records...")
        deleted_processed = session.query(ProcessedNews).delete()
        print(f"   Deleted {deleted_processed} records")

        # Delete cost logs
        print("3. Deleting CostLog records...")
        deleted_costs = session.query(CostLog).delete()
        print(f"   Deleted {deleted_costs} records")

        # Reset raw_news status
        print("4. Resetting RawNews status to 'collected'...")
        updated_raw = session.query(RawNews).filter(
            RawNews.status == "processed"
        ).update({"status": "collected"})
        print(f"   Updated {updated_raw} records")

        # Commit changes
        session.commit()
        print()
        print("=" * 70)
        print("✅ DATA CLEARED SUCCESSFULLY")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Collect fresh news: python scripts/collection/collect_news.py")
        print("  2. Score with Grok: python scripts/evaluation/score_collected_news.py 200")
        print("  3. Verify diversity: python scripts/debug/analyze_scoring_issue.py")
        print()

        return 0

    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        session.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
