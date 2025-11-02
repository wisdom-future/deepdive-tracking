#!/usr/bin/env python3
"""
Score Collected News - 评分采集的真实新闻

功能：
  - 从数据库读取未评分的文章
  - 使用 OpenAI GPT-4o API 进行智能评分
  - 保存评分结果到 processed_news 表
  - 显示成功率、成本、性能统计

使用方法：
  python scripts/02-evaluation/score_collected_news.py [max_count]

参数：
  max_count: 最多评分多少条（默认 50）
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import io

# 设置标准输出编码为 UTF-8 (Windows 兼容)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models import RawNews, ProcessedNews
from src.services.ai import ScoringService

async def main():
    """Main scoring function"""
    max_count = int(sys.argv[1]) if len(sys.argv) > 1 else 50

    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n" + "=" * 80)
    print("DeepDive Tracking - Score Collected News")
    print("=" * 80)
    print()

    try:
        # [1] 获取未评分的文章
        print("[1] 查询未评分的文章...")

        unscored = session.query(RawNews).filter(
            ~RawNews.id.in_(
                session.query(ProcessedNews.raw_news_id)
            )
        ).order_by(RawNews.published_at.desc()).limit(max_count).all()

        if not unscored:
            print("    没有未评分的文章")
            return 0

        print(f"    找到 {len(unscored)} 条未评分的文章")
        print()

        # [2] 初始化评分服务
        print("[2] 初始化 OpenAI 评分服务...")
        service = ScoringService(settings, session)
        print("    OK - 服务就绪")
        print()

        # [3] 开始评分
        print("[3] 开始评分...")
        print(f"    时间: {datetime.now().isoformat()}")
        print()

        scored_count = 0
        failed_count = 0
        total_cost = 0.0

        for idx, article in enumerate(unscored, 1):
            try:
                # 显示进度
                title_preview = article.title[:40] + "..." if len(article.title) > 40 else article.title
                print(f"  [{idx:3}/{len(unscored)}] {title_preview}")

                # 调用评分服务
                result = await service.score_news(article)

                # 提取字段
                score = result.score
                categories = result.categories if result.categories else []
                summary = (result.summary[:300] if result.summary else "")
                keywords = result.keywords if result.keywords else []
                cost = result.cost

                # 保存到数据库
                processed = ProcessedNews(
                    raw_news_id=article.id,
                    score=score,
                    category=','.join(categories),
                    summary=summary,
                    keywords=','.join(keywords) if keywords else None
                )
                session.add(processed)
                session.commit()

                scored_count += 1
                total_cost += cost

                print(f"           分数: {score}/100, 成本: ${cost:.4f}")

            except Exception as e:
                failed_count += 1
                error_msg = str(e)[:50]
                print(f"           [ERROR] {error_msg}")

        print()
        print("=" * 80)
        print("[4] 评分结果")
        print("=" * 80)
        print()
        print(f"  成功: {scored_count}/{len(unscored)}")
        print(f"  失败: {failed_count}/{len(unscored)}")
        print(f"  成功率: {100*scored_count//max(1, len(unscored))}%")
        print()
        print(f"  总成本: ${total_cost:.4f}")
        print(f"  平均成本: ${total_cost/max(1, scored_count):.4f}/条")
        print()

        # [5] 成本投影
        print("=" * 80)
        print("[5] 成本投影 (基于当前速率)")
        print("=" * 80)
        print()

        avg_cost = total_cost / max(1, scored_count)
        print(f"  100 条文章:    ${avg_cost * 100:.2f}")
        print(f"  1,000 条文章:  ${avg_cost * 1000:.2f}")
        print(f"  10,000 条文章: ${avg_cost * 10000:.2f}")
        print()

        # [6] 显示评分分布
        print("=" * 80)
        print("[6] 评分分布")
        print("=" * 80)
        print()

        # 查询评分分布
        from sqlalchemy import func, text

        # 简化: 不显示评分分布如果没有评分
        if scored_count == 0:
            distribution = []
        else:
            try:
                score_range_expr = (ProcessedNews.score / 10).cast('int')
                distribution = session.query(
                    func.count(ProcessedNews.id).label('count'),
                    score_range_expr.label('range')
                ).group_by(
                    score_range_expr
                ).order_by(score_range_expr).all()
            except Exception:
                distribution = []

        for row in distribution:
            if row.range:
                score_range = f"{int(row.range*10)}-{int(row.range*10+9)}"
            else:
                score_range = "0-9"
            print(f"  {score_range:8} 分: {'█' * row.count} ({row.count}条)")

        print()
        print("=" * 80)
        print("评分完成!")
        print("=" * 80)
        print()
        print("下一步:")
        print("  python scripts/03-verification/view_summary.py  # 查看完整统计")
        print()

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        session.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
