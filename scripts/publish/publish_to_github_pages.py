#!/usr/bin/env python3
"""
Publish TOP AI News to GitHub Pages via GitHub API
使用GitHub API直接推送HTML到仓库，适用于Cloud Run等无状态环境
"""
import sys
import os
import base64
import asyncio
from datetime import datetime
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config.settings import get_settings
from src.models import ProcessedNews
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from src.database.connection import get_session
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def push_file_to_github(
    github_token: str,
    repo: str,  # format: "username/repo"
    file_path: str,  # path in repo, e.g., "docs/digests/2025-11-08.html"
    content: str,
    commit_message: str,
    branch: str = "main"
) -> dict:
    """
    使用GitHub API推送单个文件到仓库

    Args:
        github_token: GitHub Personal Access Token
        repo: 仓库名称 (username/repo)
        file_path: 文件在仓库中的路径
        content: 文件内容
        commit_message: 提交信息
        branch: 分支名称

    Returns:
        dict: API响应结果
    """
    # GitHub API URL
    api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"

    # 编码内容为base64
    content_bytes = content.encode('utf-8')
    content_b64 = base64.b64encode(content_bytes).decode('utf-8')

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    async with aiohttp.ClientSession() as session:
        # 首先尝试获取文件的SHA（如果文件已存在）
        sha = None
        async with session.get(api_url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                sha = data.get('sha')
                logger.info(f"文件已存在，SHA: {sha}")

        # 准备提交数据
        payload = {
            "message": commit_message,
            "content": content_b64,
            "branch": branch
        }

        if sha:
            payload["sha"] = sha  # 更新现有文件需要提供SHA

        # 创建或更新文件
        async with session.put(api_url, headers=headers, json=payload) as resp:
            if resp.status in [200, 201]:
                result = await resp.json()
                logger.info(f"✓ 文件推送成功: {file_path}")
                return {
                    "success": True,
                    "file_path": file_path,
                    "html_url": result.get('content', {}).get('html_url'),
                    "sha": result.get('content', {}).get('sha')
                }
            else:
                error_text = await resp.text()
                logger.error(f"✗ 文件推送失败: HTTP {resp.status} - {error_text}")
                return {
                    "success": False,
                    "error": f"HTTP {resp.status}: {error_text}"
                }


def generate_digest_html(date_str: str, top_news: list) -> str:
    """生成每日摘要HTML"""
    news_cards = []

    for idx, news in enumerate(top_news, 1):
        if not news.raw_news:
            continue

        title = news.raw_news.title
        summary = news.summary_pro or news.summary_sci or "暂无摘要"
        url = news.raw_news.url or "#"
        score = news.score or 0
        category = news.category or "AI News"
        author = news.raw_news.source_name or "Unknown"

        # 评分颜色
        if score >= 80:
            badge_color = "#4caf50"
        elif score >= 60:
            badge_color = "#2196f3"
        else:
            badge_color = "#ff9800"

        card_html = f"""
        <div class="news-card">
            <div class="card-header">
                <div class="card-number">{idx}</div>
                <div class="card-content">
                    <h3><a href="{url}" target="_blank">{title}</a></h3>
                    <p class="summary">{summary}</p>
                    <div class="meta">
                        <span class="badge" style="background: {badge_color};">{int(score)}分</span>
                        <span class="category">{category}</span>
                        <span class="author">来源: {author}</span>
                    </div>
                </div>
            </div>
        </div>
        """
        news_cards.append(card_html)

    news_html = "\n".join(news_cards)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepDive AI Daily - {date_str}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.2em;
            color: #667eea;
            margin-bottom: 10px;
        }}

        .header .date {{
            color: #666;
            font-size: 1.1em;
        }}

        .news-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }}

        .news-card:hover {{
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
            transform: translateY(-2px);
        }}

        .card-header {{
            display: flex;
            gap: 20px;
        }}

        .card-number {{
            flex-shrink: 0;
            width: 40px;
            height: 40px;
            background: #667eea;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.2em;
        }}

        .card-content {{
            flex: 1;
        }}

        .card-content h3 {{
            font-size: 1.2em;
            margin-bottom: 12px;
        }}

        .card-content h3 a {{
            color: #333;
            text-decoration: none;
        }}

        .card-content h3 a:hover {{
            color: #667eea;
        }}

        .summary {{
            color: #666;
            line-height: 1.6;
            margin-bottom: 12px;
        }}

        .meta {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            font-size: 0.9em;
        }}

        .badge {{
            padding: 4px 12px;
            border-radius: 20px;
            color: white;
            font-weight: 500;
        }}

        .category, .author {{
            color: #999;
        }}

        .footer {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            color: #999;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}

        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 DeepDive AI Daily</h1>
            <div class="date">{date_str} · TOP {len(top_news)} AI资讯精选</div>
        </div>

        {news_html}

        <div class="footer">
            <p>由 <a href="https://github.com/wisdom-future/deepdive-tracking">DeepDive Tracking</a> 自动生成</p>
            <p style="margin-top: 10px; font-size: 0.9em;">更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""


def generate_index_html(digests: list) -> str:
    """生成索引页面HTML"""
    digest_links = []
    for digest in sorted(digests, reverse=True):
        digest_links.append(f"""
        <div class="digest-item">
            <a href="digests/{digest}">
                <span class="date">📅 {digest.replace('.html', '')}</span>
                <span class="arrow">→</span>
            </a>
        </div>
        """)

    links_html = "\n".join(digest_links)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepDive AI Daily - 每日精选归档</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }}

        .header h1 {{
            font-size: 3em;
            margin-bottom: 15px;
            text-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        }}

        .header p {{
            font-size: 1.2em;
            opacity: 0.95;
        }}

        .digests-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }}

        .digest-item {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }}

        .digest-item:hover {{
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
            transform: translateY(-4px);
        }}

        .digest-item a {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 25px 30px;
            text-decoration: none;
            color: inherit;
        }}

        .digest-item .date {{
            font-size: 1.1em;
            font-weight: 600;
            color: #333;
        }}

        .digest-item .arrow {{
            font-size: 1.5em;
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 DeepDive AI Daily</h1>
            <p>AI领域每日精选资讯归档</p>
        </div>

        <div class="digests-grid">
            {links_html}
        </div>
    </div>
</body>
</html>"""


async def main():
    """主函数"""
    settings = get_settings()

    print("=" * 80)
    print("PUBLISH TO GITHUB PAGES - Using GitHub API")
    print("=" * 80)

    # 检查GitHub配置
    print("\n1. 检查GitHub配置...")
    if not settings.github_token or settings.github_token == "your_github_token":
        print("[错误] GitHub Token未配置")
        print("\n请按以下步骤配置:")
        print("1. 创建GitHub Personal Access Token:")
        print("   https://github.com/settings/tokens/new")
        print("   勾选权限: repo (完整仓库访问)")
        print("")
        print("2. 在GCP Secret Manager中添加:")
        print("   Secret名称: GITHUB_TOKEN")
        print("   Secret值: 你的token")
        print("")
        print("3. 更新.env文件:")
        print("   GITHUB_TOKEN=ghp_your_token_here")
        print("   GITHUB_REPO=wisdom-future/deepdive-tracking")
        print("   GITHUB_USERNAME=wisdom-future")
        return False

    if not settings.github_repo:
        print("[错误] GitHub仓库未配置")
        return False

    print(f"[✓] GitHub配置正常")
    print(f"    仓库: {settings.github_repo}")

    # 获取TOP新闻
    print("\n2. 获取TOP新闻...")
    try:
        session = get_session()
        top_news = session.query(ProcessedNews).options(
            joinedload(ProcessedNews.raw_news)
        ).order_by(
            desc(ProcessedNews.score)
        ).limit(10).all()
        session.close()

        if not top_news:
            print("[错误] 数据库中没有新闻")
            return False

        print(f"[✓] 找到 {len(top_news)} 条TOP新闻")
    except Exception as e:
        print(f"[错误] 数据库查询失败: {e}")
        return False

    # 生成HTML
    print("\n3. 生成HTML内容...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    digest_html = generate_digest_html(date_str, top_news)
    index_html = generate_index_html([f"{date_str}.html"])
    print(f"[✓] HTML生成完成")

    # 推送到GitHub
    print("\n4. 推送到GitHub...")
    try:
        # 推送每日摘要
        digest_result = await push_file_to_github(
            github_token=settings.github_token,
            repo=settings.github_repo,
            file_path=f"docs/news/digests/{date_str}.html",
            content=digest_html,
            commit_message=f"📰 发布每日精选: {date_str}"
        )

        if not digest_result.get('success'):
            print(f"[错误] 摘要推送失败: {digest_result.get('error')}")
            return False

        print(f"[✓] 每日摘要已推送")

        # 推送索引页面
        index_result = await push_file_to_github(
            github_token=settings.github_token,
            repo=settings.github_repo,
            file_path="docs/news/index.html",
            content=index_html,
            commit_message=f"📑 更新索引页面: {date_str}"
        )

        if not index_result.get('success'):
            print(f"[警告] 索引推送失败: {index_result.get('error')}")
        else:
            print(f"[✓] 索引页面已更新")

    except Exception as e:
        print(f"[错误] GitHub推送失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 完成
    print("\n" + "=" * 80)
    print("✓ 发布成功！")
    print("=" * 80)
    print(f"\n访问地址:")
    print(f"https://wisdom-future.github.io/deepdive-tracking/news/digests/{date_str}.html")
    print(f"https://wisdom-future.github.io/deepdive-tracking/news/index.html")
    print("")
    print("注意: 首次发布需要在GitHub仓库设置中启用GitHub Pages:")
    print("Settings → Pages → Source: Deploy from a branch")
    print("Branch: main, Folder: /docs")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[致命错误] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
