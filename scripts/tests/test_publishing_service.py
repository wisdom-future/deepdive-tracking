#!/usr/bin/env python3
"""
Test Publishing Service - 测试内容发布服务

功能：
  - 创建发布计划
  - 测试发布工作流 (标记为发布)
  - 显示发布统计
"""

import sys
from pathlib import Path
import io
from datetime import datetime, timedelta

# 设置标准输出编码为 UTF-8 (Windows 兼容)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models import ProcessedNews
from src.services.publishing_service import PublishingService

def main():
    """Main test function"""
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n" + "=" * 80)
    print("Test Publishing Service")
    print("=" * 80)
    print()

    try:
        # [1] 获取已评分的文章
        print("[1] 查询已评分的文章...")
        processed_articles = session.query(ProcessedNews).filter(
            ProcessedNews.id > 0
        ).limit(5).all()

        if not processed_articles:
            print("    没有已评分的文章")
            return 0

        print(f"    找到 {len(processed_articles)} 条已评分的文章")
        print()

        # [2] 初始化发布服务
        print("[2] 初始化发布服务...")
        publishing_service = PublishingService(session)
        print("    OK - 服务就绪")
        print()

        # [3] 创建发布计划
        print("[3] 创建发布计划...")
        published_contents = []
        for idx, article in enumerate(processed_articles, 1):
            try:
                # 为每条创建不同的发布计划
                if idx == 1:
                    channels = ["wechat", "xiaohongshu", "website"]
                elif idx == 2:
                    channels = ["wechat", "website"]
                else:
                    channels = ["website"]

                published_content = publishing_service.create_publishing_plan(
                    processed_news_id=article.id,
                    channels=channels,
                    scheduled_at=datetime.utcnow() + timedelta(hours=idx)
                )
                published_contents.append(published_content)
                print(f"    [{idx}] 为文章 {article.id} 创建发布计划")
                print(f"        - ID: {published_content.id}")
                print(f"        - 频道: {', '.join(channels)}")
                print(f"        - 状态: {published_content.publish_status}")
            except Exception as e:
                print(f"    [{idx}] 错误: {str(e)[:60]}")

        print()

        # [4] 测试发布工作流
        print("[4] 测试发布工作流...")
        print()

        if len(published_contents) >= 1:
            pc = published_contents[0]
            print("    [A] 发布到微信")
            result = publishing_service.publish_to_channel(
                pc.id,
                "wechat",
                "https://mp.weixin.qq.com/s/XXXXX",
                "msg_12345",
                "test_publisher"
            )
            print(f"        状态: {result.publish_status}")
            print(f"        微信URL: {result.wechat_url}")
            print()

        if len(published_contents) >= 2:
            pc = published_contents[1]
            print("    [B] 发布到小红书和网站")
            # 先发布小红书
            result = publishing_service.publish_to_channel(
                pc.id,
                "xiaohongshu",
                "https://www.xiaohongshu.com/discovery/item/XXXXX",
                "post_67890",
                "test_publisher"
            )
            print(f"        小红书URL: {result.xiaohongshu_url}")
            # 再发布网站
            result = publishing_service.publish_to_channel(
                pc.id,
                "website",
                "https://example.com/article/XXXXX",
                "",
                "test_publisher"
            )
            print(f"        网站URL: {result.web_url}")
            print(f"        最终状态: {result.publish_status}")
            print()

        if len(published_contents) >= 3:
            pc = published_contents[2]
            print("    [C] 标记为已发布 (完整内容)")
            result = publishing_service.mark_published(
                pc.id,
                final_title="Final Published Title",
                final_summary_pro="Final professional summary",
                final_keywords=["keyword1", "keyword2"],
                publisher_name="test_publisher"
            )
            print(f"        最终标题: {result.final_title}")
            print(f"        发布状态: {result.publish_status}")
            print(f"        发布时间: {result.published_at}")
            print()

        # [5] 获取待发布的内容
        print("[5] 待发布的内容")
        print("=" * 80)
        scheduled_content = publishing_service.get_scheduled_content(limit=5)
        print(f"  找到 {len(scheduled_content)} 条待发布的内容")
        for content in scheduled_content[:3]:
            print(f"    - ID: {content.id}, 状态: {content.publish_status}, "
                  f"频道: {', '.join(content.channels)}")
        print()

        # [6] 获取发布统计
        print("[6] 发布统计")
        print("=" * 80)
        stats = publishing_service.get_publishing_stats()
        print(f"  总发布数: {stats['total']}")
        print(f"  已发布: {stats['published']}")
        print(f"  待发布: {stats['scheduled']}")
        print(f"  发布失败: {stats['failed']}")
        print(f"  发布率: {stats['publish_rate']:.1f}%")
        print()

        print("=" * 80)
        print("发布服务测试完成!")
        print("=" * 80)
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
    exit_code = main()
    sys.exit(exit_code)
