#!/usr/bin/env python3
"""
Send TOP news email - Send the highest-scored AI news items by email with bilingual summaries

生产级邮件发送脚本 - 完整的错误处理、日志记录和数据验证
"""
import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.services.channels.email.email_publisher import EmailPublisher
from src.config.settings import get_settings
from src.models import ProcessedNews, RawNews
from src.database.connection import get_session
from sqlalchemy import desc, and_
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


def format_publish_date(dt) -> str:
    """Format publish date in user-friendly format"""
    if not dt:
        return "Unknown"

    # Format: 2025-11-04 15:30
    return dt.strftime("%Y-%m-%d %H:%M")


def generate_bilingual_email_html(news_items: list, date_str: str) -> str:
    """
    Generate clean, mobile-friendly HTML email with bilingual summaries

    设计原则 (Design Principles):
    1. 移动优先 (Mobile-first): 充足的padding和触摸目标大小
    2. 可读性 (Readability): 清晰的层级结构和视觉分隔
    3. 双语支持 (Bilingual): 中英文摘要分别独立显示
    4. 专业性 (Professional): 现代化设计,支持所有主流邮件客户端
    """

    news_items_html = []

    for idx, news in enumerate(news_items, 1):
        if not news.raw_news:
            continue

        # Get Chinese summary
        summary_zh = news.summary_pro or news.summary_sci or "暂无中文摘要"
        summary_zh = get_summary_with_limit(summary_zh, 150)

        # Get English summary with proper fallback
        summary_en = news.summary_pro_en or news.summary_sci_en
        if not summary_en or len(summary_en.strip()) < 20:
            summary_en = "(English summary not available)"
        summary_en = get_summary_with_limit(summary_en, 150)

        score = news.score or 0
        source_url = news.raw_news.url or "https://deepdive-tracking.github.io"
        author = news.raw_news.source_name or news.raw_news.author or "Unknown"
        category = news.category or "AI News"
        published_date = format_publish_date(news.raw_news.published_at)

        # Score color
        if score >= 80:
            color = "#10b981"  # Green
        elif score >= 60:
            color = "#3b82f6"  # Blue
        elif score >= 40:
            color = "#f59e0b"  # Orange
        else:
            color = "#ef4444"  # Red

        # Enhanced mobile-friendly layout with proper padding
        item_html = f"""
<table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom:30px;">
  <tr>
    <td style="border-left:5px solid {color};background:#ffffff;padding:25px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
      <!-- Title and Score Row -->
      <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom:18px;">
        <tr>
          <td style="font-size:18px;font-weight:700;color:#1f2937;line-height:1.5;padding-right:15px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
            {idx}. {news.raw_news.title}
          </td>
          <td align="right" valign="top" style="background:{color};color:white;padding:8px 16px;border-radius:6px;font-size:15px;font-weight:700;white-space:nowrap;min-width:60px;">
            {int(score)}
          </td>
        </tr>
      </table>

      <!-- Publish Date and Metadata -->
      <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom:18px;">
        <tr>
          <td style="font-size:13px;color:#6b7280;padding-right:20px;">
            📅 发布时间: {published_date}
          </td>
          <td style="font-size:13px;color:#6b7280;padding-right:20px;">
            📂 {category}
          </td>
          <td style="font-size:13px;color:#6b7280;">
            ✍️ {author}
          </td>
        </tr>
      </table>

      <!-- Summary Section - Chinese -->
      <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom:18px;background:#f8fafc;padding:18px;border-radius:6px;">
        <tr>
          <td style="color:#334155;font-size:14px;line-height:1.7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
            <p style="margin:0 0 10px 0;font-weight:600;color:#0f172a;"><strong>📌 中文摘要:</strong></p>
            <p style="margin:0;color:#475569;">{summary_zh}</p>
          </td>
        </tr>
      </table>

      <!-- Summary Section - English -->
      <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom:20px;background:#f0f9ff;padding:18px;border-radius:6px;">
        <tr>
          <td style="color:#1e3a8a;font-size:14px;line-height:1.7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
            <p style="margin:0 0 10px 0;font-weight:600;color:#1e40af;"><strong>📄 English Summary:</strong></p>
            <p style="margin:0;color:#1e40af;">{summary_en}</p>
          </td>
        </tr>
      </table>

      <!-- Read More Link -->
      <table width="100%" border="0" cellspacing="0" cellpadding="0">
        <tr>
          <td align="center" style="padding:15px 0 0 0;">
            <a href="{source_url}" target="_blank" style="display:inline-block;background:{color};color:white;padding:12px 30px;border-radius:6px;text-decoration:none;font-weight:600;font-size:14px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
              阅读原文 / Read Full Article →
            </a>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
"""
        news_items_html.append(item_html)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="x-apple-disable-message-reformatting">
    <meta name="format-detection" content="telephone=no,date=no,address=no,email=no">
    <title>AI News Digest - {date_str}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f3f4f6;
            padding: 0;
            margin: 0;
            min-height: 100vh;
        }}

        /* Mobile optimization */
        @media (max-width: 600px) {{
            body {{
                padding: 0 !important;
            }}

            table[width="600"] {{
                width: 100% !important;
                min-width: 320px !important;
            }}

            td {{
                padding: 15px !important;
            }}

            h1 {{
                font-size: 22px !important;
            }}

            p {{
                font-size: 14px !important;
            }}
        }}

        /* Dark mode support */
        @media (prefers-color-scheme: dark) {{
            body {{
                background: #1f2937 !important;
            }}
        }}
    </style>
