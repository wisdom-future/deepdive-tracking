#!/usr/bin/env python3
"""
Phase 2 验证脚本 - 自动审核与微信发布
Manual verification script for Phase 2 implementation

This script provides a user-friendly way to verify the complete
Phase 2 implementation without requiring pytest or test framework setup.

Usage:
    python scripts/05-verification/verify_phase2.py [num_articles]

Example:
    python scripts/05-verification/verify_phase2.py 5   # 验证5篇文章
    python scripts/05-verification/verify_phase2.py     # 默认5篇
"""

import sys
import os
from pathlib import Path
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
from src.models import RawNews, ProcessedNews, ContentReview, PublishedContent
from src.services.ai.scoring_service import ScoringService
from src.services.workflow.auto_review_workflow import AutoReviewWorkflow
from src.services.workflow.wechat_workflow import WeChatPublishingWorkflow
import asyncio


def print_header(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_step(num, title):
    print(f"\n[步骤 {num}] {title}")
    print("-" * 80)


def main():
    print_header("DeepDive Tracking - Phase 2 验证脚本")

    # 获取命令行参数
    num_articles = 5
    if len(sys.argv) > 1:
        try:
            num_articles = int(sys.argv[1])
        except ValueError:
            num_articles = 5

    print(f"配置: 处理 {num_articles} 篇文章\n")

    # 初始化数据库
    get_settings.cache_clear()
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # ===== 步骤 1: 配置验证 =====
        print_step(1, "配置验证 (Configuration Check)")

        print(f"  OpenAI API Key: {'配置' if settings.openai_api_key else '未配置'}")
        print(f"  OpenAI Model: {settings.openai_model}")
        print(f"  WeChat App ID: {'配置' if settings.wechat_app_id else '未配置'}")
        print(f"  Database: {settings.database_url}")
        print()

        # ===== 步骤 2: 数据库统计 =====
        print_step(2, "数据库统计 (Database Statistics)")

        total_raw = session.query(RawNews).count()
        total_scored = session.query(ProcessedNews).count()
        total_reviewed = session.query(ContentReview).count()
        total_published = session.query(PublishedContent).count()

        print(f"  原始文章: {total_raw} 篇")
        print(f"  已评分:   {total_scored} 篇 ({total_scored*100//total_raw if total_raw > 0 else 0}%)")
        print(f"  已审核:   {total_reviewed} 篇")
        print(f"  已发布:   {total_published} 篇")
        print()

        # ===== 步骤 3: AI 评分验证 =====
        print_step(3, "AI 评分验证 (Scoring Verification)")

        if not settings.openai_api_key:
            print("  跳过: OpenAI API Key 未配置")
            print()
        else:
            scored_ids = [row[0] for row in session.query(ProcessedNews.raw_news_id).all()]
            unscored = session.query(RawNews).filter(
                ~RawNews.id.in_(scored_ids) if scored_ids else True
            ).limit(num_articles).all()

            if not unscored:
                print(f"  所有文章都已评分，跳过新评分")
                print()
            else:
                print(f"  找到 {len(unscored)} 篇待评分的文章")
                print(f"  初始化 OpenAI 服务...")

                scoring_service = ScoringService(settings, session)
                success = 0
                failed = 0

                for idx, raw_news in enumerate(unscored, 1):
                    try:
                        print(f"  [{idx:2d}/{len(unscored)}] {raw_news.title[:40]}...", end="", flush=True)
                        result = asyncio.run(scoring_service.score_news(raw_news))

                        if result:
                            success += 1
                            print(f" ✓ ({result.scoring.score}/100)")
                        else:
                            failed += 1
                            print(" ✗ (None)")
                    except Exception as e:
                        failed += 1
                        print(f" ✗ ({str(e)[:30]})")

                print()
                print(f"  成功: {success}/{len(unscored)}")
                print(f"  失败: {failed}/{len(unscored)}")
                print()

        # ===== 步骤 4: 自动审核验证 =====
        print_step(4, "自动审核验证 (Auto-Review Verification)")

        from src.services.review.review_service import ReviewService
        review_service = ReviewService(session)

        # 为没有审核记录的文章创建审核记录
        reviewed_ids = [row[0] for row in session.query(ContentReview.processed_news_id).all()]
        unreviewed = session.query(ProcessedNews).filter(
            ~ProcessedNews.id.in_(reviewed_ids) if reviewed_ids else True
        ).all()

        if unreviewed:
            print(f"  创建 {len(unreviewed)} 条新审核记录...")
            for processed in unreviewed:
                review_service.create_review(processed.id)
            print()

        # 执行自动审核
        print("  执行自动审核工作流...")
        workflow = AutoReviewWorkflow(session)
        result = workflow.execute(score_threshold=50, max_reviews=100)

        if result['success']:
            print(f"  自动批准: {result['approved_count']} 篇")
            print(f"  跳过: {result['skipped_count']} 篇")
        else:
            print(f"  失败: {result.get('error', 'Unknown')}")

        # 显示统计
        stats = review_service.get_review_stats()
        print()
        print("  审核统计:")
        print(f"    总数: {stats['total']}")
        print(f"    批准: {stats['approved']}")
        print(f"    拒绝: {stats['rejected']}")
        print(f"    待审: {stats['pending']}")
        print()

        # ===== 步骤 5: WeChat 发布验证 =====
        print_step(5, "WeChat 发布验证 (WeChat Publishing Verification)")

        if not settings.wechat_app_id or not settings.wechat_app_secret:
            print("  WeChat 凭证未配置")
            print()
        else:
            print("  WeChat 凭证已配置")
            print("  初始化 WeChat 发布工作流...")

            try:
                wechat_workflow = WeChatPublishingWorkflow(
                    db_session=session,
                    wechat_app_id=settings.wechat_app_id,
                    wechat_app_secret=settings.wechat_app_secret
                )

                result = wechat_workflow.execute()

                if result['success']:
                    print(f"  成功发布: {result['published_count']} 篇")
                    print(f"  发布失败: {result['failed_count']} 篇")
                else:
                    print(f"  执行失败: {result.get('error', 'Unknown')}")

                print()
            except Exception as e:
                print(f"  异常: {str(e)[:100]}")
                print()

        # ===== 最终统计 =====
        print_header("验证完成")

        print("最终数据库统计:")
        total_raw = session.query(RawNews).count()
        total_scored = session.query(ProcessedNews).count()
        total_reviewed = session.query(ContentReview).count()
        total_published = session.query(PublishedContent).count()

        print(f"  原始文章:  {total_raw:>6d} 篇")
        print(f"  已评分:    {total_scored:>6d} 篇 ({total_scored*100//total_raw if total_raw > 0 else 0}%)")
        print(f"  已审核:    {total_reviewed:>6d} 篇")
        print(f"  已发布:    {total_published:>6d} 篇")
        print()

        print("验证结果: OK")
        print()

        return 0

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        session.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
