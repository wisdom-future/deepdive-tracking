#!/usr/bin/env python3
"""
WeChat Publishing Script - 发布已审核的文章到微信公众号

功能：
  - 获取已审核的文章
  - 创建发布计划
  - 发布到微信公众号
  - 显示发布结果和统计
"""

import sys
from pathlib import Path
import io
from datetime import datetime

# 设置标准输出编码为 UTF-8 (Windows 兼容)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models import ProcessedNews, ContentReview, PublishedContent, RawNews
from src.services.publishing_service import PublishingService
from src.services.review_service import ReviewService
import os

def main():
    """Main publishing function"""
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n" + "="*80)
    print("WeChat Publishing Workflow")
    print("="*80)
    print()

    try:
        # [1] 检查 WeChat 凭证
        print("[1] 检查 WeChat 凭证...")
        wechat_app_id = os.getenv('WECHAT_APP_ID')
        wechat_app_secret = os.getenv('WECHAT_APP_SECRET')

        if not wechat_app_id or not wechat_app_secret:
            print("    ❌ WeChat 凭证未配置")
            print("    请设置环境变量:")
            print("    export WECHAT_APP_ID='你的AppID'")
            print("    export WECHAT_APP_SECRET='你的AppSecret'")
            return 1

        print(f"    ✅ 已检测到 WeChat 凭证")
        print(f"    App ID: {wechat_app_id[:10]}...")
        print()

        # [2] 初始化服务
        print("[2] 初始化服务...")
        review_service = ReviewService(session)
        publishing_service = PublishingService(
            db_session=session,
            wechat_app_id=wechat_app_id,
            wechat_app_secret=wechat_app_secret
        )

        if not publishing_service.wechat_publisher:
            print("    ❌ WeChat 发布器初始化失败")
            return 1

        print("    ✅ 审核服务就绪")
        print("    ✅ 发布服务就绪")
        print()

        # [3] 获取待发布的文章
        print("[3] 获取待发布的文章...")

        # 获取已批准的审核记录
        approved_reviews = session.query(ContentReview).filter(
            ContentReview.status == "approved"
        ).all()

        if not approved_reviews:
            print("    ⚠️  没有已批准的文章")
            print()
            print("    建议流程:")
            print("    1. 采集: python scripts/01-collection/collect_rss.py")
            print("    2. 评分: python scripts/02-evaluation/score_collected_news.py 10")
            print("    3. 审核: python scripts/03-review/auto_review_articles.py")
            print("    4. 再次运行本脚本")
            return 0

        print(f"    找到 {len(approved_reviews)} 条已批准的文章")
        print()

        # [4] 检查是否已发布
        print("[4] 过滤未发布的文章...")

        articles_to_publish = []
        for review in approved_reviews:
            # 检查是否已经有发布计划
            existing_publish = session.query(PublishedContent).filter(
                PublishedContent.processed_news_id == review.processed_news_id
            ).first()

            if not existing_publish:
                articles_to_publish.append(review)

        print(f"    待发布: {len(articles_to_publish)} 篇")
        print(f"    已发布: {len(approved_reviews) - len(articles_to_publish)} 篇")
        print()

        if not articles_to_publish:
            print("    📢 所有已批准的文章都已发布")
            print()
            # 显示最近发布的文章
            recent = session.query(PublishedContent).filter(
                PublishedContent.publish_status == "published"
            ).order_by(PublishedContent.published_at.desc()).limit(5).all()

            if recent:
                print("[5] 最近发布的文章")
                print("-" * 80)
                for idx, pub in enumerate(recent, 1):
                    raw_news = session.query(RawNews).filter(
                        RawNews.id == pub.raw_news_id
                    ).first()
                    if raw_news:
                        print(f"  [{idx}] {raw_news.title[:60]}...")
                        if pub.wechat_url:
                            print(f"      WeChat: {pub.wechat_url}")
                print()

            return 0

        # [5] 创建发布计划
        print("[5] 创建发布计划...")
        published_contents = []

        for idx, review in enumerate(articles_to_publish, 1):
            try:
                processed_news = session.query(ProcessedNews).filter(
                    ProcessedNews.id == review.processed_news_id
                ).first()

                if not processed_news:
                    continue

                # 创建发布计划
                pub_content = publishing_service.create_publishing_plan(
                    processed_news_id=processed_news.id,
                    channels=["wechat"],  # 只发布到微信
                    content_review_id=review.id
                )
                published_contents.append(pub_content)
                print(f"    [{idx}] 创建发布计划 ID: {pub_content.id}")

            except Exception as e:
                print(f"    [{idx}] 错误: {str(e)[:60]}")

        print(f"    ✅ 成功创建 {len(published_contents)} 个发布计划")
        print()

        # [6] 发布到微信
        print("[6] 发布到微信公众号...")
        print("-" * 80)

        success_count = 0
        failed_count = 0

        for idx, pub_content in enumerate(published_contents, 1):
            try:
                raw_news = session.query(RawNews).filter(
                    RawNews.id == pub_content.raw_news_id
                ).first()

                if not raw_news:
                    print(f"  [{idx}] ❌ 找不到原始文章")
                    failed_count += 1
                    continue

                article_title = raw_news.title[:50]
                print(f"  [{idx}] 发布: {article_title}...")

                # 调用微信发布
                result = publishing_service.publish_to_wechat(
                    published_content_id=pub_content.id
                )

                if result.wechat_url:
                    print(f"      ✅ 成功")
                    print(f"      链接: {result.wechat_url}")
                    success_count += 1
                else:
                    print(f"      ❌ 失败")
                    if result.publish_error:
                        print(f"      错误: {result.publish_error}")
                    failed_count += 1

            except Exception as e:
                print(f"  [{idx}] ❌ 异常: {str(e)[:60]}")
                failed_count += 1

        print()

        # [7] 显示统计
        print("[7] 发布统计")
        print("="*80)

        stats = publishing_service.get_publishing_stats()
        review_stats = review_service.get_review_stats()

        print(f"  发布统计:")
        print(f"    总发布数: {stats['total']}")
        print(f"    已发布: {stats['published']}")
        print(f"    待发布: {stats['scheduled']}")
        print(f"    发布失败: {stats['failed']}")
        print(f"    发布率: {stats['publish_rate']:.1f}%")
        print()

        print(f"  审核统计:")
        print(f"    总审核数: {review_stats['total']}")
        print(f"    已批准: {review_stats['approved']}")
        print(f"    自动批准: {review_stats['auto_approved']}")
        print(f"    批准率: {review_stats['approval_rate']:.1f}%")
        print()

        print(f"  本次发布结果:")
        print(f"    成功: {success_count}")
        print(f"    失败: {failed_count}")
        print()

        # [8] 显示最近发布的文章
        if success_count > 0:
            print("[8] 最近发布的文章")
            print("-"*80)
            recent = session.query(PublishedContent).filter(
                PublishedContent.publish_status == "published"
            ).order_by(PublishedContent.published_at.desc()).limit(10).all()

            for idx, pub in enumerate(recent[:5], 1):
                raw_news = session.query(RawNews).filter(
                    RawNews.id == pub.raw_news_id
                ).first()
                if raw_news:
                    print(f"  [{idx}] {raw_news.title[:60]}...")
                    print(f"      发布时间: {pub.published_at}")
                    if pub.wechat_url:
                        print(f"      微信链接: {pub.wechat_url}")
            print()

        print("="*80)
        print("发布流程完成!")
        print("="*80)
        print()

        return 0 if failed_count == 0 else 1

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        session.close()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
