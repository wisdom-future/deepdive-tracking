#!/usr/bin/env python
"""Simple script to rescore unscored articles by running the collection task."""

import sys
import asyncio
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text

db_url = 'sqlite:///data/db/deepdive_tracking.db'
engine = create_engine(db_url)

print("=== 对未评分的记录进行评分 ===\n")

# 先检查未评分的记录
with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT COUNT(*) FROM raw_news
        WHERE id NOT IN (SELECT raw_news_id FROM processed_news)
    '''))
    unscored_count = result.scalar()

    print(f"找到 {unscored_count} 条未评分的记录")

    if unscored_count == 0:
        print("所有记录都已评分，无需处理!")
        sys.exit(0)

# 运行Celery任务（或直接的task函数）
print("\n选项1: 直接调用评分任务...")
print("(这将使用现有的Celery任务代码))")

from src.tasks.news_collection import collect_and_score_news_task

try:
    result = collect_and_score_news_task()
    print(f"\n任务完成:")
    print(f"  状态: {result.get('status')}")
    print(f"  采集: {result.get('articles_collected')}")
    print(f"  评分: {result.get('articles_scored')}")
    print(f"  成本: {result.get('total_cost')}")

except Exception as e:
    print(f"任务执行错误: {e}")
    import traceback
    traceback.print_exc()

# 最后验证
print("\n=== 验证结果 ===")
with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN id IN (SELECT raw_news_id FROM processed_news) THEN 1 ELSE 0 END) as scored,
            SUM(CASE WHEN id NOT IN (SELECT raw_news_id FROM processed_news) THEN 1 ELSE 0 END) as unscored
        FROM raw_news
    '''))
    row = result.fetchone()
    print(f"总数: {row[0]}")
    print(f"已评分: {row[1]}")
    print(f"未评分: {row[2]}")
    print(f"完成率: {row[1]/row[0]*100:.1f}%")
