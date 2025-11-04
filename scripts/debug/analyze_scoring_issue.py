#!/usr/bin/env python3
"""
Analyze Scoring Issue - 分析评分问题

分析当前数据库状态，找出评分问题的根本原因
"""

import sys
import io
from pathlib import Path
from datetime import datetime, timedelta

# 修复 Windows 编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_session
from src.models import RawNews, ProcessedNews
from sqlalchemy import func, desc

def main():
    """Main analysis function"""
    session = get_session()

    print("\n" + "="*80)
    print("DeepDive Tracking - Scoring Issue Analysis")
    print("="*80)
    print()

    try:
        # 1. Raw News统计
        print("[1] Raw News 数据统计")
        print("-" * 80)

        total_raw = session.query(func.count(RawNews.id)).scalar()
        print(f"总数: {total_raw}")
        print()

        # 按来源统计
        print("按来源分布:")
        source_dist = session.query(
            RawNews.source_name,
            func.count(RawNews.id).label('count')
        ).group_by(RawNews.source_name).order_by(desc('count')).limit(10).all()

        for source, count in source_dist:
            print(f"  {source:30} {count:5} 条")
        print()

        # 按日期统计
        print("按日期分布:")
        recent_days = datetime.now() - timedelta(days=7)
        date_dist = session.query(
            func.date(RawNews.created_at).label('date'),
            func.count(RawNews.id).label('count')
        ).filter(
            RawNews.created_at >= recent_days
        ).group_by('date').order_by(desc('date')).all()

        for date, count in date_dist:
            print(f"  {date}: {count} 条")
        print()

        # 2. Processed News统计
        print("[2] Processed News 数据统计")
        print("-" * 80)

        total_processed = session.query(func.count(ProcessedNews.id)).scalar()
        print(f"总数: {total_processed}")
        print()

        # 按分数分布
        print("按分数分布:")
        score_dist = session.query(
            ProcessedNews.score,
            func.count(ProcessedNews.id).label('count')
        ).group_by(ProcessedNews.score).order_by(desc('count')).limit(10).all()

        for score, count in score_dist:
            print(f"  {score:.1f} 分: {count} 条")
        print()

        # 按类别分布
        print("按类别分布:")
        category_dist = session.query(
            ProcessedNews.category,
            func.count(ProcessedNews.id).label('count')
        ).group_by(ProcessedNews.category).order_by(desc('count')).all()

        for category, count in category_dist:
            print(f"  {category:30} {count:5} 条")
        print()

        # 3. 关联查询 - ProcessedNews的来源分布
        print("[3] Processed News 的来源分布（通过关联 RawNews）")
        print("-" * 80)

        processed_sources = session.query(
            RawNews.source_name,
            func.count(ProcessedNews.id).label('count')
        ).join(
            ProcessedNews, RawNews.id == ProcessedNews.raw_news_id
        ).group_by(
            RawNews.source_name
        ).order_by(desc('count')).all()

        if processed_sources:
            for source, count in processed_sources:
                print(f"  {source:30} {count:5} 条")
        else:
            print("  无数据")
        print()

        # 4. 未评分的文章
        print("[4] 未评分文章统计")
        print("-" * 80)

        unscored_count = session.query(func.count(RawNews.id)).filter(
            ~RawNews.id.in_(
                session.query(ProcessedNews.raw_news_id)
            )
        ).scalar()

        print(f"未评分总数: {unscored_count}")
        print()

        # 未评分文章的来源分布
        print("未评分文章的来源分布 (Top 10):")
        unscored_sources = session.query(
            RawNews.source_name,
            func.count(RawNews.id).label('count')
        ).filter(
            ~RawNews.id.in_(
                session.query(ProcessedNews.raw_news_id)
            )
        ).group_by(RawNews.source_name).order_by(desc('count')).limit(10).all()

        for source, count in unscored_sources:
            print(f"  {source:30} {count:5} 条")
        print()

        # 5. 最近的ProcessedNews记录详情
        print("[5] 最近 5 条 ProcessedNews 详情")
        print("-" * 80)

        recent_processed = session.query(ProcessedNews).order_by(
            desc(ProcessedNews.created_at)
        ).limit(5).all()

        for pn in recent_processed:
            raw = session.query(RawNews).filter(RawNews.id == pn.raw_news_id).first()
            if raw:
                print(f"ID: {pn.id}")
                print(f"  Raw News ID: {pn.raw_news_id}")
                print(f"  来源: {raw.source_name}")
                print(f"  标题: {raw.title[:60]}...")
                print(f"  分数: {pn.score}")
                print(f"  类别: {pn.category}")
                print(f"  创建时间: {pn.created_at}")
                print()

        # 6. 诊断结果
        print("="*80)
        print("[诊断结果]")
        print("="*80)
        print()

        # 检查1: 是否所有processed news来自同一个源
        if processed_sources:
            unique_sources = len(processed_sources)
            dominant_source_pct = (processed_sources[0][1] / total_processed * 100) if total_processed > 0 else 0

            print(f"✓ Processed news 涉及 {unique_sources} 个不同来源")
            print(f"✓ 最主要来源占比: {dominant_source_pct:.1f}% ({processed_sources[0][0]})")

            if unique_sources == 1:
                print("⚠️  问题: 所有已评分文章都来自同一个源！")
            elif dominant_source_pct > 80:
                print("⚠️  问题: 已评分文章来源过于集中！")

        # 检查2: 是否所有分数都相同
        if score_dist:
            if len(score_dist) == 1:
                print(f"⚠️  问题: 所有文章分数都是 {score_dist[0][0]}！")
            else:
                print(f"✓ 分数有 {len(score_dist)} 个不同值")

        # 检查3: 未评分文章是否有多样的来源
        if unscored_sources:
            print(f"✓ 未评分文章涉及 {len(unscored_sources)} 个不同来源")
            print(f"✓ 最多的未评分来源: {unscored_sources[0][0]} ({unscored_sources[0][1]} 条)")

        # 检查4: 评分覆盖率
        coverage = (total_processed / total_raw * 100) if total_raw > 0 else 0
        print(f"✓ 评分覆盖率: {coverage:.1f}% ({total_processed}/{total_raw})")

        if coverage < 5:
            print("⚠️  问题: 评分覆盖率过低！需要大量评分工作")

        print()
        print("="*80)
        print("分析完成")
        print("="*80)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
