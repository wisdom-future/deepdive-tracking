#!/usr/bin/env python3
"""
Send TOP news email - Send the highest-scored AI news items by email with bilingual summaries
"""
import sys
import os
import asyncio
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

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
    """Generate clean, mobile-friendly HTML email with actual bilingual summaries"""

    news_items_html = []

    for idx, news in enumerate(news_items, 1):
        if not news.raw_news:
            continue

        # Get both summaries - use them as distinct professional and technical perspectives
        summary_pro = get_summary_with_limit(news.summary_pro or "无摘要", 120)
        summary_sci = get_summary_with_limit(news.summary_sci or "无摘要", 120)

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
    <div style="margin-bottom:3px;"><strong>📌 核心观点：</strong></div>
    <div style="margin-bottom:10px;">{summary_pro}</div>
    <div style="margin-bottom:3px;"><strong>🔬 技术角度：</strong></div>
    <div style="margin-bottom:10px;">{summary_sci}</div>
  </div>

  <div style="display:flex;gap:15px;flex-wrap:wrap;font-size:13px;color:#6b7280;margin-bottom:12px;">
    <div>📂 {category}</div>
    <div>✍️ {author}</div>
  </div>

  <a href="{source_url}" target="_blank" style="display:inline-block;color:{color};text-decoration:none;font-weight:600;border-bottom:1px solid {color};">阅读全文 →</a>
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
    """Send TOP news email"""
    settings = get_settings()

    print("=" * 70)
    print("TOP NEWS EMAIL - Clean Mobile-Friendly Design with Bilingual Content")
    print("=" * 70)

    # Check SMTP configuration
    print("\n1. Checking SMTP configuration...")
    if not settings.smtp_user or not settings.smtp_password:  # noqa: S105
        print("[FAILED] SMTP credentials not configured")
        return False

    print(f"[OK] SMTP Host: {settings.smtp_host}")
    print(f"[OK] SMTP Port: {settings.smtp_port}")
    print(f"[OK] From Email: {settings.smtp_from_email}")

    # Initialize Email Publisher
    print("\n2. Initializing Email Publisher...")
    try:
        publisher = EmailPublisher(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_user=settings.smtp_user,
            smtp_password=settings.smtp_password,  # noqa: S105
            from_email=settings.smtp_from_email,
            from_name=settings.smtp_from_name
        )
        print("[OK] Email publisher initialized successfully")
    except Exception as e:
        print(f"[FAILED] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Fetch TOP news from database
    print("\n3. Fetching TOP news from database...")
    try:
        session = get_session()

        top_news = session.query(ProcessedNews).options(
            joinedload(ProcessedNews.raw_news)
        ).order_by(
            desc(ProcessedNews.score)
        ).limit(10).all()

        session.close()

        if not top_news:
            print("[WARNING] No news found in the database")
            return False

        print(f"[OK] Found {len(top_news)} news items")
        for idx, news in enumerate(top_news, 1):
            title = news.raw_news.title if news.raw_news else "Unknown Title"
            score = news.score or 0
            print(f"    {idx}. {title} (Score: {score})")

    except Exception as e:
        print(f"[FAILED] Database query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Generate and send email
    print("\n4. Generating email with bilingual summaries...")
    recipient_email = settings.smtp_from_email or "hello.junjie.duan@gmail.com"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Generate clean HTML with bilingual content
        html_content = generate_bilingual_email_html(top_news, date_str)

        print(f"[OK] Generated HTML email with {len(top_news)} items")
        print(f"[OK] Recipient: {recipient_email}")

        # Send email
        print("\n5. Sending consolidated email...")
        result = await publisher.publish_article(
            title=f"AI News Daily Digest - {datetime.now().strftime('%Y-%m-%d')} ({len(top_news)} items)",
            content=html_content,
            summary=f"Top {len(top_news)} AI news items with bilingual summaries",
            author="DeepDive Tracking",
            source_url="https://deepdive-tracking.github.io",
            score=0,
            category="Daily Digest",
            email_list=[recipient_email]
        )

        print("\n" + "=" * 70)
        print("EMAIL SENDING COMPLETE")
        print("=" * 70)

        if result and result.get("success"):
            print(f"\n[OK] Successfully sent email with {len(top_news)} items")
            print(f"[OK] Recipient: {recipient_email}")
            print("[OK] Email includes Chinese + English bilingual summaries")
            return True
        else:
            error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else "Unknown error"
            print(f"\n[WARNING] Email send returned: {error_msg}")
            return False

    except Exception as e:
        print(f"[FAILED] Exception during send: {e}")
        import traceback
        traceback.print_exc()
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
