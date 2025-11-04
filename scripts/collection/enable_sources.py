#!/usr/bin/env python
"""
Quick script to enable disabled data sources for collection.

This will enable all the major AI news sources that are currently disabled.
Expected result: 5-10x more data collection.

Usage:
    python scripts/collection/enable_sources.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_session
from src.models import DataSource

# Sources to enable (high-value AI news sources)
SOURCES_TO_ENABLE = [
    "Google DeepMind Blog",
    "Meta AI Research",
    "Microsoft AI Blog",
    "MIT Technology Review",
    "Anthropic News",
    "JiQiZhiXin",  # China AI news
]

def main():
    print("\n" + "="*70)
    print("Enabling Data Sources for Collection")
    print("="*70)
    
    session = get_session()
    
    try:
        # Get all sources
        all_sources = session.query(DataSource).all()
        
        print(f"\nTotal sources in database: {len(all_sources)}")
        enabled_before = sum(1 for s in all_sources if s.is_enabled)
        print(f"Currently enabled: {enabled_before}")
        
        # Enable target sources
        enabled_count = 0
        print("\nEnabling sources:")
        print("-" * 70)
        
        for source in all_sources:
            if source.name in SOURCES_TO_ENABLE:
                if not source.is_enabled:
                    source.is_enabled = True
                    print(f"  [ENABLED] {source.name:40} (priority: {source.priority})")
                    enabled_count += 1
                else:
                    print(f"  [ALREADY] {source.name:40} (priority: {source.priority})")
        
        # Commit changes
        session.commit()
        
        print("\n" + "-" * 70)
        print(f"\nEnabled: {enabled_count} sources")
        
        # Show final stats
        all_sources_updated = session.query(DataSource).all()
        enabled_after = sum(1 for s in all_sources_updated if s.is_enabled)
        
        print(f"Before: {enabled_before} sources enabled")
        print(f"After:  {enabled_after} sources enabled")
        
        print("\nNow run collection to get more data:")
        print("  python scripts/collection/collect_news.py")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
