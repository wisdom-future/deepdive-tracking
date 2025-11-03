#!/usr/bin/env python3
"""
Send TOP news email - Send the highest-scored AI news items by email
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.channels.email.email_publisher import EmailPublisher
from src.config.settings import get_settings
from src.models import ProcessedNews, RawNews
from sqlalchemy import desc
from sqlalchemy.orm import joinedload


async def main():
    """Send TOP news email"""
    settings = get_settings()

    print("=" * 70)
    print("TOP NEWS EMAIL - Send Highest-Scored Articles")
    print("=" * 70)

    # Check SMTP configuration
    print("\n1. Checking SMTP configuration...")
    # Check SMTP configuration (from env vars, not hardcoded)
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
        from src.database.connection import get_session
        session = get_session()

        # Get top 10 news items by score with eager loading of raw_news relationship
        top_news = session.query(ProcessedNews).options(
            joinedload(ProcessedNews.raw_news)
        ).order_by(
            desc(ProcessedNews.score)
        ).limit(10).all()

        session.close()

        if not top_news:
            print("[WARNING] No news found in the database")
            print("Please run news collection first: python scripts/01-collection/collect_news.py")
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

    # Send TOP news email (all content in one email)
    print("\n4. Sending TOP news email (all content in one email)...")
    recipient_email = settings.smtp_from_email or "hello.junjie.duan@gmail.com"
    print(f"    Recipient: {recipient_email}")

    try:
        # Build combined email content with all news items
        email_content_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '<meta charset="UTF-8">',
            "<style>",
            "body { font-family: Arial, sans-serif; color: #333; }",
            "h1 { color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 10px; }",
            ".news-item { margin: 20px 0; padding: 15px; border-left: 4px solid #1a73e8; background: #f9f9f9; }",
            ".news-title { font-size: 18px; font-weight: bold; color: #1a73e8; margin-bottom: 8px; }",
            ".news-score { display: inline-block; background: #4285f4; color: white; padding: 5px 10px; border-radius: 3px; margin-bottom: 10px; font-weight: bold; }",
            ".news-summary { margin: 10px 0; line-height: 1.6; }",
            ".news-meta { color: #666; font-size: 12px; margin-top: 10px; }",
            ".news-link { color: #1a73e8; text-decoration: none; }",
            ".news-link:hover { text-decoration: underline; }",
            ".footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>📰 AI News Daily Digest - {datetime.now().strftime('%Y-%m-%d')}</h1>",
            f"<p>Here are the top {len(top_news)} AI news items for today:</p>"
        ]

        # Add all news items to the email content
        for idx, news in enumerate(top_news, 1):
            if not news.raw_news:
                continue

            summary = news.summary_pro or news.summary_sci or "No summary available"
            source_url = news.raw_news.url or "https://deepdive-tracking.github.io"
            author = news.raw_news.source_name or news.raw_news.author or "Unknown Source"
            score = news.score or 0

            email_content_lines.extend([
                '<div class="news-item">',
                f'<div class="news-title">{idx}. {news.raw_news.title}</div>',
                f'<div class="news-score">Score: {score}/100</div>',
                f'<div class="news-summary">{summary}</div>',
                '<div class="news-meta">',
                f'📌 Category: {news.category or "AI News"} | ',
                f'📝 Source: {author} | ',
                f'🔗 <a class="news-link" href="{source_url}" target="_blank">Read full article</a>',
                '</div>',
                '</div>'
            ])

        # Add footer
        email_content_lines.extend([
            '<div class="footer">',
            '<p>This is an automated email from DeepDive Tracking AI News Platform.</p>',
            '<p><a class="news-link" href="https://deepdive-tracking.github.io">View all news online</a></p>',
            '</div>',
            '</body>',
            '</html>'
        ])

        html_content = "\n".join(email_content_lines)

        # Send the combined email
        result = await publisher.publish_article(
            title=f"AI News Daily Digest - {datetime.now().strftime('%Y-%m-%d')} ({len(top_news)} items)",
            content=html_content,
            summary=f"Today's top {len(top_news)} AI news items",
            author="DeepDive Tracking",
            source_url="https://deepdive-tracking.github.io",
            score=0,
            category="Daily Digest",
            email_list=[recipient_email],
            is_html=True
        )

        print("\n" + "=" * 70)
        print("TOP NEWS EMAIL SENDING COMPLETE")
        print("=" * 70)

        if result and result.get("success"):
            print(f"\n[OK] Successfully sent combined email with {len(top_news)} news items")
            print(f"Recipients: {recipient_email}")
            print("Please check your inbox for the AI news digest.")
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
