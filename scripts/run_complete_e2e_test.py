#!/usr/bin/env python3
"""
Complete End-to-End Testing Script: Collection → Scoring → Review → Publishing

This script runs the complete news processing pipeline from start to finish:
1. Initialize data sources
2. Collect raw news
3. Score and process news with AI
4. Auto-review articles
5. Publish to WeChat

Usage:
    python scripts/run_complete_e2e_test.py [num_articles] [--skip-collection]

Examples:
    python scripts/run_complete_e2e_test.py 10          # Collect 10 new articles
    python scripts/run_complete_e2e_test.py 5 --skip-collection  # Skip collection, only score
    python scripts/run_complete_e2e_test.py             # Use default (3 articles)
"""

import sys
import os
from pathlib import Path
import io
import asyncio
from datetime import datetime

# Set UTF-8 encoding for Windows compatibility
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models import (
    Base,
    RawNews,
    ProcessedNews,
    ContentReview,
    PublishedContent,
    WeChatMediaCache,
    DataSource,
)


def print_header(title):
    """Print a section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_step(num, title):
    """Print a step header."""
    print(f"\n[步骤 {num}] {title}")
    print("-" * 80)


def print_success(message):
    """Print success message."""
    print(f"  ✅ {message}")


def print_error(message):
    """Print error message."""
    print(f"  ❌ {message}")


def print_warning(message):
    """Print warning message."""
    print(f"  ⚠️  {message}")


def print_info(message):
    """Print info message."""
    print(f"  ℹ️  {message}")


def main():
    """Main function."""
    print_header("DeepDive 完整端到端测试：采集 → 评分 → 审核 → 发布")

    # Parse arguments
    num_articles = 3
    skip_collection = False

    for arg in sys.argv[1:]:
        if arg == "--skip-collection":
            skip_collection = True
        else:
            try:
                num_articles = int(arg)
            except ValueError:
                pass

    print(f"配置:")
    print(f"  • 文章数量: {num_articles}")
    print(f"  • 跳过采集: {'是' if skip_collection else '否'}\n")

    # Initialize settings and database
    get_settings.cache_clear()
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # ===== 步骤 0: 验证配置 =====
        print_step(0, "验证配置")

        # Check credentials
        config_ok = True
        if not settings.openai_api_key:
            print_warning("OpenAI API Key 未配置（评分功能需要）")
            config_ok = False
        else:
            print_success("OpenAI API Key 已配置")

        if not settings.wechat_app_id or not settings.wechat_app_secret:
            print_warning("WeChat 凭证未配置（发布功能需要）")
            config_ok = False
        else:
            print_success("WeChat 凭证已配置")

        if not config_ok:
            print_warning("某些功能可能不可用，但可继续测试")

        print()

        # ===== 步骤 1: 数据库初始化和统计 =====
        print_step(1, "数据库统计")

        total_sources = session.query(DataSource).count()
        total_raw = session.query(RawNews).count()
        total_scored = session.query(ProcessedNews).count()
        total_reviewed = session.query(ContentReview).count()
        total_published = session.query(PublishedContent).count()
        total_media_cache = session.query(WeChatMediaCache).count()

        print(f"  数据源配置: {total_sources:>6d} 个")
        print(f"  原始文章:   {total_raw:>6d} 篇")
        print(f"  已评分:     {total_scored:>6d} 篇 ({total_scored*100//total_raw if total_raw > 0 else 0}%)")
        print(f"  已审核:     {total_reviewed:>6d} 篇")
        print(f"  已发布:     {total_published:>6d} 篇")
        print(f"  媒体缓存:   {total_media_cache:>6d} 项")
        print()

        # ===== 步骤 2: 采集 (可选) =====
        if not skip_collection:
            print_step(2, "采集新闻")

            from src.services.collection.collection_manager import CollectionManager

            collector = CollectionManager(session)
            try:
                collected = collector.collect_from_enabled_sources(limit=num_articles)
                print_success(f"采集完成: {len(collected)} 篇新文章")

                if collected:
                    print(f"  样本文章:")
                    for article in collected[:3]:
                        print(f"    - {article.title[:60]}...")
            except Exception as e:
                print_error(f"采集失败: {str(e)}")
                print_warning("继续使用现有数据进行测试...")

            print()

            # Refresh counts
            total_raw = session.query(RawNews).count()
            print_info(f"当前原始文章总数: {total_raw}")
            print()
        else:
            print_step(2, "跳过采集步骤")
            print_info("使用现有数据库中的文章进行测试")
            print()

        # ===== 步骤 3: 评分和处理 =====
        print_step(3, "AI评分和处理")

        from src.services.ai.scoring_service import ScoringService

        try:
            scoring_service = ScoringService(session)

            # Get unscored articles
            unscored = session.query(RawNews).filter(
                ~RawNews.processed_news.any()
            ).limit(num_articles).all()

            if not unscored:
                print_warning(f"没有未评分的文章，使用已评分的文章进行测试")
                unscored = session.query(RawNews).filter(
                    RawNews.processed_news.any()
                ).limit(num_articles).all()

            if unscored:
                print_info(f"开始评分 {len(unscored)} 篇文章...")

                scored_count = 0
                failed_count = 0

                for idx, raw_news in enumerate(unscored, 1):
                    try:
                        # Check if already scored
                        existing = session.query(ProcessedNews).filter(
                            ProcessedNews.raw_news_id == raw_news.id
                        ).first()

                        if not existing:
                            processed = asyncio.run(
                                scoring_service.score_news(raw_news)
                            )
                            print_info(f"  [{idx}/{len(unscored)}] ✓ {raw_news.title[:50]}... (分数: {processed.score})")
                            scored_count += 1
                        else:
                            print_info(f"  [{idx}/{len(unscored)}] ⊘ {raw_news.title[:50]}... (已评分)")

                    except Exception as e:
                        print_error(f"  [{idx}/{len(unscored)}] ✗ {raw_news.title[:50]}... ({str(e)[:30]})")
                        failed_count += 1

                print_success(f"评分完成: {scored_count} 篇成功, {failed_count} 篇失败")
            else:
                print_warning("没有可评分的文章")

        except Exception as e:
            print_error(f"评分服务初始化失败: {str(e)}")
            print_warning("跳过评分步骤")

        print()

        # Refresh counts
        total_scored = session.query(ProcessedNews).count()
        print_info(f"当前已评分文章总数: {total_scored}")
        print()

        # ===== 步骤 4: 自动审核 =====
        print_step(4, "自动审核")

        from src.services.review.review_service import ReviewService

        try:
            review_service = ReviewService(session)

            # Get unreviewed scored articles
            reviewed_ids = [row[0] for row in session.query(ContentReview.processed_news_id).all()]
            unreviewed = session.query(ProcessedNews).filter(
                ~ProcessedNews.id.in_(reviewed_ids) if reviewed_ids else True
            ).limit(num_articles).all()

            if unreviewed:
                print_info(f"开始审核 {len(unreviewed)} 篇文章...")

                reviewed_count = 0
                for idx, processed in enumerate(unreviewed, 1):
                    try:
                        review = review_service.create_review(processed.id)
                        # Auto-approve for testing
                        review.status = "approved"
                        session.commit()
                        print_info(f"  [{idx}/{len(unreviewed)}] ✓ 文章 {processed.id} 已批准")
                        reviewed_count += 1
                    except Exception as e:
                        print_error(f"  [{idx}/{len(unreviewed)}] ✗ 文章 {processed.id} 失败: {str(e)[:30]}")

                print_success(f"审核完成: {reviewed_count} 篇文章已批准")
            else:
                print_warning("没有待审核的文章")

        except Exception as e:
            print_error(f"审核服务初始化失败: {str(e)}")
            print_warning("跳过审核步骤")

        print()

        # Refresh counts
        total_reviewed = session.query(ContentReview).count()
        print_info(f"当前已审核文章总数: {total_reviewed}")
        print()

        # ===== 步骤 5: 发布到微信 =====
        print_step(5, "发布到WeChat")

        if not settings.wechat_app_id or not settings.wechat_app_secret:
            print_warning("WeChat 凭证未配置，跳过发布步骤")
        else:
            from src.services.workflow.wechat_workflow_v2 import WeChatPublishingWorkflowV2

            try:
                workflow = WeChatPublishingWorkflowV2(
                    db_session=session,
                    wechat_app_id=settings.wechat_app_id,
                    wechat_app_secret=settings.wechat_app_secret,
                )

                print_info("启动WeChat V2发布工作流...")

                result = asyncio.run(workflow.execute(batch_size=min(3, num_articles)))

                print_success(f"发布完成:")
                print(f"    • 成功: {result.get('published_count', 0)} 篇")
                print(f"    • 失败: {result.get('failed_count', 0)} 篇")

                if result.get('articles'):
                    print(f"\n  已发布的文章:")
                    for article in result['articles']:
                        print(f"    - {article['title'][:50]}...")

                if result.get('failed_articles'):
                    print(f"\n  失败的文章:")
                    for title in result['failed_articles']:
                        print(f"    - {title[:50]}...")

            except Exception as e:
                print_error(f"发布失败: {str(e)}")
                print_warning("详细错误信息已记录到日志")

        print()

        # ===== 步骤 6: 最终统计 =====
        print_step(6, "最终统计")

        # Refresh all counts
        final_raw = session.query(RawNews).count()
        final_scored = session.query(ProcessedNews).count()
        final_reviewed = session.query(ContentReview).count()
        final_published = session.query(PublishedContent).count()
        final_media_cache = session.query(WeChatMediaCache).count()

        print("  初始 → 当前:")
        print(f"    原始文章:  {total_raw:>6d} → {final_raw:>6d} (增加 {final_raw - total_raw})")
        print(f"    已评分:    {total_scored:>6d} → {final_scored:>6d} (增加 {final_scored - total_scored})")
        print(f"    已审核:    {total_reviewed:>6d} → {final_reviewed:>6d} (增加 {final_reviewed - total_reviewed})")
        print(f"    已发布:    {total_published:>6d} → {final_published:>6d} (增加 {final_published - total_published})")
        print(f"    媒体缓存:  {total_media_cache:>6d} → {final_media_cache:>6d} (增加 {final_media_cache - total_media_cache})")

        # Show processing rate
        if final_scored > 0:
            processing_rate = (final_reviewed / final_scored) * 100 if final_scored > 0 else 0
            publishing_rate = (final_published / final_scored) * 100 if final_scored > 0 else 0
            print(f"\n  处理进度:")
            print(f"    评分→审核: {processing_rate:.1f}%")
            print(f"    评分→发布: {publishing_rate:.1f}%")

        print()

        # ===== 完成 =====
        print_header("端到端测试完成")

        if final_published > total_published:
            print_success(f"成功发布 {final_published - total_published} 篇新文章！\n")
            return 0
        elif final_reviewed > total_reviewed:
            print_success(f"成功审核 {final_reviewed - total_reviewed} 篇文章，等待发布\n")
            return 0
        elif final_scored > total_scored:
            print_success(f"成功评分 {final_scored - total_scored} 篇文章，等待审核\n")
            return 0
        else:
            print_warning("未产生新的处理结果，但测试完成\n")
            return 0

    except KeyboardInterrupt:
        print_error("\n测试被用户中断")
        return 130
    except Exception as e:
        print_error(f"\n测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
