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

        # Get English summary from database with strict validation
        summary_en = news.summary_pro_en or news.summary_sci_en

        # Validate English summary - must be meaningful and not an error message
        if not summary_en or len(summary_en.strip()) < 20:
            # If English summary is missing or too short, use Chinese as fallback
            summary_en = summary_zh

        summary_en = get_summary_with_limit(summary_en, 120)

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

        # Table-based layout for better email client compatibility
        item_html = f"""
<table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom:25px;">
  <tr>
    <td style="border-left:4px solid {color};background:#f9fafb;padding:20px;">
      <!-- Title and Score Row -->
      <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom:15px;">
        <tr>
          <td style="font-size:16px;font-weight:600;color:#1f2937;line-height:1.5;padding-right:15px;">
            {idx}. {news.raw_news.title}
          </td>
          <td align="right" valign="top" style="background:{color};color:white;padding:5px 12px;border-radius:4px;font-size:13px;font-weight:600;white-space:nowrap;width:50px;">
            {int(score)}
          </td>
        </tr>
      </table>

      <!-- Summary Section -->
      <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom:15px;">
        <tr>
          <td style="color:#4b5563;font-size:14px;line-height:1.6;">
            <p style="margin:0 0 8px 0;"><strong>📌 摘要（中文）:</strong></p>
            <p style="margin:0 0 15px 0;">{summary_zh}</p>
            <p style="margin:0 0 8px 0;"><strong>📄 Summary (English):</strong></p>
            <p style="margin:0;">{summary_en}</p>
          </td>
        </tr>
      </table>

      <!-- Category and Author Row -->
      <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom:15px;">
        <tr>
          <td style="font-size:13px;color:#6b7280;padding-right:20px;">
            📂 {category}
          </td>
          <td style="font-size:13px;color:#6b7280;">
            ✍️ {author}
          </td>
        </tr>
      </table>

      <!-- Read More Link -->
      <table width="100%" border="0" cellspacing="0" cellpadding="0">
        <tr>
          <td>
            <a href="{source_url}" target="_blank" style="color:{color};text-decoration:none;font-weight:600;border-bottom:1px solid {color};display:inline-block;">
              阅读全文 / Read More →
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f3f4f6;
            padding: 0;
            min-height: 100vh;
        }}

        .wrapper {{
            width: 100%;
            background: #f3f4f6;
            padding: 20px 0;
        }}

        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: #ffffff;
            width: 100%;
        }}

        .header {{
            background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 10px;
            line-height: 1.3;
        }}

        .header-info {{
            font-size: 13px;
            opacity: 0.9;
            line-height: 1.4;
        }}

        .content {{
            padding: 20px;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 12px;
            color: #6b7280;
            background: #f9fafb;
        }}

        .footer p {{
            margin: 5px 0;
            line-height: 1.5;
        }}

        /* Mobile optimization */
        @media (max-width: 600px) {{
            .wrapper {{
                padding: 10px 0;
            }}

            .header {{
                padding: 20px 15px;
            }}

            .header h1 {{
                font-size: 20px;
            }}

            .content {{
                padding: 15px;
            }}

            .footer {{
                padding: 15px;
                font-size: 11px;
            }}

            table[width="100%"] {{
                width: 100% !important;
            }}

            td {{
                display: block;
                width: 100% !important;
                text-align: left !important;
                padding: 10px 0 !important;
            }}

            .title-row td:last-child {{
                text-align: right !important;
                padding: 0 !important;
                width: auto !important;
            }}
        }}

        /* iPad/Tablet optimization */
        @media (min-width: 601px) and (max-width: 900px) {{
            .container {{
                max-width: 95%;
            }}

            .header {{
                padding: 25px 20px;
            }}

            .header h1 {{
                font-size: 22px;
            }}
        }}
    </style>
</head>
<body>
    <div class="wrapper">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background:#f3f4f6;">
            <tr>
                <td align="center" style="padding:20px 0;">
                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="max-width:100%;background:#ffffff;border-collapse:collapse;">
                        <!-- Header -->
                        <tr>
                            <td style="background:linear-gradient(135deg, #1f2937 0%, #374151 100%);color:white;padding:30px 20px;text-align:center;">
                                <h1 style="font-size:24px;font-weight:700;margin:0 0 10px 0;line-height:1.3;">📰 AI News Daily Digest</h1>
                                <p style="font-size:13px;opacity:0.9;margin:0;line-height:1.4;">
                                    Published: {date_str} | Total: {len(news_items)} items | Curated from 300+ sources
                                </p>
                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td style="padding:20px;">
                                {("".join(news_items_html))}
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="border-top:1px solid #e5e7eb;background:#f9fafb;padding:20px;text-align:center;font-size:12px;color:#6b7280;">
                                <p style="margin:0 0 5px 0;line-height:1.5;">Generated by <strong>DeepDive Tracking</strong> - AI News Intelligence Platform</p>
                                <p style="margin:0;line-height:1.5;">© 2025 DeepDive Tracking. All rights reserved.</p>
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
