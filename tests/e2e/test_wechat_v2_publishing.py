#!/usr/bin/env python3
"""
WeChat V2 API 端到端测试

测试新的永久素材 API 和群发接口的完整发布流程。

Usage:
    python tests/e2e/test_wechat_v2_publishing.py [num_articles]

Example:
    python tests/e2e/test_wechat_v2_publishing.py 5    # 发布5篇文章
    python tests/e2e/test_wechat_v2_publishing.py      # 使用默认3篇
"""

import sys
import os
from pathlib import Path
import io
import asyncio
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
from src.models import RawNews, ProcessedNews, ContentReview, PublishedContent, WeChatMediaCache
from src.services.workflow.wechat_workflow_v2 import WeChatPublishingWorkflowV2


def print_header(title):
    """打印标题"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_step(num, title):
    """打印步骤标题"""
    print(f"\n[步骤 {num}] {title}")
    print("-" * 80)


def main():
    """主函数"""

    print_header("WeChat V2 API 端到端发布测试")

    # 获取命令行参数
    num_articles = 3
    if len(sys.argv) > 1:
        try:
            num_articles = int(sys.argv[1])
        except ValueError:
            num_articles = 3

    print(f"配置: 发布 {num_articles} 篇文章\n")

    # 初始化数据库
    get_settings.cache_clear()
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # ===== 步骤 1: 配置验证 =====
        print_step(1, "配置验证")

        if not settings.openai_api_key:
            print("  ⚠️  OpenAI API Key 未配置")
        else:
            print(f"  ✓ OpenAI API Key 已配置")

        if not settings.wechat_app_id or not settings.wechat_app_secret:
            print("  ✗ WeChat 凭证未配置！无法测试。")
            return 1
        else:
            print(f"  ✓ WeChat App ID 已配置")
            print(f"  ✓ WeChat App Secret 已配置")

        print()

        # ===== 步骤 2: 数据库统计 =====
        print_step(2, "数据库统计")

        total_raw = session.query(RawNews).count()
        total_scored = session.query(ProcessedNews).count()
        total_reviewed = session.query(ContentReview).count()
        total_published = session.query(PublishedContent).count()
        total_media_cache = session.query(WeChatMediaCache).count()

        print(f"  原始文章:   {total_raw:>6d} 篇")
        print(f"  已评分:     {total_scored:>6d} 篇 ({total_scored*100//total_raw if total_raw > 0 else 0}%)")
        print(f"  已审核:     {total_reviewed:>6d} 篇")
        print(f"  已发布:     {total_published:>6d} 篇")
        print(f"  媒体缓存:   {total_media_cache:>6d} 项")
        print()

        # ===== 步骤 3: 准备测试数据 =====
        print_step(3, "准备测试数据")

        # 获取未审核的文章
        reviewed_ids = [row[0] for row in session.query(ContentReview.processed_news_id).all()]
        unreviewed = session.query(ProcessedNews).filter(
            ~ProcessedNews.id.in_(reviewed_ids) if reviewed_ids else True
        ).limit(num_articles).all()

        if not unreviewed:
            print(f"  ⚠️  没有待审核的文章")

            # 获取已审核但未发布的文章
            published_ids = [row[0] for row in session.query(PublishedContent.processed_news_id).all()]
            unreviewed = session.query(ProcessedNews).filter(
                ~ProcessedNews.id.in_(published_ids) if published_ids else True
            ).limit(num_articles).all()

            if not unreviewed:
                print(f"  ✗ 没有可用的文章进行测试")
                return 1

        print(f"  找到 {len(unreviewed)} 篇待审核的文章")

        # 为待审核的文章创建审核记录
        from src.services.review.review_service import ReviewService
        review_service = ReviewService(session)

        for processed in unreviewed:
            existing = session.query(ContentReview).filter(
                ContentReview.processed_news_id == processed.id
            ).first()

            if not existing:
                review_service.create_review(processed.id)
                print(f"  创建审核记录: {processed.id}")

        # 设置为已批准
        from src.models import ContentReview as CR
        session.query(CR).filter(
            CR.processed_news_id.in_([p.id for p in unreviewed])
        ).update({"status": "approved"})
        session.commit()

        print(f"  ✓ 准备完成，{len(unreviewed)} 篇文章已标记为批准")
        print()

        # ===== 步骤 4: 执行 V2 发布工作流 =====
        print_step(4, "执行 V2 发布工作流")

        print(f"  初始化 WeChat V2 发布工作流...")
        workflow = WeChatPublishingWorkflowV2(
            db_session=session,
            wechat_app_id=settings.wechat_app_id,
            wechat_app_secret=settings.wechat_app_secret
        )

        print(f"  启动异步发布任务...\n")

        # 运行异步工作流
        result = asyncio.run(workflow.execute(batch_size=min(3, len(unreviewed))))

        print(f"\n  工作流执行结果:")
        print(f"    成功: {result.get('published_count', 0)} 篇")
        print(f"    失败: {result.get('failed_count', 0)} 篇")

        if result.get('articles'):
            print(f"\n  已发布的文章:")
            for article in result['articles']:
                print(f"    - {article['title'][:50]}...")
                print(f"      media_id: {article['media_id']}")
                print(f"      msg_id: {article['msg_id']}")

        if result.get('failed_articles'):
            print(f"\n  失败的文章:")
            for title in result['failed_articles']:
                print(f"    - {title[:50]}...")

        print()

        # ===== 步骤 5: 验证数据库状态 =====
        print_step(5, "验证数据库状态")

        # 刷新统计
        total_published_new = session.query(PublishedContent).count()
        total_media_cache_new = session.query(WeChatMediaCache).count()

        print(f"  已发布文章: {total_published} → {total_published_new} (增加 {total_published_new - total_published})")
        print(f"  媒体缓存:   {total_media_cache} → {total_media_cache_new} (增加 {total_media_cache_new - total_media_cache})")

        # 显示最新发布记录
        latest_published = session.query(PublishedContent).order_by(
            PublishedContent.publish_timestamp.desc()
        ).limit(3).all()

        if latest_published:
            print(f"\n  最新发布记录:")
            for pub in latest_published:
                print(f"    - 状态: {pub.publish_status}")
                print(f"      频道: {pub.channel}")
                print(f"      时间: {pub.publish_timestamp}")
                metadata = pub.metadata or {}
                print(f"      media_id: {metadata.get('media_id', 'N/A')}")

        print()

        # ===== 最终结果 =====
        print_header("测试完成")

        if result['success']:
            print("✅ 所有文章发布成功！\n")
            return 0
        else:
            print("⚠️  部分文章发布失败，请检查日志。\n")
            return result['failed_count']

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        session.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
