#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速查看数据库摘要和TOP 10新闻"""

import sys
import io
sys.path.insert(0, '.')

# Fix encoding on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from sqlalchemy import create_engine, text
from datetime import datetime

db_url = 'sqlite:///data/db/deepdive_tracking.db'
engine = create_engine(db_url)

print("\n" + "=" * 80)
print("DeepDive Tracking - Database Summary")
print("=" * 80)

with engine.connect() as conn:
    # 1. Raw News 统计
    print("\n[1] RAW_NEWS Table Summary")
    print("-" * 80)

    result = conn.execute(text('''
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status='raw' THEN 1 END) as raw_count,
            COUNT(CASE WHEN status='processed' THEN 1 END) as processed_count,
            COUNT(CASE WHEN author IS NOT NULL AND author != '' THEN 1 END) as with_author,
            ROUND(AVG(LENGTH(content))) as avg_content_len,
            COUNT(DISTINCT source_name) as unique_sources
        FROM raw_news
    '''))

    row = result.fetchone()
    print(f"Total articles:       {row[0]}")
    print(f"  - Status 'raw':     {row[1]} (待处理)")
    print(f"  - Status 'proc':    {row[2]} (已评分)")
    print(f"  - With author:      {row[3]} ({row[3]/row[0]*100:.1f}%)")
    print(f"Avg content length:   {row[4]} chars")
    print(f"Unique sources:       {row[5]}")

    # 2. Processed News 统计
    print("\n[2] PROCESSED_NEWS Table Summary")
    print("-" * 80)

    result = conn.execute(text('''
        SELECT
            COUNT(*) as total,
            ROUND(AVG(score)) as avg_score,
            COUNT(DISTINCT category) as unique_categories
        FROM processed_news
    '''))

    row = result.fetchone()
    if row[0] > 0:
        print(f"Total scored:         {row[0]}")
        print(f"Avg score:            {row[1]}/100")
        print(f"Unique categories:    {row[2]}")
    else:
        print("No scored news yet")

    # 3. Data Sources 统计
    print("\n[3] DATA_SOURCES Configuration")
    print("-" * 80)

    result = conn.execute(text('''
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN is_enabled THEN 1 END) as enabled,
            COUNT(CASE WHEN default_author IS NOT NULL THEN 1 END) as with_default_author
        FROM data_sources
    '''))

    row = result.fetchone()
    print(f"Total sources:        {row[0]}")
    print(f"Enabled:              {row[1]}")
    print(f"With default author:  {row[2]}")

    # 4. TOP 10 最新新闻
    print("\n[4] TOP 10 Latest News")
    print("-" * 80)

    result = conn.execute(text('''
        SELECT
            title,
            source_name,
            author,
            LENGTH(content) as content_len,
            language,
            status,
            fetched_at
        FROM raw_news
        ORDER BY fetched_at DESC
        LIMIT 10
    '''))

    rows = result.fetchall()
    for i, (title, source, author, content_len, language, status, fetched_at) in enumerate(rows, 1):
        print(f"\n{i}. {title[:70]}")
        print(f"   Source: {source:<30} | Lang: {language} | Status: {status}")
        print(f"   Author: {author if author else '(none)' :<50} | Content: {content_len} chars")
        if fetched_at:
            print(f"   Fetched: {fetched_at}")

    # 5. 按来源的统计
    print("\n" + "=" * 80)
    print("[5] Statistics by Data Source")
    print("-" * 80)

    result = conn.execute(text('''
        SELECT
            source_name,
            COUNT(*) as total,
            COUNT(CASE WHEN author IS NOT NULL AND author != '' THEN 1 END) as with_author,
            ROUND(AVG(LENGTH(content))) as avg_content_len
        FROM raw_news
        GROUP BY source_name
        ORDER BY total DESC
    '''))

    print(f"{'Source':<30} | {'Total':<6} | {'Author %':<10} | {'Avg Len':<8}")
    print("-" * 80)

    for source, total, with_author, avg_len in result.fetchall():
        author_pct = (with_author / total * 100) if total > 0 else 0
        print(f"{source:<30} | {total:<6} | {author_pct:>8.1f}% | {avg_len:>7.0f}")

    # 6. 快速查询命令
    print("\n" + "=" * 80)
    print("[6] Quick Query Commands")
    print("-" * 80)
    print("""
sqlite3 data/db/deepdive_tracking.db

# View recent articles with all details
SELECT * FROM raw_news ORDER BY fetched_at DESC LIMIT 5;

# View scored articles
SELECT * FROM processed_news LIMIT 5;

# View data sources
SELECT name, type, is_enabled, default_author FROM data_sources;

# Find articles without author
SELECT source_name, title FROM raw_news WHERE author IS NULL OR author = '';

# Check content length distribution
SELECT
  CASE
    WHEN LENGTH(content) < 100 THEN 'too short'
    WHEN LENGTH(content) < 500 THEN 'short'
    WHEN LENGTH(content) < 2000 THEN 'medium'
    ELSE 'long'
  END as length_category,
  COUNT(*) as count
FROM raw_news
GROUP BY length_category;
    """)

    # 7. 总结
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    # 重新计算总体统计
    result = conn.execute(text('''
        SELECT
            COUNT(*) as total_articles,
            COUNT(CASE WHEN status='processed' THEN 1 END) as scored_articles
        FROM raw_news
    '''))

    total, scored = result.fetchone()
    print(f"Collection Status: {total} articles, {scored} scored ({scored/total*100 if total > 0 else 0:.1f}%)")

    result = conn.execute(text('''
        SELECT
            COUNT(CASE WHEN author IS NOT NULL AND author != '' THEN 1 END) as with_author
        FROM raw_news
    '''))

    with_author = result.scalar()
    print(f"Metadata Quality:  {with_author} articles have author ({with_author/total*100 if total > 0 else 0:.1f}%)")

    print("\n✓ Ready for P1-3 end-to-end testing!")
    print("=" * 80 + "\n")