</head>
<body>
    <div style="width:100%;background:#f3f4f6;padding:20px 10px;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background:#f3f4f6;">
            <tr>
                <td align="center" style="padding:0;">
                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="max-width:100%;background:#ffffff;border-collapse:collapse;border-radius:12px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background:linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);color:white;padding:40px 30px;text-align:center;">
                                <h1 style="font-size:28px;font-weight:800;margin:0 0 15px 0;line-height:1.3;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">📰 AI News Daily Digest</h1>
                                <p style="font-size:15px;opacity:0.95;margin:0;line-height:1.5;font-weight:500;">
                                    发布时间: {date_str} | 共 {len(news_items)} 条精选 | 来自300+优质源
                                </p>
                                <p style="font-size:14px;opacity:0.9;margin:10px 0 0 0;line-height:1.5;">
                                    Published: {date_str} | {len(news_items)} Selected Items | From 300+ Sources
                                </p>
                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td style="padding:30px;background:#f8fafc;">
                                {("".join(news_items_html))}
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="border-top:2px solid #e5e7eb;background:#ffffff;padding:30px;text-align:center;font-size:13px;color:#6b7280;">
                                <p style="margin:0 0 8px 0;line-height:1.6;font-weight:500;color:#374151;">由 <strong style="color:#1e3a8a;">DeepDive Tracking</strong> 提供 - AI资讯智能平台</p>
                                <p style="margin:0 0 8px 0;line-height:1.6;">Generated by <strong>DeepDive Tracking</strong> - AI News Intelligence Platform</p>
                                <p style="margin:0;line-height:1.6;color:#9ca3af;">© 2025 DeepDive Tracking. All rights reserved.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
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

    # Step 3: Fetch TOP news from database (last 24 hours only)
    logger.info("Step 3: Fetching TOP 10 news items from last 24 hours...")
    print("\nStep 3: Fetching TOP 10 news items (last 24 hours)...")

    session = None
    try:
        session = get_session()

        # Calculate 24 hours ago
        time_threshold = datetime.now() - timedelta(hours=24)
        logger.info(f"  Time threshold: {time_threshold.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Time threshold: {time_threshold.strftime('%Y-%m-%d %H:%M:%S')}")

        # Query TOP news from last 24 hours
        # Join with RawNews to filter by published_at and collected_at
        top_news = session.query(ProcessedNews).join(
            RawNews, ProcessedNews.raw_news_id == RawNews.id
        ).filter(
            and_(
                # Either published_at or collected_at within last 24 hours
                # (some sources may not have accurate published_at)
                RawNews.collected_at >= time_threshold,
                ProcessedNews.score.isnot(None)
            )
        ).options(
            joinedload(ProcessedNews.raw_news)
        ).order_by(
            desc(ProcessedNews.score)
        ).limit(15).all()  # Get top 15 to have more selection

        if not top_news:
            logger.warning("No processed news found in database")
            print("  WARNING: No news items found in database")
            return False

        logger.info(f"Retrieved {len(top_news)} top news items")
        print(f"  Found {len(top_news)} items:")

        for idx, news in enumerate(top_news, 1):
            title = news.raw_news.title if news.raw_news else "Unknown"
            score = news.score or 0
            published = format_publish_date(news.raw_news.published_at) if news.raw_news else "Unknown"

            logger.info(f"  [{idx}] {title} (Score: {score}, Published: {published})")
            print(f"    [{idx}] Score:{score:3.0f} | {published} | {title[:50]}")

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
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

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
            summary_en=f"Top {len(top_news)} AI news items - carefully curated and scored by our AI system",
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
