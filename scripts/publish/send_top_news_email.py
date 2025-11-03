#!/usr/bin/env python3
"""
Send TOP news email - Send the highest-scored AI news items by email with bilingual summaries

生产级邮件发送脚本 - 完整的错误处理、日志记录和数据验证
"""
import sys
import os
import asyncio
import logging
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.services.channels.email.email_publisher import EmailPublisher
from src.config.settings import get_settings
from src.models import ProcessedNews
from src.database.connection import get_session
from sqlalchemy import desc
from sqlalchemy.orm import joinedload


def get_summary_with_limit(text: str, max_length: int = 100) -> str:
    """Truncate text to word boundary"""
    if not text or len(text) <= max_length:
        return text

    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.7:  # Make sure we remove meaningful amount
        return truncated[:last_space] + "..."
    return truncated + "..."


def generate_bilingual_email_html(news_items: list, date_str: str) -> str:
    """Generate clean, mobile-friendly HTML email with bilingual summaries from AI"""

    news_items_html = []

    for idx, news in enumerate(news_items, 1):
        if not news.raw_news:
            continue

        # Get summaries directly from database (AI already generated both Chinese and English)
        summary_zh = get_summary_with_limit(news.summary_pro or news.summary_sci or "无摘要", 120)
        summary_en = get_summary_with_limit(news.summary_pro_en or news.summary_sci_en or "No summary available", 120)

        score = news.score or 0
        source_url = news.raw_news.url or "https://deepdive-tracking.github.io"
        author = news.raw_news.source_name or news.raw_news.author or "Unknown"
        category = news.category or "AI News"

        # Score color
        if score >= 80:
            color = "#10b981"
        elif score >= 60:
            color = "#3b82f6"
        elif score >= 40:
            color = "#f59e0b"
        else:
            color = "#ef4444"

        item_html = f"""
<div style="margin-bottom:25px;padding:20px;border-left:4px solid {color};background:#f9fafb;border-radius:4px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;gap:10px;">
    <h3 style="margin:0;font-size:16px;font-weight:600;color:#1f2937;flex:1;line-height:1.5;">{idx}. {news.raw_news.title}</h3>
    <span style="display:inline-block;background:{color};color:white;padding:5px 12px;border-radius:4px;font-size:13px;font-weight:600;white-space:nowrap;">{int(score)}</span>
  </div>

  <div style="margin-bottom:10px;color:#4b5563;font-size:14px;line-height:1.6;">
    <div style="margin-bottom:3px;"><strong>📌 摘要（中文）:</strong></div>
    <div style="margin-bottom:10px;">{summary_zh}</div>
    <div style="margin-bottom:3px;"><strong>📄 Summary (English):</strong></div>
    <div style="margin-bottom:10px;">{summary_en}</div>
  </div>

  <div style="display:flex;gap:15px;flex-wrap:wrap;font-size:13px;color:#6b7280;margin-bottom:12px;">
    <div>📂 {category}</div>
    <div>✍️ {author}</div>
  </div>

  <a href="{source_url}" target="_blank" style="display:inline-block;color:{color};text-decoration:none;font-weight:600;border-bottom:1px solid {color};">阅读全文 / Read More →</a>
</div>
"""
        news_items_html.append(item_html)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Digest - {date_str}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #ffffff;
            padding: 0;
        }}

        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
            color: white;
            padding: 30px 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 10px;
        }}

        .header-info {{
            font-size: 13px;
            opacity: 0.9;
        }}

        .news-item {{
            margin-bottom: 30px;
            padding: 20px;
            border-left: 4px solid #3b82f6;
            background: #f9fafb;
            border-radius: 4px;
        }}

        .footer {{
            text-align: center;
            padding-top: 20px;
            margin-top: 30px;
            border-top: 1px solid #e5e7eb;
            font-size: 12px;
            color: #6b7280;
        }}

        @media (max-width: 480px) {{
            .container {{
                padding: 10px;
            }}

            .header {{
                padding: 20px 15px;
            }}

            .header h1 {{
                font-size: 20px;
            }}

            .news-item {{
                padding: 15px;
                margin-bottom: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 AI News Daily Digest</h1>
            <div class="header-info">
                Published: {date_str} | Total: {len(news_items)} items | Curated from 300+ sources
            </div>
        </div>

        {"".join(news_items_html)}

        <div class="footer">
            <p>Generated by <strong>DeepDive Tracking</strong> - AI News Intelligence Platform</p>
            <p>© 2025 DeepDive Tracking. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""

    return html_content


async def main():
    """Send TOP news email - Production-grade implementation"""
    logger.info("Starting email send workflow...")
    settings = get_settings()

    print("\n" + "=" * 80)
    print("DEEPDIVE TRACKING - PRODUCTION EMAIL SERVICE")
    print("=" * 80)

    # Step 1: Validate SMTP configuration
    logger.info("Step 1: Validating SMTP configuration...")
    print("\nStep 1: Validating SMTP configuration...")

    if not settings.smtp_host:
        logger.error("SMTP_HOST not configured")
        print("ERROR: SMTP_HOST not configured")
        return False

    if not settings.smtp_user or not settings.smtp_password:  # noqa: S105
        logger.error("SMTP authentication config missing")
        print("ERROR: SMTP credentials not configured")
        return False

    logger.info(f"SMTP config OK - Host: {settings.smtp_host}, Port: {settings.smtp_port}")
    print(f"  SMTP Host: {settings.smtp_host}")
    print(f"  SMTP Port: {settings.smtp_port}")
    print(f"  From Email: {settings.smtp_from_email}")
    print("  Status: PASS")

    # Step 2: Initialize EmailPublisher
    logger.info("Step 2: Initializing EmailPublisher...")
    print("\nStep 2: Initializing EmailPublisher...")

    try:
        publisher = EmailPublisher(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_user=settings.smtp_user,
            smtp_password=settings.smtp_password,  # noqa: S105
            from_email=settings.smtp_from_email,
            from_name=settings.smtp_from_name
        )
        logger.info("EmailPublisher initialized successfully")
        print("  Status: PASS")
    except Exception as e:
        logger.error(f"Failed to initialize EmailPublisher: {e}", exc_info=True)
        print(f"  ERROR: {e}")
        return False

    # Step 3: Fetch TOP news from database
    logger.info("Step 3: Fetching TOP 10 news items from database...")
    print("\nStep 3: Fetching TOP 10 news items...")

    session = None
    try:
        session = get_session()

        top_news = session.query(ProcessedNews).options(
            joinedload(ProcessedNews.raw_news)
        ).order_by(
            desc(ProcessedNews.score)
        ).limit(10).all()

        if not top_news:
            logger.warning("No processed news found in database")
            print("  WARNING: No news items found in database")
            return False

        logger.info(f"Retrieved {len(top_news)} top news items")
        print(f"  Found {len(top_news)} items:")

        for idx, news in enumerate(top_news, 1):
            title = news.raw_news.title if news.raw_news else "Unknown"
            score = news.score or 0
            summary_zh = news.summary_pro or news.summary_sci or "N/A"
            summary_en = news.summary_pro_en or news.summary_sci_en or "N/A"

            logger.info(f"  [{idx}] {title} (Score: {score})")
            logger.debug(f"      Chinese: {summary_zh[:50]}...")
            logger.debug(f"      English: {summary_en[:50]}...")
            print(f"    [{idx}] Score:{score:3.0f} | {title[:60]}")

        print("  Status: PASS")

    except Exception as e:
        logger.error(f"Database query failed: {e}", exc_info=True)
        print(f"  ERROR: Database query failed - {e}")
        return False
    finally:
        if session:
            session.close()
            logger.debug("Database session closed")

    # Step 4: Generate email HTML
    logger.info("Step 4: Generating bilingual email HTML...")
    print("\nStep 4: Generating email HTML...")

    try:
        recipient_email = settings.smtp_from_email or "hello.junjie.duan@gmail.com"
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html_content = generate_bilingual_email_html(top_news, date_str)
        html_size = len(html_content)

        logger.info(f"Generated HTML email ({html_size} bytes) with {len(top_news)} news items")
        print(f"  Generated HTML ({html_size} bytes)")
        print(f"  Recipient: {recipient_email}")
        print("  Status: PASS")

    except Exception as e:
        logger.error(f"Failed to generate email HTML: {e}", exc_info=True)
        print(f"  ERROR: {e}")
        return False

    # Step 5: Send email via SMTP
    logger.info("Step 5: Sending email via SMTP...")
    print("\nStep 5: Sending email via SMTP...")

    try:
        email_title = f"AI News Daily Digest - {datetime.now().strftime('%Y-%m-%d')} ({len(top_news)} items)"

        logger.info(f"Calling EmailPublisher.publish_article()...")
        result = await publisher.publish_article(
            title=email_title,
            content=html_content,
            summary=f"Top {len(top_news)} AI news items with Chinese and English bilingual summaries",
            author="DeepDive Tracking",
            source_url="https://deepdive-tracking.github.io",
            score=0,
            category="Daily Digest",
            email_list=[recipient_email]
        )

        logger.info(f"Email send result: {result}")

        if result and result.get("success"):
            sent_count = result.get("sent_count", 0)
            logger.info(f"Email sent successfully to {sent_count} recipient(s)")
            print(f"  Email sent successfully!")
            print(f"  Recipient: {recipient_email}")
            print(f"  Items: {len(top_news)}")
            print("  Status: PASS")

            print("\n" + "=" * 80)
            print("EMAIL SEND WORKFLOW COMPLETED SUCCESSFULLY")
            print("=" * 80)
            return True
        else:
            error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else "Unknown error"
            failed_emails = result.get("failed_emails", []) if isinstance(result, dict) else []

            logger.error(f"Email send failed: {error_msg}")
            logger.error(f"Failed recipients: {failed_emails}")

            print(f"  ERROR: Email send failed")
            print(f"  Error: {error_msg}")
            print(f"  Failed recipients: {failed_emails}")
            print("  Status: FAIL")
            return False

    except Exception as e:
        logger.error(f"Exception during email send: {e}", exc_info=True)
        print(f"  ERROR: {e}")
        print("  Status: FAIL")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
