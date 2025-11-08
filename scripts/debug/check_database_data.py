#!/usr/bin/env python3
"""
检查GCP数据库实际数据情况
诊断用户在CLAUDE.md中提到的3个致命问题
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.database.connection import get_session
from src.models import RawNews, DataSource, ProcessedNews
from sqlalchemy import func, and_
from datetime import datetime, timedelta

def main():
    print("="*80)
    print("GCP数据库数据完整性检查")
    print("="*80)

    session = get_session()

    try:
        # 问题1: 检查内容是否完整
        print("\n[问题1检查] 内容完整性")
        print("-"*80)

        total_raw = session.query(func.count(RawNews.id)).scalar()
        print(f"总新闻数: {total_raw}")

        # 检查content字段
        has_content = session.query(func.count(RawNews.id)).filter(
            RawNews.content.isnot(None),
            RawNews.content != ""
        ).scalar()
        print(f"有content的新闻: {has_content}/{total_raw}")

        # 检查content长度
        avg_length = session.query(func.avg(func.length(RawNews.content))).filter(
            RawNews.content.isnot(None)
        ).scalar()
        print(f"平均content长度: {avg_length:.0f if avg_length else 0} 字符")

        # 采样查看
        sample = session.query(RawNews).limit(3).all()
        print(f"\n采样3条数据:")
        for i, news in enumerate(sample, 1):
            print(f"\n  [{i}] ID: {news.id}")
            print(f"      标题: {news.title[:50]}...")
            print(f"      URL: {news.url[:60]}...")
            print(f"      Content长度: {len(news.content) if news.content else 0}")
            print(f"      Author: {news.author or 'N/A'}")
            print(f"      Published: {news.published_at}")

        # 问题2: 检查source_id引用
        print("\n\n[问题2检查] source_id引用完整性")
        print("-"*80)

        has_source_id = session.query(func.count(RawNews.id)).filter(
            RawNews.source_id.isnot(None)
        ).scalar()
        print(f"有source_id的新闻: {has_source_id}/{total_raw}")

        # 按source_id统计
        by_source = session.query(
            RawNews.source_id,
            DataSource.name,
            func.count(RawNews.id).label('count')
        ).join(
            DataSource, RawNews.source_id == DataSource.id
        ).group_by(RawNews.source_id, DataSource.name).all()

        print(f"\n按数据源统计:")
        for source_id, source_name, count in by_source:
            print(f"  源 {source_id} ({source_name}): {count} 条")

        # 问题3: 检查去重情况
        print("\n\n[问题3检查] 去重情况")
        print("-"*80)

        # 检查hash重复
        duplicate_hashes = session.query(
            RawNews.hash,
            func.count(RawNews.id).label('count')
        ).group_by(RawNews.hash).having(
            func.count(RawNews.id) > 1
        ).all()

        print(f"重复的hash数量: {len(duplicate_hashes)}")
        if duplicate_hashes:
            print(f"前5个重复hash:")
            for hash_val, count in duplicate_hashes[:5]:
                print(f"  Hash {hash_val[:16]}...: {count} 条重复")
                # 显示重复的记录
                dupes = session.query(RawNews).filter(RawNews.hash == hash_val).limit(3).all()
                for news in dupes:
                    print(f"    - ID {news.id}: {news.title[:40]}... ({news.created_at})")

        # 检查simhash
        has_simhash = session.query(func.count(RawNews.id)).filter(
            RawNews.content_simhash.isnot(None)
        ).scalar()
        print(f"\n有content_simhash的新闻: {has_simhash}/{total_raw}")

        # 检查is_duplicate标记
        marked_duplicate = session.query(func.count(RawNews.id)).filter(
            RawNews.is_duplicate == True
        ).scalar()
        print(f"标记为duplicate的新闻: {marked_duplicate}")

        # 最近24小时的数据
        print("\n\n[最近24小时数据]")
        print("-"*80)
        time_threshold = datetime.now() - timedelta(hours=24)
        recent_count = session.query(func.count(RawNews.id)).filter(
            RawNews.created_at >= time_threshold
        ).scalar()
        print(f"最近24小时新闻: {recent_count}")

        # 检查这些数据的processed状态
        recent_processed = session.query(func.count(ProcessedNews.id)).join(
            RawNews, ProcessedNews.raw_news_id == RawNews.id
        ).filter(
            RawNews.created_at >= time_threshold
        ).scalar()
        print(f"已被AI处理: {recent_processed}/{recent_count}")

        # 显示最近的重复数据
        recent_duplicates = session.query(
            RawNews.title,
            func.count(RawNews.id).label('count')
        ).filter(
            RawNews.created_at >= time_threshold
        ).group_by(RawNews.title).having(
            func.count(RawNews.id) > 1
        ).all()

        if recent_duplicates:
            print(f"\n最近24小时的重复标题 ({len(recent_duplicates)} 个):")
            for title, count in recent_duplicates[:10]:
                print(f"  {count}x: {title[:60]}...")

        print("\n\n" + "="*80)
        print("检查完成")
        print("="*80)

    finally:
        session.close()

if __name__ == "__main__":
    main()
