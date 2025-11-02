"""
邮件发布渠道 - 发送文章到邮件列表

支持功能：
- 发送单篇文章到邮件列表
- 批量发送文章
- 管理邮件列表
- 美化的HTML邮件格式
"""

import logging
import smtplib
from typing import Dict, List, Optional, Any
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import html
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class EmailPublisher:
    """邮件发布器"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        from_name: str = "DeepDive Tracking",
        email_list: Optional[List[str]] = None
    ):
        """
        初始化邮件发布器

        Args:
            smtp_host: SMTP服务器地址
            smtp_port: SMTP服务器端口
            smtp_user: SMTP用户名
            smtp_password: SMTP密码
            from_email: 发件邮箱
            from_name: 发件人名称
            email_list: 默认邮件列表
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.from_name = from_name
        self.email_list = email_list or ["hello.junjie.duan@gmail.com"]
        self.logger = logger

    def add_email(self, email: str) -> bool:
        """
        添加邮箱到列表

        Args:
            email: 邮箱地址

        Returns:
            bool: 是否添加成功
        """
        if email not in self.email_list:
            self.email_list.append(email)
            self.logger.info(f"✓ 添加邮箱: {email}")
            return True
        self.logger.warning(f"邮箱已存在: {email}")
        return False

    def remove_email(self, email: str) -> bool:
        """
        从列表移除邮箱

        Args:
            email: 邮箱地址

        Returns:
            bool: 是否移除成功
        """
        if email in self.email_list:
            self.email_list.remove(email)
            self.logger.info(f"✓ 移除邮箱: {email}")
            return True
        self.logger.warning(f"邮箱不存在: {email}")
        return False

    def get_email_list(self) -> List[str]:
        """获取邮件列表"""
        return self.email_list.copy()

    def set_email_list(self, emails: List[str]):
        """设置邮件列表"""
        self.email_list = emails
        self.logger.info(f"✓ 邮件列表已更新: {len(emails)} 个邮箱")

    async def publish_article(
        self,
        title: str,
        content: str,
        summary: str,
        author: str,
        source_url: str,
        score: float,
        category: str,
        email_list: Optional[List[str]] = None,
        article_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        发送单篇文章到邮件列表

        Args:
            title: 文章标题
            content: 文章内容（HTML格式）
            summary: 摘要
            author: 作者
            source_url: 源URL
            score: 评分 (0-100)
            category: 分类
            email_list: 邮件列表（如为None则使用默认列表）
            article_id: 文章ID

        Returns:
            {
                "success": bool,
                "sent_count": int,
                "failed_emails": [...],
                "error": str (if failed)
            }
        """
        try:
            recipients = email_list or self.email_list
            if not recipients:
                return {
                    "success": False,
                    "sent_count": 0,
                    "failed_emails": [],
                    "error": "No recipients configured"
                }

            # 生成邮件HTML
            email_html = self._generate_email_html(
                title=title,
                content=content,
                summary=summary,
                author=author,
                source_url=source_url,
                score=score,
                category=category,
                publish_date=datetime.now()
            )

            # 发送邮件
            failed_emails = []
            sent_count = 0

            for recipient in recipients:
                try:
                    self._send_email(
                        to_email=recipient,
                        subject=f"[{category}] {title}",
                        html_content=email_html
                    )
                    sent_count += 1
                    self.logger.info(f"✓ 邮件已发送: {recipient}")
                except Exception as e:
                    failed_emails.append(recipient)
                    self.logger.error(f"✗ 发送失败 {recipient}: {str(e)}")

            return {
                "success": len(failed_emails) == 0,
                "sent_count": sent_count,
                "failed_emails": failed_emails,
                "title": title,
                "recipients": len(recipients)
            }

        except Exception as e:
            self.logger.error(f"✗ 发送文章失败: {str(e)}")
            return {
                "success": False,
                "sent_count": 0,
                "failed_emails": recipients or [],
                "error": str(e)
            }

    async def publish_batch_articles(
        self,
        articles: List[Dict[str, Any]],
        batch_name: Optional[str] = None,
        email_list: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        批量发送文章到邮件列表

        Args:
            articles: 文章列表，每个包含 title, content, summary, author, source_url, score, category
            batch_name: 批次名称
            email_list: 邮件列表（如为None则使用默认列表）

        Returns:
            {
                "success": bool,
                "published_count": int,
                "failed_count": int,
                "sent_emails": int,
                "failed_emails": [...]
            }
        """
        batch_name = batch_name or datetime.now().strftime("%Y-%m-%d")
        recipients = email_list or self.email_list
        published_count = 0
        failed_count = 0
        failed_emails = []

        try:
            if not recipients:
                return {
                    "success": False,
                    "published_count": 0,
                    "failed_count": len(articles),
                    "error": "No recipients configured"
                }

            self.logger.info(f"开始批量发送 {len(articles)} 篇文章到 {len(recipients)} 个邮箱...")

            # 生成汇总邮件
            batch_html = self._generate_batch_email_html(articles, batch_name)

            # 发送汇总邮件
            for recipient in recipients:
                try:
                    self._send_email(
                        to_email=recipient,
                        subject=f"DeepDive Daily Report - {batch_name} ({len(articles)} articles)",
                        html_content=batch_html
                    )
                    published_count += 1
                except Exception as e:
                    failed_count += 1
                    failed_emails.append(recipient)
                    self.logger.error(f"✗ 发送失败 {recipient}: {str(e)}")

            self.logger.info(f"批量发送完成: {published_count} 成功, {failed_count} 失败")

            return {
                "success": failed_count == 0,
                "published_count": len(articles),
                "sent_emails": published_count,
                "failed_emails": failed_emails,
                "batch_name": batch_name,
                "message": f"Sent batch to {published_count} recipients"
            }

        except Exception as e:
            self.logger.error(f"✗ 批量发送失败: {str(e)}")
            return {
                "success": False,
                "published_count": 0,
                "sent_emails": 0,
                "failed_emails": recipients,
                "error": str(e)
            }

    def _generate_email_html(
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
        """生成邮件HTML"""
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
            background: #f5f5f5;
            padding: 20px 0;
        }}

        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 1.8em;
            margin-bottom: 15px;
            word-break: break-word;
        }}

        .meta {{
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            font-size: 0.9em;
            opacity: 0.9;
            padding: 15px 0 0 0;
            border-top: 1px solid rgba(255,255,255,0.3);
        }}

        .meta-item {{
            text-align: center;
        }}

        .meta-label {{
            font-size: 0.8em;
            opacity: 0.8;
            display: block;
        }}

        .meta-value {{
            font-weight: bold;
            display: block;
        }}

        .score {{
            font-size: 1.1em;
        }}

        .content-wrapper {{
            padding: 30px 20px;
        }}

        .summary {{
            background: #e7f3ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}

        .summary-title {{
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
            font-size: 0.95em;
        }}

        .article-content {{
            line-height: 1.8;
            color: #444;
            font-size: 0.95em;
        }}

        .article-content p {{
            margin-bottom: 15px;
        }}

        .article-content h2 {{
            font-size: 1.3em;
            margin: 25px 0 15px 0;
            color: #667eea;
        }}

        .article-content h3 {{
            font-size: 1.1em;
            margin: 20px 0 10px 0;
            color: #764ba2;
        }}

        .article-content a {{
            color: #667eea;
            text-decoration: none;
        }}

        .article-content a:hover {{
            text-decoration: underline;
        }}

        .source {{
            background: #f0f8ff;
            border: 1px solid #b3d9ff;
            padding: 12px 15px;
            border-radius: 4px;
            margin: 20px 0 0 0;
            font-size: 0.9em;
        }}

        .source-title {{
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }}

        .source-link {{
            word-break: break-all;
            color: #667eea;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-top: 1px solid #e9ecef;
            font-size: 0.85em;
            color: #6c757d;
            text-align: center;
        }}

        .button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            text-decoration: none;
            margin-top: 15px;
            font-size: 0.9em;
        }}

        .button:hover {{
            opacity: 0.9;
        }}

        @media (max-width: 600px) {{
            .meta {{
                font-size: 0.8em;
                gap: 10px;
            }}
            .header h1 {{
                font-size: 1.4em;
            }}
            .content-wrapper {{
                padding: 20px 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{html.escape(title)}</h1>
            <div class="meta">
                <div class="meta-item">
                    <span class="meta-label">评分</span>
                    <span class="meta-value score">{score_level} {score}/100</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">分类</span>
                    <span class="meta-value">{html.escape(category)}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">作者</span>
                    <span class="meta-value">{html.escape(author)}</span>
                </div>
            </div>
        </div>

        <div class="content-wrapper">
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

            <center>
                <a href="{html.escape(source_url)}" class="button">查看原文</a>
            </center>
        </div>

        <div class="footer">
            <p>由 DeepDive Tracking 生成 | {publish_date.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="margin-top: 10px; font-size: 0.8em; opacity: 0.8;">AI领域资讯深度追踪与精选</p>
        </div>
    </div>
</body>
</html>"""

    def _generate_batch_email_html(self, articles: List[Dict[str, Any]], batch_name: str) -> str:
        """生成批量邮件HTML"""
        articles_html = "".join([
            f"""
            <div class="article-card">
                <h3>{html.escape(article.get('title', 'Untitled')[:60])}</h3>
                <div class="article-meta">
                    <span class="badge category">{html.escape(article.get('category', 'Unknown'))}</span>
                    <span class="score">{article.get('score', 0)}/100</span>
                </div>
                <p class="summary">{html.escape(article.get('summary', '')[:150])}...</p>
                <a href="{html.escape(article.get('source_url', '#'))}" class="read-more">Read More →</a>
            </div>
            """
            for article in articles
        ])

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepDive Daily Report - {html.escape(batch_name)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
            background: #f5f5f5;
            padding: 20px 0;
        }}

        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 0.95em;
        }}

        .content-wrapper {{
            padding: 30px 20px;
        }}

        .article-card {{
            padding: 20px;
            margin-bottom: 20px;
            background: #f9f9f9;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }}

        .article-card:last-child {{
            margin-bottom: 0;
        }}

        .article-card h3 {{
            margin-bottom: 10px;
            color: #333;
            font-size: 1.1em;
        }}

        .article-meta {{
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
            font-size: 0.85em;
        }}

        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            background: #e3f2fd;
            color: #667eea;
            font-weight: 500;
        }}

        .score {{
            color: #ffc107;
            font-weight: bold;
        }}

        .summary {{
            color: #666;
            font-size: 0.9em;
            line-height: 1.6;
            margin-bottom: 10px;
        }}

        .read-more {{
            color: #667eea;
            text-decoration: none;
            font-size: 0.9em;
            font-weight: 500;
        }}

        .read-more:hover {{
            text-decoration: underline;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 20px;
            border-top: 1px solid #e9ecef;
            font-size: 0.85em;
            color: #6c757d;
            text-align: center;
        }}

        .stats {{
            background: #e7f3ff;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
            margin-bottom: 20px;
        }}

        .stats p {{
            margin: 5px 0;
            color: #667eea;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 DeepDive Daily Report</h1>
            <p>{html.escape(batch_name)}</p>
        </div>

        <div class="content-wrapper">
            <div class="stats">
                <p>📰 今日精选 {len(articles)} 篇优质AI资讯</p>
                <p style="font-size: 0.9em; opacity: 0.8;">精选自300+ 数据源，AI智能评分</p>
            </div>

            {articles_html}
        </div>

        <div class="footer">
            <p>DeepDive Tracking - AI领域资讯深度追踪与精选</p>
            <p style="margin-top: 10px; opacity: 0.7;">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""

    def _send_email(self, to_email: str, subject: str, html_content: str):
        """
        发送邮件

        Args:
            to_email: 收件人
            subject: 邮件主题
            html_content: HTML内容
        """
        try:
            # 创建邮件
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to_email

            # 添加HTML部分
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(html_part)

            # 发送邮件
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                # 升级到TLS
                if self.smtp_port == 587:
                    server.starttls()

                # 登录
                server.login(self.smtp_user, self.smtp_password)

                # 发送
                server.send_message(message)

            self.logger.debug(f"邮件已发送到: {to_email}")

        except Exception as e:
            self.logger.error(f"发送邮件失败: {str(e)}")
            raise
