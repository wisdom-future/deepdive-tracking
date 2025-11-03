#!/usr/bin/env python3
"""
WeChat Publishing Test - 测试微信发布功能

功能：
  - 演示 WeChat 发布渠道的集成
  - 展示 WeChat 发布 API 的使用方式
  - 验证 WeChat 发布服务的功能完整性
"""

import sys
from pathlib import Path
import io

# 设置标准输出编码为 UTF-8 (Windows 兼容)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.channels.wechat_channel import WeChatPublisher

def main():
    """Main test function"""

    print("\n" + "="*80)
    print("WeChat Publishing Channel - Integration Test")
    print("="*80)
    print()

    try:
        # [1] 展示 WeChat 发布器的功能
        print("[1] WeChat 发布器功能演示")
        print("-"*80)
        print()
        print("  WeChatPublisher 类提供以下功能：")
        print()
        print("  1. publish_article()")
        print("     - 发布文章到微信公众号")
        print("     - 支持标题、作者、内容、摘要")
        print("     - 支持封面图片")
        print("     - 支持来源链接")
        print()
        print("  2. send_message()")
        print("     - 向用户发送单条消息")
        print("     - 支持文本、图片、图文消息类型")
        print()
        print("  3. get_followers_count()")
        print("     - 获取公众号粉丝数")
        print()
        print("  4. verify_message_signature()")
        print("     - 验证来自微信的消息签名")
        print("     - 用于 Webhook 集成")
        print()

        # [2] 验证 WeChat API 集成
        print("[2] WeChat API 集成验证")
        print("-"*80)
        print()

        # 检查是否有 WeChat 凭证
        import os
        wechat_app_id = os.getenv('WECHAT_APP_ID', 'not_configured')
        wechat_app_secret = os.getenv('WECHAT_APP_SECRET', 'not_configured')

        if wechat_app_id == 'not_configured':
            print("  WeChat 凭证未配置")
            print()
            print("  要使用 WeChat 发布功能，需要：")
            print("  1. 申请微信公众号官方账号")
            print("  2. 在公众号后台获取 App ID 和 App Secret")
            print("  3. 设置环境变量：")
            print("     - WECHAT_APP_ID")
            print("     - WECHAT_APP_SECRET")
            print()
            print("  快速开始指南：")
            print("  1. 微信公众号申请：https://mp.weixin.qq.com")
            print("  2. 开发配置：https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/")
            print("  3. API 文档：https://developers.weixin.qq.com/doc/offiaccount/Message_Management/")
            print()
        else:
            print("  已检测到 WeChat 凭证 (部分显示)")
            print(f"  App ID: {wechat_app_id[:10]}...")
            print()

            # 尝试初始化 WeChat 发布器
            print("  初始化 WeChat 发布器...")
            try:
                publisher = WeChatPublisher(
                    app_id=wechat_app_id,
                    app_secret=wechat_app_secret
                )
                print("  OK - WeChat 发布器已初始化")
                print()

                # 尝试获取访问令牌
                print("  获取 WeChat 访问令牌...")
                try:
                    token = publisher._get_access_token()
                    print(f"  OK - 成功获取访问令牌 (prefix: {token[:10]}...)")
                except Exception as e:
                    print(f"  FAIL - 无法获取访问令牌")
                    print(f"  原因: {str(e)[:100]}")

            except Exception as e:
                print(f"  ERROR - 无法初始化 WeChat 发布器: {e}")

        print()

        # [3] 发布服务集成
        print("[3] 发布服务集成验证")
        print("-"*80)
        print()

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from src.config import get_settings
        from src.services.publishing_service import PublishingService

        settings = get_settings()
        engine = create_engine(settings.database_url, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()

        # 使用 WeChat 凭证初始化发布服务
        publishing_service = PublishingService(
            db_session=session,
            wechat_app_id=os.getenv('WECHAT_APP_ID'),
            wechat_app_secret=os.getenv('WECHAT_APP_SECRET')
        )

        if publishing_service.wechat_publisher:
            print("  OK - 发布服务已集成 WeChat 发布器")
            print("  可用方法：publish_to_wechat()")
        else:
            print("  NOTE - WeChat 发布器未配置")
            print("  需要设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET 环境变量")

        session.close()
        print()

        # [4] 发布工作流示例
        print("[4] WeChat 发布工作流")
        print("-"*80)
        print()
        print("  标准工作流：")
        print()
        print("  1. 采集阶段")
        print("     python scripts/01-collection/collect_rss.py")
        print()
        print("  2. 评分阶段")
        print("     python scripts/02-evaluation/score_collected_news.py 10")
        print()
        print("  3. 自动审核（可选）")
        print("     python scripts/03-review/auto_review_articles.py")
        print()
        print("  4. 准备发布计划")
        print("     python scripts/04-publish/prepare_publishing_plan.py")
        print()
        print("  5. 发布到 WeChat")
        print("     python scripts/04-publish/publish_to_wechat.py")
        print()
        print("  6. 查看发布统计")
        print("     python scripts/03-verification/view_summary.py")
        print()

        # [5] 数据流图
        print("[5] WeChat 发布数据流")
        print("-"*80)
        print()
        print("  原始新闻 → AI 评分 → 内容审核 → 发布计划 → WeChat 发布 → 粉丝")
        print("   (RawNews)   (Score)   (Review)   (Plan)     (publish)   (读者)")
        print()
        print("  数据库表关系：")
        print("  - raw_news: 原始新闻内容")
        print("  - processed_news: AI 评分结果")
        print("  - content_review: 人工审核记录")
        print("  - published_content: 发布记录和链接")
        print()

        print("="*80)
        print("WeChat 发布功能概览")
        print("="*80)
        print()

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
