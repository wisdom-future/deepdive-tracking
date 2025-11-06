#!/usr/bin/env python3
"""查看数据库中的数据"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_session
from src.models import RawNews, ProcessedNews, DataSource
from sqlalchemy import func, desc

def main():
    session = get_session()
    
    print("\n" + "="*70)
    print("数据库数据统计")
    print("="*70)
    
    # 统计原始新闻
    total_raw = session.query(func.count(RawNews.id)).scalar()
    pending_raw = session.query(func.count(RawNews.id)).filter(RawNews.status == 'pending').scalar()
    processed_raw = session.query(func.count(RawNews.id)).filter(RawNews.status == 'processed').scalar()
    
    print(f"\n原始新闻 (raw_news):")
    print(f"  总数: {total_raw}")
    print(f"  待处理: {pending_raw}")
    print(f"  已处理: {processed_raw}")
    
    # 统计已处理新闻
    total_processed = session.query(func.count(ProcessedNews.id)).scalar()
    print(f"\n已处理新闻 (processed_news):")
    print(f"  总数: {total_processed}")
    
    # 统计数据源
    total_sources = session.query(func.count(DataSource.id)).scalar()
    enabled_sources = session.query(func.count(DataSource.id)).filter(DataSource.is_enabled == True).scalar()
    print(f"\n数据源 (data_sources):")
    print(f"  总数: {total_sources}")
    print(f"  已启用: {enabled_sources}")
    
    # 显示最新的10条原始新闻
    print(f"\n" + "="*70)
    print("最新采集的10条新闻")
    print("="*70)
    recent_news = session.query(RawNews)\
        .order_by(desc(RawNews.created_at))\
        .limit(10).all()
    
    for i, news in enumerate(recent_news, 1):
        print(f"\n{i}. [{news.status}] {news.title[:60]}...")
        print(f"   来源: {news.source}")
        print(f"   采集时间: {news.created_at}")
        if news.url:
            print(f"   URL: {news.url[:70]}...")
    
    # 按来源统计
    print(f"\n" + "="*70)
    print("新闻来源分布")
    print("="*70)
    source_stats = session.query(
        RawNews.source,
        func.count(RawNews.id).label('count')
    ).group_by(RawNews.source).all()
    
    for source, count in source_stats:
        print(f"  {source}: {count}条")
    
    session.close()
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
