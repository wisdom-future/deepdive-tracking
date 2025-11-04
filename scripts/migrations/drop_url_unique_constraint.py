#!/usr/bin/env python3
"""Drop URL unique constraint from raw_news table."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from sqlalchemy import text
from src.database.connection import get_session

def main():
    """Drop the unique constraint on raw_news.url field."""
    print("=" * 80)
    print("DATABASE MIGRATION: Drop URL Unique Constraint")
    print("=" * 80)
    print()

    session = get_session()

    try:
        print("Dropping constraint raw_news_url_key...")
        session.execute(text("ALTER TABLE raw_news DROP CONSTRAINT IF EXISTS raw_news_url_key;"))
        session.commit()
        print("✅ Successfully dropped URL unique constraint")
        print()
        print("Migration completed successfully!")
        return 0

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        session.rollback()
        return 1
    finally:
        session.close()

if __name__ == "__main__":
    sys.exit(main())
