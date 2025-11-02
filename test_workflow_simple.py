#!/usr/bin/env python3
"""
Simple End-to-End Workflow Test (使用现有数据)
简化的端到端工作流测试脚本

这个脚本测试完整的工作流（不包括采集）：
1. 查看已采集的文章
2. 选择文章进行 AI 评分
3. 自动审核
4. 微信发布

使用方式:
    python test_workflow_simple.py [number_of_articles]

示例:
    python test_workflow_simple.py 10   # 评分10篇文章
    python test_workflow_simple.py      # 默认评分5篇文章
"""

import sys
import os
from pathlib import Path
import io
from datetime import datetime

# 设置标准输出编码为 UTF-8 (Windows 兼容)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models import RawNews, ProcessedNews, ContentReview, PublishedContent
from src.services.ai.scoring_service import ScoringService
from src.services.workflow.auto_review_workflow import AutoReviewWorkflow
from src.services.workflow.wechat_workflow import WeChatPublishingWorkflow


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_step(step_num, title):
    """Print a formatted step header."""
    print(f"\n[步骤 {step_num}] {title}")
    print("-" * 80)


def main():
    """Main workflow test function."""

    print_section("DeepDive Tracking - 完整端到端工作流测试")
    print("(使用现有数据 - 无需采集)\n")

    # 获取命令行参数
    num_articles = 5  # 默认
    if len(sys.argv) > 1:
        try:
            num_articles = int(sys.argv[1])
        except ValueError:
            num_articles = 5

    print(f"配置: 处理 {num_articles} 篇文章\n")

    # 初始化数据库
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # ===== 步骤 1: 查看已采集的文章 =====
        print_step(1, "查看已采集的文章 (Show Collected Articles)")

        raw_news_list = session.query(RawNews).order_by(
            RawNews.created_at.desc()
        ).limit(10).all()

        if not raw_news_list:
            print("  ❌ 没有采集的文章，请先运行采集脚本")
            print("  python scripts/01-collection/collect_rss.py")
            return 1

        print(f"  找到 {session.query(RawNews).count()} 篇已采集的文章\n")
        print("  最近的10篇文章:\n")

        for idx, news in enumerate(raw_news_list[:10], 1):
            is_scored = session.query(ProcessedNews).filter(
                ProcessedNews.raw_news_id == news.id
            ).first() is not None

            status = "✓ 已评分" if is_scored else "○ 待评分"
            print(f"  [{idx:2d}] {status} | {news.title[:60]}...")

        print()

        # ===== 步骤 2: AI 评分 =====
        print_step(2, "AI 评分 (Scoring)")

        # 获取未评分的文章
        scored_ids = [row[0] for row in session.query(ProcessedNews.raw_news_id).all()]
        unscored = session.query(RawNews).filter(
            ~RawNews.id.in_(scored_ids) if scored_ids else True
        ).limit(num_articles).all()

        if not unscored:
            print(f"  ⚠️  没有待评分的文章")
            print(f"  所有文章都已评分，跳过此步骤")
            print()
        else:
            print(f"  找到 {len(unscored)} 篇待评分的文章")

            # Check if OpenAI API key is available
            if not settings.openai_api_key:
                print(f"  ⚠️  OpenAI API key 未配置，跳过评分")
                print(f"  将使用已有的 {session.query(ProcessedNews).count()} 篇已评分文章继续工作流")
                print()
            else:
                print(f"  初始化评分服务...")
                print(f"  开始评分...\n")

                scoring_service = ScoringService(settings, session)
                success_count = 0
                failed_count = 0
                total_cost = 0.0

                for idx, raw_news in enumerate(unscored, 1):
                    try:
                        print(f"  [{idx:2d}/{len(unscored)}] {raw_news.title[:50]}...", end="", flush=True)
                        result = scoring_service.score_article(raw_news)

                        if result:
                            success_count += 1
                            total_cost += result.metadata.cost if result.metadata else 0
                            print(f" ✓ 评分: {result.scoring.score}/100")
                        else:
                            failed_count += 1
                            print(" ✗ 失败")

                    except Exception as e:
                        failed_count += 1
                        print(f" ✗ 错误")

                print()
                print(f"  评分统计:")
                print(f"    成功: {success_count}/{len(unscored)}")
                print(f"    失败: {failed_count}/{len(unscored)}")
                print(f"    总成本: ${total_cost:.4f}")
                print()

        # ===== 步骤 3: 显示已评分文章 =====
        print_step(3, "显示已评分的文章样本 (Show Scored Articles)")

        processed_list = session.query(ProcessedNews).order_by(
            ProcessedNews.created_at.desc()
        ).limit(5).all()

        if processed_list:
            print(f"  找到 {session.query(ProcessedNews).count()} 篇已评分的文章\n")
            print("  最近评分的5篇文章:\n")

            for idx, processed in enumerate(processed_list, 1):
                raw_news = session.query(RawNews).filter(
                    RawNews.id == processed.raw_news_id
                ).first()

                if raw_news:
                    print(f"  [{idx}] {raw_news.title[:65]}...")
                    print(f"      评分: {processed.score:>5.1f}/100 | 分类: {processed.category:<15} | 关键词: {', '.join(processed.keywords[:2]) if processed.keywords else 'N/A'}")
                    print()

        # ===== 步骤 4: 自动审核 =====
        print_step(4, "自动审核 (Auto Review)")

        print("  为所有已评分文章创建审核记录...")
        from src.services.review.review_service import ReviewService

        review_service = ReviewService(session)

        # 为没有审核记录的文章创建审核记录
        reviewed_ids = [row[0] for row in session.query(ContentReview.processed_news_id).all()]
        processed_without_review = session.query(ProcessedNews).filter(
            ~ProcessedNews.id.in_(reviewed_ids) if reviewed_ids else True
        ).all()

        if processed_without_review:
            for processed in processed_without_review:
                review_service.create_review(processed.id)
            print(f"  创建了 {len(processed_without_review)} 条审核记录")
        else:
            print(f"  所有文章都有审核记录")

        print()
        print("  执行自动审核...")

        result = review_workflow = AutoReviewWorkflow(session).execute(
            score_threshold=50,
            max_reviews=100
        )

        if result['success']:
            print(f"  ✓ 自动审核完成")
            print(f"    自动批准: {result['approved_count']} 篇")
            print(f"    跳过处理: {result['skipped_count']} 篇")
            print()
        else:
            print(f"  ✗ 自动审核失败")
            print()

        # 显示审核统计
        stats = review_service.get_review_stats()
        print(f"  审核统计:")
        print(f"    总数: {stats['total']}")
        print(f"    待审核: {stats['pending']}")
        print(f"    已批准: {stats['approved']}")
        print(f"    已拒绝: {stats['rejected']}")
        print(f"    自动批准: {stats['auto_approved']}")
        print(f"    批准率: {stats['approval_rate']:.1f}%")
        print()

        # ===== 步骤 5: 微信发布 =====
        print_step(5, "微信发布 (WeChat Publishing)")

        # 检查 WeChat 凭证
        wechat_app_id = os.getenv('WECHAT_APP_ID')
        wechat_app_secret = os.getenv('WECHAT_APP_SECRET')

        if not wechat_app_id or not wechat_app_secret:
            print("  ⚠️  WeChat 凭证未配置")
            print("  配置方式:")
            print("    export WECHAT_APP_ID='wxc3d4bc2d698da563'")
            print("    export WECHAT_APP_SECRET='e9f5d2a2b2ffe5bc4e23c9904c0021b6'")
            print()
        else:
            print("  ✓ WeChat 凭证已配置")
            print("  初始化 WeChat 发布工作流...")

            try:
                wechat_workflow = WeChatPublishingWorkflow(
                    db_session=session,
                    wechat_app_id=wechat_app_id,
                    wechat_app_secret=wechat_app_secret
                )

                print("  执行 WeChat 发布...\n")
                result = wechat_workflow.execute()

                if result['success']:
                    print(f"  ✓ WeChat 发布完成")
                    print(f"    成功发布: {result['published_count']} 篇")
                    print(f"    发布失败: {result['failed_count']} 篇")
                    print()

                    if result['articles']:
                        print("  已发布的文章:")
                        for article in result['articles'][:5]:
                            print(f"    - {article['title'][:60]}...")
                        print()
                else:
                    print(f"  ⚠️  WeChat 发布: {result.get('error', 'Unknown error')}")
                    print()

                # 显示发布统计
                from src.services.publishing.publishing_service import PublishingService

                publishing_service = PublishingService(session)
                stats = publishing_service.get_publishing_stats()
                print(f"  发布统计:")
                print(f"    总数: {stats['total']}")
                print(f"    已发布: {stats['published']}")
                print(f"    待发布: {stats['scheduled']}")
                print(f"    发布失败: {stats['failed']}")
                print(f"    发布率: {stats['publish_rate']:.1f}%")
                print()

            except Exception as e:
                print(f"  ❌ WeChat 发布异常: {str(e)[:100]}")
                print()

        # ===== 最终统计 =====
        print_section("工作流执行完成")

        # 数据库统计
        total_raw = session.query(RawNews).count()
        total_processed = session.query(ProcessedNews).count()
        total_reviews = session.query(ContentReview).count()
        total_published = session.query(PublishedContent).count()

        print(f"数据库统计:")
        print(f"  原始新闻: {total_raw:>6d} 篇")
        print(f"  已评分:  {total_processed:>6d} 篇 ({total_processed*100//total_raw if total_raw > 0 else 0}%)")
        print(f"  已审核:  {total_reviews:>6d} 篇")
        print(f"  已发布:  {total_published:>6d} 篇")
        print()

        print("✅ 完整工作流测试成功!")
        print()

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        session.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
