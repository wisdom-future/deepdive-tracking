"""
GitHub HTML Publisher - 发布文章为HTML格式到GitHub仓库

支持功能：
- 生成美观的HTML文章页面
- 上传到GitHub仓库
- 生成索引页面
- 自动提交和推送
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import subprocess
import html
import asyncio

logger = logging.getLogger(__name__)


class GitHubPublisher:
    """GitHub HTML发布器"""

    def __init__(
        self,
        github_token: str,  # noqa: S107
        github_repo: str,
        github_username: str,
        local_repo_path: Optional[str] = None
    ):
        """
        初始化GitHub发布器

        Args:
            github_token: 访问令牌（从环境变量获取）
            github_repo: 仓库名称 (username/repo)
            github_username: GitHub用户名
            local_repo_path: 本地仓库路径，如果为None则使用临时目录
        """
        self.github_token = github_token  # noqa: S105
        self.github_repo = github_repo
        self.github_username = github_username
        self.local_repo_path = local_repo_path or f"/tmp/{github_repo.split('/')[-1]}"
        self.logger = logger
        self.articles_dir = "articles"
        self.index_file = "index.html"

    async def publish_article(
        self,
        title: str,
        content: str,
        summary: str,
        author: str,
        source_url: str,
        score: float,
        category: str,
        article_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        发布单篇文章到GitHub

        Args:
            title: 文章标题
            content: 文章内容（HTML格式）
            summary: 摘要
            author: 作者
            source_url: 源URL
            score: 评分 (0-100)
            category: 分类
            article_id: 文章ID

        Returns:
            {
                "success": bool,
                "article_url": str,
                "commit_sha": str,
                "error": str (if failed)
            }
        """
        try:
            # 初始化仓库
            await self._init_repo()

            # 生成文章文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{article_id or timestamp}_{self._sanitize_filename(title)}.html"
            article_path = Path(self.local_repo_path) / self.articles_dir / filename

            # 确保目录存在
            article_path.parent.mkdir(parents=True, exist_ok=True)

            # 生成HTML内容
            html_content = self._generate_article_html(
                title=title,
                content=content,
                summary=summary,
                author=author,
                source_url=source_url,
                score=score,
                category=category,
                publish_date=datetime.now()
            )

            # 写入文件
            article_path.write_text(html_content, encoding='utf-8')
            self.logger.info(f"生成文章HTML: {article_path}")

            # 更新索引
            await self._update_index()

            # 提交和推送
            commit_sha = await self._commit_and_push(
                message=f"发布: {title[:50]}",
                files=[str(article_path), str(Path(self.local_repo_path) / self.index_file)]
            )

            # 生成URL
            article_url = f"https://raw.githubusercontent.com/{self.github_repo}/main/{self.articles_dir}/{filename}"

            return {
                "success": True,
                "article_url": article_url,
                "commit_sha": commit_sha,
                "filename": filename
            }

        except Exception as e:
            self.logger.error(f"✗ 发布文章失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def publish_batch_articles(
        self,
        articles: List[Dict[str, Any]],
        batch_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批量发布文章到GitHub

        Args:
            articles: 文章列表，每个包含 title, content, summary, author, source_url, score, category
            batch_name: 批次名称（用于索引）

        Returns:
            {
                "success": bool,
                "published_count": int,
                "failed_count": int,
                "articles": [...],
                "batch_url": str
            }
        """
        batch_name = batch_name or datetime.now().strftime("%Y%m%d")
        published = []
        failed = []

        try:
            await self._init_repo()

            for article in articles:
                result = await self.publish_article(
                    title=article.get('title'),
                    content=article.get('content'),
                    summary=article.get('summary'),
                    author=article.get('author'),
                    source_url=article.get('source_url'),
                    score=article.get('score', 0),
                    category=article.get('category'),
                    article_id=article.get('id')
                )

                if result.get('success'):
                    published.append(result)
                else:
                    failed.append(article.get('title'))

            # 生成批次摘要页面
            batch_summary = self._generate_batch_summary(batch_name, published)
            batch_path = Path(self.local_repo_path) / "batches" / f"{batch_name}.html"
            batch_path.parent.mkdir(parents=True, exist_ok=True)
            batch_path.write_text(batch_summary, encoding='utf-8')

            # 最后一次提交包含所有文件
            await self._commit_and_push(
                message=f"批量发布: {batch_name} ({len(published)} 篇)"
            )

            return {
                "success": len(failed) == 0,
                "published_count": len(published),
                "failed_count": len(failed),
                "articles": published,
                "failed_articles": failed,
                "batch_url": f"https://raw.githubusercontent.com/{self.github_repo}/main/batches/{batch_name}.html"
            }

        except Exception as e:
            self.logger.error(f"✗ 批量发布失败: {str(e)}")
            return {
                "success": False,
                "published_count": len(published),
                "failed_count": len(failed) + 1,
                "error": str(e)
            }

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名"""
        import re
        # 只保留字母、数字和下划线
        return re.sub(r'[^a-zA-Z0-9_-]', '_', filename)[:50]

    def _generate_article_html(
        self,
        title: str,
        content: str,
        summary: str,
        author: str,
        source_url: str,
        score: float,
        category: str,
        publish_date: datetime
    ) -> str:
        """生成文章HTML"""
        # 计算评分等级
        if score >= 80:
            score_level = "⭐⭐⭐⭐⭐"
        elif score >= 60:
            score_level = "⭐⭐⭐⭐"
        elif score >= 40:
            score_level = "⭐⭐⭐"
        elif score >= 20:
            score_level = "⭐⭐"
        else:
            score_level = "⭐"

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 20px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}

        .meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            padding: 20px 40px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}

        .meta-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        .meta-label {{
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 5px;
        }}

        .meta-value {{
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
        }}

        .score {{
            font-size: 1.5em;
            color: #ffc107;
        }}

        .content {{
            padding: 40px;
        }}

        .summary {{
            background: #e7f3ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 30px;
            border-radius: 5px;
        }}

        .summary-title {{
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}

        .article-content {{
            line-height: 1.8;
            color: #444;
        }}

        .article-content p {{
            margin-bottom: 15px;
        }}

        .article-content h2 {{
            font-size: 1.5em;
            margin: 30px 0 15px 0;
            color: #667eea;
        }}

        .article-content h3 {{
            font-size: 1.2em;
            margin: 20px 0 10px 0;
            color: #764ba2;
        }}

        .article-content pre {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            overflow-x: auto;
            margin: 15px 0;
        }}

        .article-content code {{
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}

        .article-content a {{
            color: #667eea;
            text-decoration: none;
            border-bottom: 1px solid #667eea;
        }}

        .article-content a:hover {{
            background: #667eea;
            color: white;
            padding: 0 2px;
        }}

        .source {{
            background: #f0f8ff;
            border: 1px solid #b3d9ff;
            padding: 15px;
            border-radius: 5px;
            margin: 30px 0 0 0;
        }}

        .source-title {{
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }}

        .source-link {{
            word-break: break-all;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            border-top: 1px solid #e9ecef;
            font-size: 0.9em;
            color: #6c757d;
            text-align: center;
        }}

        .back-link {{
            display: inline-block;
            margin-top: 20px;
            color: #667eea;
            text-decoration: none;
            border-bottom: 1px solid #667eea;
        }}

        .back-link:hover {{
            background: #667eea;
            color: white;
            padding: 0 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{html.escape(title)}</h1>
        </div>

        <div class="meta">
            <div class="meta-item">
                <div class="meta-label">评分</div>
                <div class="meta-value score">{score_level} {score}/100</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">分类</div>
                <div class="meta-value">{html.escape(category)}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">作者</div>
                <div class="meta-value">{html.escape(author)}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">发布时间</div>
                <div class="meta-value">{publish_date.strftime('%Y-%m-%d %H:%M')}</div>
            </div>
        </div>

        <div class="content">
            <div class="summary">
                <div class="summary-title">📌 内容摘要</div>
                <p>{html.escape(summary)}</p>
            </div>

            <div class="article-content">
                {content}
            </div>

            <div class="source">
                <div class="source-title">📚 原文链接</div>
                <div class="source-link"><a href="{html.escape(source_url)}" target="_blank">{html.escape(source_url)}</a></div>
            </div>

            <a href="../index.html" class="back-link">← 返回首页</a>
        </div>

        <div class="footer">
            <p>由 DeepDive Tracking 生成 | {publish_date.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""

    def _generate_batch_summary(self, batch_name: str, articles: List[Dict]) -> str:
        """
        生成批次总结HTML - 卡片形式展示所有TOP新闻

        Args:
            batch_name: 批次名称 (日期格式)
            articles: 发布的文章列表
        """
        # 从 published articles 中提取元数据并生成卡片
        cards_html = ""
        for idx, article in enumerate(articles, 1):
            filename = article.get('filename', '')
            # 从 article 数据中获取更详细的信息
            title = article.get('article_title', filename.replace('.html', '').replace('_', ' ')[:80]) if filename else 'Unknown'
            score = article.get('score', 0) or 0
            category = article.get('category', 'AI News')
            source = article.get('author', 'Unknown')

            # 评分徽章颜色
            if score >= 80:
                badge_bg = "#4caf50"  # 绿色
                score_label = "优秀"
            elif score >= 60:
                badge_bg = "#2196f3"  # 蓝色
                score_label = "良好"
            else:
                badge_bg = "#ff9800"  # 橙色
                score_label = "不错"

            cards_html += f"""
            <div class="article-card">
                <div class="card-header">
                    <div>
                        <h3><a href="articles/{filename}">{html.escape(title)}</a></h3>
                        <p class="article-meta">
                            <span class="badge">{html.escape(category)}</span>
                            <span class="source-meta">来源: {html.escape(source)}</span>
                        </p>
                    </div>
                    <div class="score-badge" style="background: {badge_bg};" title="{score_label}">{int(score)}</div>
                </div>
                <a href="articles/{filename}" class="read-more">阅读全文 →</a>
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepDive 每日速览 - {html.escape(batch_name)}</title>
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
            background: white;
            border-radius: 10px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}

        .header h1 {{
            font-size: 2em;
            color: #667eea;
            margin-bottom: 10px;
        }}

        .header .date {{
            color: #666;
            font-size: 1.1em;
        }}

        .header .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}

        .stat-item {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-label {{
            font-size: 0.9em;
            color: #999;
            margin-top: 5px;
        }}

        .articles {{
            display: grid;
            gap: 20px;
        }}

        .article-card {{
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            border-left: 5px solid #667eea;
            transition: all 0.3s ease;
        }}

        .article-card:hover {{
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            transform: translateY(-2px);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
            gap: 15px;
        }}

        .card-header h3 {{
            flex: 1;
            font-size: 1.2em;
            color: #333;
            margin: 0;
        }}

        .card-header h3 a {{
            color: #667eea;
            text-decoration: none;
        }}

        .card-header h3 a:hover {{
            text-decoration: underline;
        }}

        .score-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            color: white;
            font-weight: bold;
            font-size: 1.2em;
            flex-shrink: 0;
        }}

        .article-meta {{
            margin-bottom: 12px;
            font-size: 0.9em;
        }}

        .source-meta {{
            display: block;
            color: #999;
            font-size: 0.85em;
            margin-top: 8px;
        }}

        .badge {{
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
            margin-right: 8px;
        }}

        .article-summary {{
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
            font-size: 0.95em;
        }}

        .read-more {{
            display: inline-block;
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s;
            padding: 8px 0;
        }}

        .read-more:hover {{
            color: #764ba2;
            text-decoration: underline;
        }}

        .footer {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
            text-align: center;
            color: #999;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}

        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}

        @media (max-width: 600px) {{
            .header {{
                padding: 20px;
            }}

            .header h1 {{
                font-size: 1.5em;
            }}

            .stats {{
                gap: 20px;
            }}

            .card-header {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .score-badge {{
                align-self: flex-start;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 DeepDive 每日速览</h1>
            <div class="date">AI 资讯精选 · {html.escape(batch_name)}</div>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value">{len(articles)}</div>
                    <div class="stat-label">篇精选资讯</div>
                </div>
            </div>
        </div>

        <div class="articles">
            {cards_html}
        </div>

        <div class="footer">
            <p>由 DeepDive Tracking 自动生成</p>
            <p><a href="index.html">← 返回首页</a></p>
        </div>
    </div>
</body>
</html>"""

    async def _init_repo(self):
        """初始化本地仓库"""
        repo_path = Path(self.local_repo_path)

        if not repo_path.exists():
            # 克隆仓库
            self.logger.info(f"克隆仓库: {self.github_repo}")
            repo_url = f"https://{self.github_username}:{self.github_token}@github.com/{self.github_repo}.git"  # noqa: S105
            await self._run_git_command(
                ["git", "clone", repo_url, str(repo_path)],
                cwd=None
            )

        # 确保目录存在
        (repo_path / self.articles_dir).mkdir(exist_ok=True, parents=True)
        (repo_path / "batches").mkdir(exist_ok=True, parents=True)

    async def _update_index(self):
        """更新索引页面"""
        repo_path = Path(self.local_repo_path)
        articles_dir = repo_path / self.articles_dir
        batches_dir = repo_path / "batches"

        # 收集所有文章
        articles = []
        if articles_dir.exists():
            for html_file in sorted(articles_dir.glob("*.html"), reverse=True)[:20]:
                articles.append({
                    "name": html_file.stem,
                    "file": f"{self.articles_dir}/{html_file.name}",
                    "date": html_file.stat().st_mtime
                })

        # 收集所有批次
        batches = []
        if batches_dir.exists():
            for batch_file in sorted(batches_dir.glob("*.html"), reverse=True)[:10]:
                batches.append({
                    "name": batch_file.stem,
                    "file": f"batches/{batch_file.name}"
                })

        # 生成索引HTML
        articles_html = "".join([
            f'<li><a href="{article["file"]}">{html.escape(article["name"][:50])}</a></li>'
            for article in articles
        ])

        batches_html = "".join([
            f'<li><a href="{batch["file"]}">{html.escape(batch["name"])}</a></li>'
            for batch in batches
        ])

        index_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepDive Tracking - AI资讯精选</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
            padding: 40px 20px;
        }}

        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}

        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .content {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 40px;
        }}

        .section {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}

        .section ul {{
            list-style: none;
        }}

        .section li {{
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }}

        .section li:last-child {{
            border-bottom: none;
        }}

        .section a {{
            color: #667eea;
            text-decoration: none;
            transition: all 0.3s ease;
        }}

        .section a:hover {{
            color: #764ba2;
            text-decoration: underline;
        }}

        .footer {{
            text-align: center;
            color: white;
            padding: 20px;
            opacity: 0.8;
        }}

        @media (max-width: 768px) {{
            .content {{
                grid-template-columns: 1fr;
            }}
            .header h1 {{
                font-size: 2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 DeepDive Tracking</h1>
            <p>AI领域资讯深度追踪与精选</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>📰 最新文章</h2>
                <ul>
                    {articles_html or '<li>暂无文章</li>'}
                </ul>
            </div>

            <div class="section">
                <h2>📅 批次存档</h2>
                <ul>
                    {batches_html or '<li>暂无批次</li>'}
                </ul>
            </div>
        </div>

        <div class="footer">
            <p>由 DeepDive Tracking 自动生成 | 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""

        index_path = repo_path / self.index_file
        index_path.write_text(index_content, encoding='utf-8')
        self.logger.info(f"更新索引: {index_path}")

    async def _commit_and_push(
        self,
        message: str,
        files: Optional[List[str]] = None
    ) -> str:
        """提交和推送到GitHub"""
        repo_path = Path(self.local_repo_path)

        try:
            # 配置git用户信息（必须在commit之前）
            await self._run_git_command(
                ["git", "config", "user.email", "deepdive-tracking@bot.local"],
                cwd=repo_path
            )
            await self._run_git_command(
                ["git", "config", "user.name", "DeepDive Tracking Bot"],
                cwd=repo_path
            )

            # 添加文件
            if files:
                for file in files:
                    await self._run_git_command(["git", "add", file], cwd=repo_path)
            else:
                await self._run_git_command(["git", "add", "-A"], cwd=repo_path)

            # 检查是否有更改
            status = await self._run_git_command(
                ["git", "status", "--porcelain"],
                cwd=repo_path
            )

            if not status.strip():
                self.logger.info("没有变更要提交")
                return ""

            # 提交
            await self._run_git_command(
                ["git", "commit", "-m", message],
                cwd=repo_path
            )

            # 推送
            await self._run_git_command(
                ["git", "push", "origin", "main"],
                cwd=repo_path
            )

            # 获取最新的commit SHA
            commit_sha = await self._run_git_command(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path
            )

            self.logger.info(f"✓ 推送成功: {commit_sha.strip()[:7]}")
            return commit_sha.strip()

        except Exception as e:
            self.logger.error(f"✗ 提交/推送失败: {str(e)}")
            raise

    async def _run_git_command(
        self,
        command: List[str],
        cwd: Optional[Path] = None
    ) -> str:
        """运行git命令"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise Exception(f"Git命令失败: {result.stderr}")

            return result.stdout

        except subprocess.TimeoutExpired:
            raise Exception("Git命令超时")
        except Exception as e:
            raise Exception(f"执行git命令时出错: {str(e)}")
