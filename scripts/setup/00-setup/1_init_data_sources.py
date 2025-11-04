#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Add additional data sources for news collection."""

import sys
import io
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Fix encoding on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.models import DataSource
from datetime import datetime

# Define new sources to add (based on product requirements)
new_sources = [
    {
        'name': 'Google DeepMind Blog',
        'description': 'Official blog of Google DeepMind',
        'type': 'rss',
        'url': 'https://deepmind.google/feed.xml',
        'method': 'GET',
        'priority': 9,
        'is_enabled': True,
    },
    {
        'name': 'Meta AI Research',
        'description': 'Meta AI research and updates',
        'type': 'rss',
        'url': 'https://ai.facebook.com/feed.xml',
        'method': 'GET',
        'priority': 8,
        'is_enabled': True,
    },
    {
        'name': 'Microsoft AI Blog',
        'description': 'Microsoft AI and Research blog',
        'type': 'rss',
        'url': 'https://www.microsoft.com/en-us/ai/ai-update-feed',
        'method': 'GET',
        'priority': 8,
        'is_enabled': True,
    },
    {
        'name': 'NVIDIA AI Blog',
        'description': 'NVIDIA AI and deep learning blog',
        'type': 'rss',
        'url': 'https://blogs.nvidia.com/ai/feed/',
        'method': 'GET',
        'priority': 8,
        'is_enabled': True,
    },
    {
        'name': 'TechCrunch AI',
        'description': 'TechCrunch AI news and analysis',
        'type': 'rss',
        'url': 'https://techcrunch.com/category/artificial-intelligence/feed/',
        'method': 'GET',
        'priority': 7,
        'is_enabled': True,
    },
    {
        'name': 'The Verge AI',
        'description': 'The Verge AI and technology news',
        'type': 'rss',
        'url': 'https://www.theverge.com/rss/index.xml',
        'method': 'GET',
        'priority': 7,
        'is_enabled': True,
    },
    {
        'name': 'MIT Technology Review',
        'description': 'MIT Technology Review AI and science',
        'type': 'rss',
        'url': 'https://www.technologyreview.com/ai/feed/',
        'method': 'GET',
        'priority': 8,
        'is_enabled': True,
    },
    {
        'name': 'VentureBeat AI',
        'description': 'VentureBeat AI news and insights',
        'type': 'rss',
        'url': 'https://venturebeat.com/category/ai/feed/',
        'method': 'GET',
        'priority': 7,
        'is_enabled': True,
    },
    {
        'name': 'ArXiv CS.AI',
        'description': 'ArXiv computer science AI papers',
        'type': 'api',
        'url': 'https://arxiv.org/list/cs.AI/recent',
        'method': 'GET',
        'priority': 9,
        'is_enabled': True,
    },
    {
        'name': 'Papers with Code',
        'description': 'Latest papers with code implementation',
        'type': 'api',
        'url': 'https://paperswithcode.com/api/papers',
        'method': 'GET',
        'priority': 8,
        'is_enabled': True,
    },
    {
        'name': 'JiQiZhiXin',
        'description': 'China - AI news and research',
        'type': 'rss',
        'url': 'https://www.jiqizhixin.com/rss',
        'method': 'GET',
        'priority': 7,
        'is_enabled': True,
    },
    {
        'name': 'QuantumBit',
        'description': 'China - AI and quantum computing news',
        'type': 'rss',
        'url': 'https://www.qbitai.com/feed',
        'method': 'GET',
        'priority': 7,
        'is_enabled': True,
    },
]

# Fix encoding issue
sources_to_add = []
for source_data in new_sources:
    if '名称' in source_data:
        source_data['name'] = source_data.pop('名称')
    sources_to_add.append(source_data)

print(f"=== 添加 {len(sources_to_add)} 个新数据源 ===\n")

session = SessionLocal()
added_count = 0

try:
    # 获取现有源的ID范围
    existing = session.query(DataSource).all()
    existing_names = {ds.name for ds in existing}
    existing_urls = {ds.url for ds in existing}

    print(f"现有源: {len(existing)}\n")

    for source_data in sources_to_add:
        name = source_data.get('name')
        url = source_data.get('url')

        # Skip if already exists
        if name in existing_names or url in existing_urls:
            print(f"跳过 (已存在): {name}")
            continue

        try:
            source = DataSource(**source_data)
            session.add(source)
            added_count += 1
            print(f"[OK] Add: {name}")
        except Exception as e:
            print(f"[ERROR] {name}: {e}")

    session.commit()
    print(f"\n=== 添加完成 ===")
    print(f"成功添加: {added_count} 个源")

    # 显示最终统计
    final_count = session.query(DataSource).count()
    print(f"总源数: {final_count}")

except Exception as e:
    session.rollback()
    print(f"数据库错误: {e}")
finally:
    session.close()
