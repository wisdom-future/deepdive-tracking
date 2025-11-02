#!/usr/bin/env python3
"""
WeChat Publishing Script - 发布已审核的文章到微信公众号

使用 WeChatPublishingWorkflow 服务进行完整的微信发布工作流
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
from src.services.workflow.wechat_workflow import WeChatPublishingWorkflow
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

        # [2] 初始化工作流
        print("[2] 初始化 WeChat 发布工作流...")
        workflow = WeChatPublishingWorkflow(
            db_session=session,
            wechat_app_id=wechat_app_id,
            wechat_app_secret=wechat_app_secret
        )
        print("    ✅ WeChat 发布工作流就绪")
        print()

        # [3] 执行发布工作流
        print("[3] 执行 WeChat 发布工作流...")
        print()

        result = workflow.execute()

        if not result['success']:
            print(f"    ❌ 工作流失败: {result.get('error', 'Unknown error')}")
            return 1

        # [4] 显示发布结果
        print("[4] 发布结果")
        print("="*80)
        print(f"  ✅ 发布成功: {result['published_count']} 篇")
        print(f"  ❌ 发布失败: {result['failed_count']} 篇")
        print()

        if result['articles']:
            print("[5] 已发布的文章")
            print("-"*80)
            for idx, article in enumerate(result['articles'], 1):
                print(f"  [{idx}] {article['title'][:60]}...")
                print(f"      链接: {article['url']}")
            print()

        # [6] 显示统计
        print("[6] 发布统计")
        print("="*80)
        stats = result['stats']
        print(f"  总发布数: {stats['total']}")
        print(f"  已发布: {stats['published']}")
        print(f"  待发布: {stats['scheduled']}")
        print(f"  发布失败: {stats['failed']}")
        print(f"  发布率: {stats['publish_rate']:.1f}%")
        print()

        # [7] 显示最近发布的文章
        recent_articles = workflow.get_published_articles(limit=5)
        if recent_articles:
            print("[7] 最近发布的文章")
            print("-"*80)
            for idx, article in enumerate(recent_articles, 1):
                print(f"  [{idx}] {article['title'][:60]}...")
                print(f"      发布时间: {article['published_at']}")
                print(f"      链接: {article['url']}")
            print()

        print("="*80)
        print("发布流程完成!")
        print("="*80)
        print()

        return 0 if result['failed_count'] == 0 else 1

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
