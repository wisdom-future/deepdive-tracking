#!/usr/bin/env python3
"""Data quality verification script - checks html_content, content, duplicates, author fields."""

import sys
sys.path.insert(0, '/workspace')

from src.database.connection import get_session
from src.models import RawNews
from sqlalchemy import func, desc

def main():
    session = get_session()

    print("=" * 80)
    print("DATA QUALITY VERIFICATION REPORT")
    print("=" * 80)
    print()

    # 1. Check total records
    total = session.query(func.count(RawNews.id)).scalar()
    print(f"✅ Total raw_news records: {total}")
    print()

    # 2. Check html_content population
    html_content_not_null = session.query(func.count(RawNews.id)).filter(
        RawNews.html_content != None,
        RawNews.html_content != ''
    ).scalar()
    html_content_null = total - html_content_not_null
    print(f"📄 html_content field:")
    print(f"   - Populated: {html_content_not_null} ({html_content_not_null/total*100:.1f}%)")
    print(f"   - NULL/Empty: {html_content_null} ({html_content_null/total*100:.1f}%)")
    print()

    # 3. Check content population and length
    content_not_null = session.query(func.count(RawNews.id)).filter(
        RawNews.content != None,
        RawNews.content != ''
    ).scalar()
    content_null = total - content_not_null
    print(f"📝 content field:")
    print(f"   - Populated: {content_not_null} ({content_not_null/total*100:.1f}%)")
    print(f"   - NULL/Empty: {content_null} ({content_null/total*100:.1f}%)")
    print()

    # Check average content length
    avg_length = session.query(func.avg(func.length(RawNews.content))).filter(
        RawNews.content != None
    ).scalar()
    print(f"   - Average length: {avg_length:.0f} chars")
    print()

    # 4. Check duplicate detection
    duplicates = session.query(func.count(RawNews.id)).filter(
        RawNews.is_duplicate == True
    ).scalar()
    unique = total - duplicates
    print(f"🔍 Duplicate detection:")
    print(f"   - Unique records: {unique} ({unique/total*100:.1f}%)")
    print(f"   - Duplicates marked: {duplicates} ({duplicates/total*100:.1f}%)")
    print()

    # 5. Check author field
    author_not_null = session.query(func.count(RawNews.id)).filter(
        RawNews.author != None,
        RawNews.author != ''
    ).scalar()
    author_null = total - author_not_null
    print(f"👤 author field:")
    print(f"   - Populated: {author_not_null} ({author_not_null/total*100:.1f}%)")
    print(f"   - NULL/Empty: {author_null} ({author_null/total*100:.1f}%)")
    print()

    # 6. Sample latest 3 records
    print("=" * 80)
    print("LATEST 3 RECORDS SAMPLE (to verify fixes)")
    print("=" * 80)
    latest_records = session.query(RawNews).order_by(desc(RawNews.id)).limit(3).all()
    for idx, record in enumerate(latest_records, 1):
        print(f"\n[Record {idx}]")
        print(f"ID: {record.id}")
        print(f"Title: {record.title[:80]}")
        print(f"URL: {record.url}")
        print(f"Source: {record.source_name}")
        print(f"Author: {record.author if record.author else '(empty)'}")
        print(f"Is Duplicate: {record.is_duplicate}")
        print(f"Content length: {len(record.content) if record.content else 0} chars")
        print(f"HTML Content length: {len(record.html_content) if record.html_content else 0} chars")
        print(f"Content preview (first 100 chars):")
        print(f"   {record.content[:100] if record.content else '(NULL)'}")

    session.close()
    print()
    print("=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
