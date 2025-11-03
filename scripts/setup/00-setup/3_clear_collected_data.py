#!/usr/bin/env python3
"""
Clear Collected Data - 清空历史采集数据

用途：
  - 清空 raw_news 表（所有采集的原始新闻）
  - 清空 processed_news 表（所有评分结果）
  - 保留 data_sources 配置

警告：
  这个操作是不可逆的！
  清空后将无法恢复历史数据。
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_settings

def main():
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)

    print("\n" + "=" * 80)
    print("清空历史采集数据")
    print("=" * 80)
    print()
    print("警告: 这个操作将删除:")
    print("  1. raw_news 表中的所有采集数据")
    print("  2. processed_news 表中的所有评分结果")
    print()
    print("数据源配置将被保留。")
    print()

    # 确认
    confirm = input("确认清空? (输入 'yes' 确认): ").strip().lower()
    if confirm != "yes":
        print("已取消。")
        return 0

    print()
    print("开始清空...")
    print()

    try:
        with engine.connect() as conn:
            # 清空 processed_news
            print("  [1] 清空 processed_news 表...")
            result = conn.execute(text("DELETE FROM processed_news"))
            conn.commit()
            print(f"      已删除 {result.rowcount} 条记录")

            # 清空 raw_news
            print("  [2] 清空 raw_news 表...")
            result = conn.execute(text("DELETE FROM raw_news"))
            conn.commit()
            print(f"      已删除 {result.rowcount} 条记录")

            # 验证
            print()
            print("  [3] 验证清空结果...")

            raw_count = conn.execute(text("SELECT COUNT(*) FROM raw_news")).scalar()
            processed_count = conn.execute(text("SELECT COUNT(*) FROM processed_news")).scalar()

            print(f"      raw_news 表: {raw_count} 条记录")
            print(f"      processed_news 表: {processed_count} 条记录")

        print()
        print("=" * 80)
        print("清空完成！")
        print("=" * 80)
        print()
        print("下一步:")
        print("  python scripts/01-collection/collect_news.py  # 重新采集新闻")
        print()

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
