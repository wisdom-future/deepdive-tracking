#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Score all unprocessed raw news items using AI."""

import asyncio
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import io

# 设置标准输出编码为 UTF-8 (Windows 兼容)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from sqlalchemy.orm import Session
    from src.config.settings import Settings
    from src.database.connection import SessionLocal
    from src.models import RawNews, ProcessedNews
    from src.services.ai import ScoringService
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


async def score_all_raw_news():
    """Score all unprocessed raw news."""
    settings = Settings()
    db_session: Session = SessionLocal()

    try:
        # 获取所有未评分的新闻
        unscored = db_session.query(RawNews).filter(
            RawNews.status == "raw"
        ).all()

        print(f"\n{'='*70}")
        print("Score Raw News with AI")
        print(f"{'='*70}\n")

        print(f"Found {len(unscored)} unscored articles\n")

        if not unscored:
            print("No unscored articles found")
            return

        # 初始化评分服务
        service = ScoringService(settings, db_session)

        results = []
        errors = []

        for i, raw_news in enumerate(unscored, 1):
            try:
                print(f"[{i}/{len(unscored)}] Scoring: {raw_news.title[:60]}")

                # 执行评分
                result = await service.score_news(raw_news)
                results.append(result)

                # 保存到数据库
                await service.save_to_database(raw_news, result)

                print(f"   Score: {result.scoring.score}/100")
                print(f"   Category: {result.scoring.category.value}")
                print(f"   Cost: ${result.metadata.cost:.4f}\n")

            except Exception as e:
                error_msg = f"Failed to score {raw_news.id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                print(f"   ERROR: {str(e)}\n")

        # 显示汇总
        print(f"\n{'='*70}")
        print("Summary")
        print(f"{'='*70}")
        print(f"Successfully scored: {len(results)}/{len(unscored)}")

        if results:
            total_cost = sum(r.metadata.cost for r in results)
            avg_score = sum(r.scoring.score for r in results) / len(results)

            print(f"Average score: {avg_score:.1f}/100")
            print(f"Total cost: ${total_cost:.4f}")
            print(f"Average cost per article: ${total_cost/len(results):.4f}")

            # 按分类统计
            print(f"\nBy category:")
            categories = {}
            for r in results:
                cat = r.scoring.category.value
                categories[cat] = categories.get(cat, 0) + 1

            for cat, count in sorted(categories.items()):
                print(f"  {cat}: {count}")

        if errors:
            print(f"\nErrors: {len(errors)}")
            for error in errors:
                print(f"  - {error}")

        print(f"\n{'='*70}")

    finally:
        db_session.close()


if __name__ == "__main__":
    try:
        asyncio.run(score_all_raw_news())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
