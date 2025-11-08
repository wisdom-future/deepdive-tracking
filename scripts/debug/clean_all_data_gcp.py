#!/usr/bin/env python3
"""
通过GCP API清空数据库所有数据
用于端到端测试前的完全重置
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import asyncio
from src.database.connection import get_session
from src.models import RawNews, ProcessedNews, PublishedContent, CostLog
from sqlalchemy import text

async def main():
    print("\n" + "="*80)
    print("GCP 数据库完全清空")
    print("="*80)
    print("\n⚠️  警告：这将删除所有数据！")

    session = get_session()

    try:
        # 统计当前数据
        raw_count = session.query(RawNews).count()
        processed_count = session.query(ProcessedNews).count()
        published_count = session.query(PublishedContent).count()
        cost_count = session.query(CostLog).count()

        print(f"\n当前数据统计:")
        print(f"  - raw_news: {raw_count} 条")
        print(f"  - processed_news: {processed_count} 条")
        print(f"  - published_content: {published_count} 条")
        print(f"  - cost_log: {cost_count} 条")
        print()

        # 删除数据（按外键依赖顺序）
        print("开始清空数据...")

        # 1. 删除published_content
        deleted = session.query(PublishedContent).delete()
        print(f"  ✓ 删除 published_content: {deleted} 条")

        # 2. 删除processed_news
        deleted = session.query(ProcessedNews).delete()
        print(f"  ✓ 删除 processed_news: {deleted} 条")

        # 3. 删除cost_log
        deleted = session.query(CostLog).delete()
        print(f"  ✓ 删除 cost_log: {deleted} 条")

        # 4. 删除raw_news
        deleted = session.query(RawNews).delete()
        print(f"  ✓ 删除 raw_news: {deleted} 条")

        # 提交
        session.commit()

        print("\n" + "="*80)
        print("✅ 数据库清空完成！")
        print("="*80)

        # 验证
        raw_count = session.query(RawNews).count()
        processed_count = session.query(ProcessedNews).count()

        print(f"\n清空后验证:")
        print(f"  - raw_news: {raw_count} 条")
        print(f"  - processed_news: {processed_count} 条")

        if raw_count == 0 and processed_count == 0:
            print("\n✅ 验证通过：数据库已完全清空")
            return 0
        else:
            print("\n⚠️  警告：部分数据未清理")
            return 1

    except Exception as e:
        print(f"\n❌ 清空失败: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
