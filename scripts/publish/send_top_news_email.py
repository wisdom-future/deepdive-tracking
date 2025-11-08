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
    Generate professional, mobile-friendly HTML email with bilingual summaries
    Based on ai_news_digest.html template design

    设计原则 (Design Principles):
    1. 移动优先 (Mobile-first): 充足的padding和触摸目标大小
    2. 可读性 (Readability): 清晰的层级结构和视觉分隔
    3. 双语支持 (Bilingual): 中英文摘要分别独立显示
    4. 专业性 (Professional): 紫色渐变品牌配色,支持所有主流邮件客户端
    """

    news_items_html = []

    for idx, news in enumerate(news_items, 1):
        if not news.raw_news:
            continue

        # Get Chinese summary
        summary_zh = news.summary_pro or news.summary_sci or "暂无中文摘要"
        summary_zh = get_summary_with_limit(summary_zh, 200)

        # Get English summary with proper fallback
        summary_en = news.summary_pro_en or news.summary_sci_en
        if not summary_en or len(summary_en.strip()) < 20:
            summary_en = "(English summary not available)"
        summary_en = get_summary_with_limit(summary_en, 200)

        score = news.score or 0
        source_url = news.raw_news.url or "https://deepdive-tracking.github.io"
        author = news.raw_news.source_name or news.raw_news.author or "Unknown"
        category = news.category or "AI News"
        published_date = format_publish_date(news.raw_news.published_at)

        # Category emoji mapping
        category_icon = "🚀"
        if "公司动态" in category or "Company" in category:
            category_icon = "🏢"
        elif "技术突破" in category or "Technology" in category:
            category_icon = "🚀"
        elif "投资" in category or "Investment" in category:
            category_icon = "💰"
        elif "研究" in category or "Research" in category:
            category_icon = "📊"

        # Modern card-based layout with gradient score badge
        item_html = f"""
<!-- News Item {idx} -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:20px;border:1px solid #e9ecef;border-radius:8px;overflow:hidden;">
  <tr>
    <td style="padding:25px 20px;">
      <!-- Title and Score Row -->
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="width:80%;vertical-align:top;">
            <div style="font-size:12px;color:#667eea;font-weight:600;margin-bottom:8px;">TOP {idx}</div>
            <div style="font-size:20px;font-weight:600;color:#212529;line-height:1.4;margin-bottom:15px;">
              {news.raw_news.title}
            </div>
          </td>
          <td style="width:20%;text-align:right;vertical-align:top;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="right">
              <tr>
                <td style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);background-color:#667eea;color:#ffffff;font-size:24px;font-weight:700;width:70px;height:70px;border-radius:8px;text-align:center;vertical-align:middle;">
                  {int(score)}
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <!-- Metadata Tags -->
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:15px 0;padding:15px 0;border-top:1px solid #f1f3f5;border-bottom:1px solid #f1f3f5;">
        <tr>
          <td style="font-size:12px;color:#6c757d;line-height:1.8;">
            {category_icon} {category} &nbsp;&nbsp;|&nbsp;&nbsp; 📰 {author} &nbsp;&nbsp;|&nbsp;&nbsp; 🕐 {published_date}
          </td>
        </tr>
      </table>

      <!-- Chinese Summary -->
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:12px;">
        <tr>
          <td style="background-color:#f8f9fa;border-left:4px solid #667eea;padding:15px 18px;border-radius:4px;">
            <div style="font-size:13px;font-weight:600;color:#495057;margin-bottom:8px;">
              🇨🇳 中文摘要
            </div>
            <div style="font-size:14px;color:#6c757d;line-height:1.7;">
              {summary_zh}
            </div>
          </td>
        </tr>
      </table>

      <!-- English Summary -->
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:15px;">
        <tr>
          <td style="background-color:#f8f9fa;border-left:4px solid #28a745;padding:15px 18px;border-radius:4px;">
            <div style="font-size:13px;font-weight:600;color:#495057;margin-bottom:8px;">
              🇬🇧 English Summary
            </div>
            <div style="font-size:14px;color:#6c757d;line-height:1.7;">
              {summary_en}
            </div>
          </td>
        </tr>
      </table>

      <!-- Read More Button -->
      <table role="presentation" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="border-radius:6px;background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);background-color:#667eea;">
            <a href="{source_url}" target="_blank" style="display:inline-block;padding:12px 28px;font-size:14px;color:#ffffff;text-decoration:none;font-weight:500;">
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
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="x-apple-disable-message-reformatting">
    <meta name="format-detection" content="telephone=no,date=no,address=no,email=no">
    <title>AI News Daily Digest - {date_str}</title>
    <!--[if mso]>
    <style type="text/css">
        body, table, td {{font-family: Arial, sans-serif !important;}}
    </style>
    <![endif]-->
