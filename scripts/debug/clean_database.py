#!/usr/bin/env python3
"""
清理GCP数据库 - 删除所有测试数据
用于端到端测试前的数据库重置
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.database.connection import get_session
from src.models import RawNews, ProcessedNews, PublishedContent, CostLog
from sqlalchemy import text

def main():
    print("="*80)
    print("GCP数据库清理")
    print("="*80)
    print("\n⚠️  警告：这将删除所有raw_news、processed_news、published_content数据！")
    print("保留data_sources配置\n")

    session = get_session()

    try:
        # 统计当前数据
        raw_count = session.query(RawNews).count()
        processed_count = session.query(ProcessedNews).count()
        published_count = session.query(PublishedContent).count()

        print(f"当前数据统计:")
        print(f"  - raw_news: {raw_count} 条")
        print(f"  - processed_news: {processed_count} 条")
        print(f"  - published_content: {published_count} 条")
        print()

        # 删除数据（保持表结构）
        print("开始清理...")

        # 1. 删除published_content（有外键依赖）
        deleted_published = session.query(PublishedContent).delete()
        print(f"  ✓ 删除published_content: {deleted_published} 条")

        # 2. 删除processed_news（有外键依赖raw_news）
        deleted_processed = session.query(ProcessedNews).delete()
        print(f"  ✓ 删除processed_news: {deleted_processed} 条")

        # 3. 删除cost_log
        deleted_cost = session.query(CostLog).delete()
        print(f"  ✓ 删除cost_log: {deleted_cost} 条")

        # 4. 删除raw_news
        deleted_raw = session.query(RawNews).delete()
        print(f"  ✓ 删除raw_news: {deleted_raw} 条")

        # 提交事务
        session.commit()

        print("\n" + "="*80)
        print("✅ 数据库清理完成！")
        print("="*80)

        # 验证清理结果
        raw_count_after = session.query(RawNews).count()
        processed_count_after = session.query(ProcessedNews).count()

        print(f"\n清理后数据统计:")
        print(f"  - raw_news: {raw_count_after} 条")
        print(f"  - processed_news: {processed_count_after} 条")

        if raw_count_after == 0 and processed_count_after == 0:
            print("\n✅ 验证通过：数据库已完全清空")
            return 0
        else:
            print("\n⚠️  警告：部分数据未清理")
            return 1

    except Exception as e:
        print(f"\n❌ 清理失败: {e}")
        session.rollback()
        return 1

    finally:
        session.close()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
