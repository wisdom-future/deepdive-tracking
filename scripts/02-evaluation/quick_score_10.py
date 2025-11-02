#!/usr/bin/env python3
"""
Quick Score - 快速评分脚本（P1-3 演示）

功能：
  - 从数据库读取前10条未评分文章
  - 快速评分作为P1-3演示
  - 展示评分结果

这是一个简化版本，用于快速演示系统功能。
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
    """Main function"""
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n" + "=" * 80)
    print("DeepDive Tracking - Quick Score Demo (P1-3)")
    print("=" * 80)
    print()

    try:
        # Get unscored articles
        print("[1] Looking for unscored articles...")
        unscored = session.query(RawNews).filter(
            ~RawNews.id.in_(
                session.query(ProcessedNews.raw_news_id)
            )
        ).order_by(RawNews.published_at.desc()).limit(10).all()

        if not unscored:
            print("    No unscored articles found")
            return 0

        print(f"    Found {len(unscored)} unscored articles")
        print()

        # Initialize service
        print("[2] Initializing scoring service...")
        service = ScoringService(settings, session)
        print("    OK - Service ready")
        print()

        # Score them
        print("[3] Scoring...")
        print()

        scored_count = 0
        failed_count = 0
        total_cost = 0.0
        results = []

        for idx, article in enumerate(unscored, 1):
            try:
                title_preview = article.title[:40] + "..." if len(article.title) > 40 else article.title
                print(f"  [{idx:2}/{len(unscored)}] {title_preview}", end="", flush=True)

                # Call scoring service
                result = await service.score_news(article)

                # Extract fields with safe truncation
                score = result.scoring.score
                categories = result.scoring.categories[:3]  # Limit categories
                # Truncate summaries BEFORE pydantic validation
                summary = (result.summaries.summary_pro[:200]
                          if result.summaries.summary_pro else "")
                cost = result.metadata.cost

                # Save to database
                processed = ProcessedNews(
                    raw_news_id=article.id,
                    score=score,
                    category=','.join(categories) if categories else "",
                    summary=summary,
                    keywords=None
                )
                session.add(processed)
                session.commit()

                scored_count += 1
                total_cost += cost
                results.append({
                    'title': article.title,
                    'score': score,
                    'cost': cost
                })

                print(f" ✓ {score}/100 (${cost:.4f})")

            except Exception as e:
                failed_count += 1
                error_msg = str(e)[:40]
                print(f" ✗ {error_msg}")

        print()
        print("=" * 80)
        print("[4] Results")
        print("=" * 80)
        print()

        print(f"Success:       {scored_count}/{len(unscored)}")
        print(f"Failed:        {failed_count}/{len(unscored)}")
        print(f"Success Rate:  {100*scored_count//max(1, len(unscored))}%")
        print()
        print(f"Total Cost:    ${total_cost:.4f}")
        if scored_count > 0:
            print(f"Avg Cost/Item: ${total_cost/scored_count:.4f}")
        print()

        # Show top 5 scores
        if results:
            print("=" * 80)
            print("[5] Top Scoring Results")
            print("=" * 80)
            print()

            sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
            for idx, r in enumerate(sorted_results[:5], 1):
                title = r['title'][:50] + "..." if len(r['title']) > 50 else r['title']
                print(f"  {idx}. [{r['score']:3}/100] {title}")
                print(f"     Cost: ${r['cost']:.4f}")

        print()
        print("=" * 80)
        print("Demo Complete!")
        print("=" * 80)
        print()
        print("Next Steps:")
        print("  python scripts/03-verification/view_summary.py")
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
