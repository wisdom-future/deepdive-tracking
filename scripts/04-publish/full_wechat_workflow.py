#!/usr/bin/env python3
"""
Complete WeChat Publishing Workflow - 完整的微信发布工作流

这个脚本演示完整的工作流：
1. 采集新闻
2. AI 评分
3. 自动审核
4. 发布到微信
5. 显示结果

使用方式：
  python scripts/04-publish/full_wechat_workflow.py [number_of_articles]
"""

import sys
from pathlib import Path
import io
import subprocess
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
from src.models import PublishedContent, ContentReview
import os

def run_command(cmd, description):
    """运行命令并显示进度"""
    print(f"\n{'='*80}")
    print(f"[步骤] {description}")
    print(f"{'='*80}")
    print(f"执行: {cmd}")
    print()

    result = subprocess.run(cmd, shell=True, capture_output=False)
    if result.returncode != 0:
        print(f"❌ {description} 失败")
        return False
    else:
        print(f"✅ {description} 成功")
    return True

def main():
    """Main workflow function"""

    print("\n" + "="*80)
    print("微信公众号完整发布工作流")
    print("="*80)
    print()

    # 获取要处理的文章数
    num_articles = 5  # 默认
    if len(sys.argv) > 1:
        try:
            num_articles = int(sys.argv[1])
        except ValueError:
            num_articles = 5

    print(f"配置: 处理 {num_articles} 篇文章")
    print()

    # 检查 WeChat 凭证
    print("[检查] WeChat 凭证...")
    wechat_app_id = os.getenv('WECHAT_APP_ID')
    wechat_app_secret = os.getenv('WECHAT_APP_SECRET')

    if not wechat_app_id or not wechat_app_secret:
        print("❌ WeChat 凭证未配置")
        print()
        print("请设置环境变量:")
        print("  export WECHAT_APP_ID='wxc3d4bc2d698da563'")
        print("  export WECHAT_APP_SECRET='e9f5d2a2b2ffe5bc4e23c9904c0021b6'")
        return 1

    print("✅ WeChat 凭证已配置")
    print()

    try:
        # [1] 采集新闻
        if not run_command(
            "python scripts/01-collection/collect_rss.py",
            "采集 RSS 新闻"
        ):
            return 1

        # [2] AI 评分
        if not run_command(
            f"python scripts/02-evaluation/score_collected_news.py {num_articles}",
            f"AI 评分已采集的新闻"
        ):
            return 1

        # [3] 自动审核
        if not run_command(
            "python scripts/03-review/auto_review_articles.py",
            "自动审核已评分的文章"
        ):
            return 1

        # [4] 微信发布
        if not run_command(
            "python scripts/04-publish/publish_to_wechat.py",
            "发布到微信公众号"
        ):
            return 1

        # [5] 显示最终统计
        print(f"\n{'='*80}")
        print("[总结] 工作流完成")
        print(f"{'='*80}")
        print()

        settings = get_settings()
        engine = create_engine(settings.database_url, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()

        # 显示统计
        total_reviews = session.query(ContentReview).count()
        approved_reviews = session.query(ContentReview).filter(
            ContentReview.status == "approved"
        ).count()
        published = session.query(PublishedContent).filter(
            PublishedContent.publish_status == "published"
        ).count()

        print(f"📊 最终统计:")
        print(f"  总审核数: {total_reviews}")
        print(f"  已批准: {approved_reviews}")
        print(f"  已发布到微信: {published}")
        print()

        # 显示发布的文章
        from src.models import RawNews

        published_contents = session.query(PublishedContent).filter(
            PublishedContent.publish_status == "published"
        ).order_by(PublishedContent.published_at.desc()).limit(10).all()

        if published_contents:
            print(f"📢 最近发布的文章:")
            for idx, pub in enumerate(published_contents[:5], 1):
                raw_news = session.query(RawNews).filter(
                    RawNews.id == pub.raw_news_id
                ).first()
                if raw_news:
                    print(f"  [{idx}] {raw_news.title[:60]}...")
                    if pub.wechat_url:
                        print(f"      WeChat: {pub.wechat_url}")
            print()

        session.close()

        print("="*80)
        print("✅ 完整工作流执行成功！")
        print("="*80)
        print()

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
