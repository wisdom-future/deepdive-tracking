#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Configure default author for data sources that don't provide author info."""

import sys
import io
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Fix encoding on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.models import DataSource

# Mapping of source names to default authors
DEFAULT_AUTHORS = {
    "OpenAI Blog": "OpenAI Team",
    "Anthropic News": "Anthropic Team",
    "HackerNews": "Hacker News Community",
    "Real News Aggregator": "News Aggregator",
}

print("=" * 70)
print("配置数据源的默认 Author")
print("=" * 70)

session = SessionLocal()
updated_count = 0

try:
    for source_name, default_author in DEFAULT_AUTHORS.items():
        source = session.query(DataSource).filter(
            DataSource.name == source_name
        ).first()

        if not source:
            print(f"\n⚠️  源未找到: {source_name}")
            continue

        # Check if already has default_author
        if source.default_author:
            print(f"\n✓ {source_name}")
            print(f"  Already configured: {source.default_author}")
            continue

        # Set default author
        source.default_author = default_author
        updated_count += 1
        print(f"\n✓ {source_name}")
        print(f"  → {default_author}")

    # Commit changes
    if updated_count > 0:
        session.commit()
        print(f"\n{'=' * 70}")
        print(f"已更新 {updated_count} 个数据源的默认 Author")
        print(f"{'=' * 70}")
    else:
        print(f"\n{'=' * 70}")
        print(f"所有源都已配置 (无需更新)")
        print(f"{'=' * 70}")

    # Show final state
    print("\n最终状态:")
    print("-" * 70)
    sources = session.query(DataSource).all()
    for source in sources:
        if source.default_author:
            print(f"  {source.name:<30} -> {source.default_author}")

except Exception as e:
    session.rollback()
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