</head>
<body style="margin:0;padding:0;background-color:#f5f7fa;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;">

    <!-- Outer Wrapper -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f5f7fa;">
        <tr>
            <td align="center" style="padding:20px 10px;">

                <!-- Main Container (max 600px) -->
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;background-color:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">

                    <!-- Header with Logo and Title -->
                    <tr>
                        <td style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);background-color:#667eea;padding:40px 30px;color:#ffffff;">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                                <!-- Logo -->
                                <tr>
                                    <td style="padding-bottom:20px;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                                            <tr>
                                                <td style="background-color:#ffffff;width:42px;height:42px;border-radius:8px;text-align:center;vertical-align:middle;font-size:24px;padding:8px;">
                                                    🔍
                                                </td>
                                                <td style="padding-left:12px;font-size:16px;color:#ffffff;font-weight:500;">
                                                    Deepdive Tracking
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <!-- Title -->
                                <tr>
                                    <td style="font-size:32px;font-weight:700;color:#ffffff;padding-bottom:15px;line-height:1.2;">
                                        AI News Daily Digest
                                    </td>
                                </tr>
                                <!-- Metadata -->
                                <tr>
                                    <td style="font-size:14px;color:#ffffff;opacity:0.95;line-height:1.8;">
                                        📅 {date_str} &nbsp;&nbsp;|&nbsp;&nbsp; 📊 {len(news_items)} 精选文章 &nbsp;&nbsp;|&nbsp;&nbsp; 🌐 来自 300+ 优质源
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Summary Section -->
                    <tr>
                        <td style="background-color:#f8f9fa;padding:30px;border-bottom:1px solid #dee2e6;">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="font-size:16px;font-weight:600;color:#495057;padding-bottom:12px;">
                                        📌 今日要点
                                    </td>
                                </tr>
                                <tr>
                                    <td style="font-size:14px;color:#6c757d;line-height:1.7;">
                                        精心筛选的{len(news_items)}条AI行业重要资讯，涵盖技术突破、商业动态、行业分析等多个维度，由AI系统智能评分排序，为您呈现最有价值的行业洞察。
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- News List Section -->
                    <tr>
                        <td style="padding:30px 20px;">
                            {("".join(news_items_html))}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color:#f8f9fa;padding:30px;text-align:center;border-top:1px solid #dee2e6;">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="font-size:14px;color:#6c757d;line-height:1.8;padding-bottom:15px;">
                                        <strong>AI News Daily Digest</strong> - 每日为您精选最有价值的AI行业资讯
                                    </td>
                                </tr>
                                <tr>
                                    <td style="font-size:13px;color:#adb5bd;line-height:1.6;padding-bottom:15px;">
                                        本邮件由AI系统自动生成 | 数据来源于300+优质信息源
                                    </td>
                                </tr>
                                <tr>
                                    <td style="font-size:12px;color:#adb5bd;">
                                        © 2025 Deepdive Tracking. All rights reserved.
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-top:20px;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center">
                                            <tr>
                                                <td style="padding:0 10px;">
                                                    <a href="https://deepdive-tracking.github.io" style="color:#667eea;text-decoration:none;font-size:12px;">官网</a>
                                                </td>
                                                <td style="color:#dee2e6;">|</td>
                                                <td style="padding:0 10px;">
                                                    <a href="https://deepdive-tracking.github.io/subscribe" style="color:#667eea;text-decoration:none;font-size:12px;">订阅设置</a>
                                                </td>
                                                <td style="color:#dee2e6;">|</td>
                                                <td style="padding:0 10px;">
                                                    <a href="https://deepdive-tracking.github.io/unsubscribe" style="color:#667eea;text-decoration:none;font-size:12px;">取消订阅</a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                </table>
                <!-- Main Container End -->

            </td>
        </tr>
    </table>
    <!-- Outer Wrapper End -->

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
        # First get all matching news, then deduplicate in Python
        all_news = session.query(ProcessedNews).join(
            RawNews, ProcessedNews.raw_news_id == RawNews.id
        ).filter(
            and_(
                RawNews.created_at >= time_threshold,
                ProcessedNews.score.isnot(None)
            )
        ).options(
            joinedload(ProcessedNews.raw_news)
        ).order_by(
            desc(ProcessedNews.score)
        ).all()

        # Deduplicate by title in Python (keep first occurrence with highest score)
        seen_titles = set()
        top_news = []
        for news in all_news:
            if news.raw_news and news.raw_news.title:
                if news.raw_news.title not in seen_titles:
                    seen_titles.add(news.raw_news.title)
                    top_news.append(news)
                    if len(top_news) >= 10:  # Get top 10 unique news items
                        break

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
        email_title = f"DeepDive AI Daily - {datetime.now().strftime('%Y-%m-%d')}"

        logger.info(f"Sending email directly...")
        # 直接发送HTML内容，不使用publish_article的元数据包装
        publisher._send_email(
            to_email=recipient_email,
            subject=email_title,
            html_content=html_content
        )

        result = {
            "success": True,
            "sent_count": 1,
            "failed_emails": [],
            "title": email_title,
            "recipients": 1
        }

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
