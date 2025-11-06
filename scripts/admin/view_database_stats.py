#!/usr/bin/env python3
"""查看数据库统计信息和最新数据"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_session
from src.models import RawNews, ProcessedNews, DataSource
from sqlalchemy import func, desc
from datetime import datetime


def main():
    """Display database statistics and recent data"""
    print("\n" + "=" * 80)
    print("数据库数据统计 (Database Statistics)")
    print("=" * 80)
    print()

    session = get_session()

    try:
        # Raw News Statistics
        print("【原始新闻统计 (Raw News)】")
        total_raw = session.query(func.count(RawNews.id)).scalar()
        pending_raw = session.query(func.count(RawNews.id)).filter(
            RawNews.status == 'pending'
        ).scalar()
        processed_raw = session.query(func.count(RawNews.id)).filter(
            RawNews.status == 'processed'
        ).scalar()
        failed_raw = session.query(func.count(RawNews.id)).filter(
            RawNews.status == 'failed'
        ).scalar()

        print(f"  总数: {total_raw}")
        print(f"  待处理 (pending): {pending_raw}")
        print(f"  已处理 (processed): {processed_raw}")
        print(f"  失败 (failed): {failed_raw}")
        print()

        # Processed News Statistics
        print("【已处理新闻统计 (Processed News)】")
        total_processed = session.query(func.count(ProcessedNews.id)).scalar()
        print(f"  总数: {total_processed}")
        print()

        # Data Sources
        print("【数据源统计 (Data Sources)】")
        sources = session.query(DataSource).all()
        print(f"  总数: {len(sources)}")
        for source in sources[:10]:  # Show first 10
            status = "启用" if source.enabled else "禁用"
            print(f"  - {source.name} ({source.source_type}): {status}")
        print()

        # Recent Raw News (last 20)
        print("【最新原始新闻 (Recent Raw News - Last 20)】")
        recent_news = session.query(RawNews).order_by(
            desc(RawNews.created_at)
        ).limit(20).all()

        for i, news in enumerate(recent_news, 1):
            created = news.created_at.strftime("%Y-%m-%d %H:%M") if news.created_at else "N/A"
            title = news.title[:70] + "..." if len(news.title) > 70 else news.title
            print(f"  {i}. [{news.status}] {title}")
            print(f"     ID: {news.id} | 创建时间: {created}")
            if news.source_url:
                print(f"     来源: {news.source_url[:80]}")
            print()

        # Recent Processed News (if any)
        if total_processed > 0:
            print("【最新已处理新闻 (Recent Processed News - Last 10)】")
            recent_processed = session.query(ProcessedNews).order_by(
                desc(ProcessedNews.created_at)
            ).limit(10).all()

            for i, proc in enumerate(recent_processed, 1):
                raw_news = session.query(RawNews).filter(
                    RawNews.id == proc.raw_news_id
                ).first()
                title = raw_news.title[:70] if raw_news else "N/A"
                print(f"  {i}. [分数: {proc.score}] {title}")
                print(f"     类别: {proc.category} | 置信度: {proc.confidence:.2f}")
                print()

        # Source Distribution
        print("【新闻来源分布 (Source Distribution)】")
        source_dist = session.query(
            RawNews.source_url,
            func.count(RawNews.id).label('count')
        ).group_by(RawNews.source_url).order_by(desc('count')).limit(10).all()

        for source, count in source_dist:
            source_name = source[:60] + "..." if source and len(source) > 60 else source
            print(f"  - {source_name}: {count} 篇")
        print()

        print("=" * 80)
        print("✅ 查询完成")
        print("=" * 80)
        print()

        return 0

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
