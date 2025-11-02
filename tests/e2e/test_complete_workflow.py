#!/usr/bin/env python3
"""
Complete End-to-End Workflow Test
完整的端到端工作流测试脚本

这个脚本执行完整的工作流：
1. 采集 RSS 新闻
2. AI 评分
3. 自动审核
4. 微信发布

使用方式:
    python test_complete_workflow.py [number_of_articles]

示例:
    python test_complete_workflow.py 10   # 采集并处理10篇文章
    python test_complete_workflow.py      # 默认处理5篇文章
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
# 从 tests/e2e/ 向上两层到项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models import RawNews, ProcessedNews, ContentReview, PublishedContent
from src.services.collection.collection_manager import CollectionManager
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


def show_raw_news_sample(session, limit=5):
    """Show sample of collected raw news."""
    raw_news_list = session.query(RawNews).order_by(
        RawNews.created_at.desc()
    ).limit(limit).all()

    if not raw_news_list:
        print("  未找到采集的新闻")
        return 0

    print(f"  找到 {len(raw_news_list)} 篇新闻样本:\n")
    for idx, news in enumerate(raw_news_list, 1):
        print(f"  [{idx}] {news.title[:70]}...")
        print(f"      来源: {news.source}")
        print(f"      采集时间: {news.created_at}")
        print()

    return len(raw_news_list)


def show_scoring_results(session, limit=5):
    """Show sample of scored articles."""
    processed_list = session.query(ProcessedNews).order_by(
        ProcessedNews.created_at.desc()
    ).limit(limit).all()

    if not processed_list:
        print("  未找到已评分的文章")
        return 0

    print(f"  找到 {len(processed_list)} 篇已评分的文章:\n")
    for idx, processed in enumerate(processed_list, 1):
        raw_news = session.query(RawNews).filter(
            RawNews.id == processed.raw_news_id
        ).first()

        if raw_news:
            print(f"  [{idx}] {raw_news.title[:70]}...")
            print(f"      评分: {processed.score}/100")
            print(f"      分类: {processed.category}")
            print(f"      关键词: {', '.join(processed.keywords[:3]) if processed.keywords else 'N/A'}")
            print()

    return len(processed_list)


def show_review_results(session):
    """Show review statistics."""
    from src.services.review.review_service import ReviewService

    review_service = ReviewService(session)
    stats = review_service.get_review_stats()

    print(f"  审核统计:")
    print(f"    总数: {stats['total']}")
    print(f"    待审核: {stats['pending']}")
    print(f"    已批准: {stats['approved']}")
    print(f"    已拒绝: {stats['rejected']}")
    print(f"    自动批准: {stats['auto_approved']}")
    print(f"    批准率: {stats['approval_rate']:.1f}%")
    print()


def show_publishing_results(session):
    """Show publishing statistics."""
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


def main():
    """Main workflow test function."""

    print_section("DeepDive Tracking - 完整端到端工作流测试")

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
        # ===== 步骤 1: 采集 RSS 新闻 =====
        print_step(1, "采集 RSS 新闻 (Collection)")

        print("  初始化采集管理器...")
        collection_manager = CollectionManager(session)

        print("  开始采集...")
        start_time = datetime.utcnow()
        collected_count = collection_manager.collect_from_all_sources()
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        print(f"  采集完成: {collected_count} 篇文章 (耗时: {duration:.2f}秒)")
        print()

        # 显示采集的文章样本
        show_raw_news_sample(session, limit=3)

        # ===== 步骤 2: AI 评分 =====
        print_step(2, "AI 评分 (Scoring)")

        print("  初始化评分服务...")
        scoring_service = ScoringService(session)

        # 获取未评分的文章
        unscored = session.query(RawNews).filter(
            ~RawNews.id.in_(
                session.query(ProcessedNews.raw_news_id).all()
            )
        ).limit(num_articles).all()

        if not unscored:
            print(f"  没有待评分的文章，跳过此步骤")
        else:
            print(f"  找到 {len(unscored)} 篇待评分的文章")
            print(f"  开始评分 (这可能需要几分钟)...\n")

            success_count = 0
            failed_count = 0
            total_cost = 0.0

            for idx, raw_news in enumerate(unscored, 1):
                try:
                    print(f"  [{idx}/{len(unscored)}] {raw_news.title[:50]}...", end="")
                    result = scoring_service.score_article(raw_news)

                    if result:
                        success_count += 1
                        total_cost += result.metadata.cost if result.metadata else 0
                        print(f" ✓ (评分: {result.scoring.score})")
                    else:
                        failed_count += 1
                        print(" ✗ (失败)")

                except Exception as e:
                    failed_count += 1
                    print(f" ✗ ({str(e)[:30]})")

            print()
            print(f"  评分结果:")
            print(f"    成功: {success_count}/{len(unscored)}")
            print(f"    失败: {failed_count}/{len(unscored)}")
            print(f"    总成本: ${total_cost:.4f}")
            print()

        # 显示评分结果样本
        show_scoring_results(session, limit=3)

        # ===== 步骤 3: 自动审核 =====
        print_step(3, "自动审核 (Auto Review)")

        print("  初始化自动审核工作流...")
        review_workflow = AutoReviewWorkflow(session)

        print("  执行自动审核...")
        result = review_workflow.execute(score_threshold=50, max_reviews=100)

        if result['success']:
            print(f"  ✓ 自动审核成功")
            print(f"    自动批准: {result['approved_count']}")
            print(f"    跳过处理: {result['skipped_count']}")
            print()
        else:
            print(f"  ✗ 自动审核失败: {result.get('error', 'Unknown error')}")
            print()

        # 显示审核结果
        show_review_results(session)

        # ===== 步骤 4: 微信发布 =====
        print_step(4, "微信发布 (WeChat Publishing)")

        # 检查 WeChat 凭证
        wechat_app_id = os.getenv('WECHAT_APP_ID')
        wechat_app_secret = os.getenv('WECHAT_APP_SECRET')

        if not wechat_app_id or not wechat_app_secret:
            print("  ⚠️  WeChat 凭证未配置，跳过微信发布")
            print("  配置方式:")
            print("    export WECHAT_APP_ID='你的AppID'")
            print("    export WECHAT_APP_SECRET='你的AppSecret'")
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

                print("  执行 WeChat 发布...")
                result = wechat_workflow.execute()

                if result['success']:
                    print(f"  ✓ WeChat 发布完成")
                    print(f"    成功发布: {result['published_count']} 篇")
                    print(f"    发布失败: {result['failed_count']} 篇")
                    print()

                    if result['articles']:
                        print("  已发布的文章:")
                        for article in result['articles'][:3]:
                            print(f"    - {article['title'][:50]}...")
                        print()
                else:
                    print(f"  ✗ WeChat 发布失败: {result.get('error', 'Unknown error')}")
                    print()

            except Exception as e:
                print(f"  ✗ WeChat 发布异常: {str(e)[:60]}")
                print()

        # 显示发布统计
        show_publishing_results(session)

        # ===== 最终统计 =====
        print_section("完整工作流执行完成")

        # 数据库统计
        total_raw = session.query(RawNews).count()
        total_processed = session.query(ProcessedNews).count()
        total_reviews = session.query(ContentReview).count()
        total_published = session.query(PublishedContent).count()

        print(f"数据库统计:")
        print(f"  原始新闻: {total_raw} 篇")
        print(f"  已评分: {total_processed} 篇")
        print(f"  已审核: {total_reviews} 篇")
        print(f"  已发布: {total_published} 篇")
        print()

        print(f"✅ 测试完成!")
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
