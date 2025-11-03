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
            smtp_password=settings.smtp_password,
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

    # Send TOP news email
    print("\n4. Sending TOP news email...")
    recipient_email = settings.smtp_from_email or "hello.junjie.duan@gmail.com"
    print(f"    Recipient: {recipient_email}")

    sent_count = 0
    failed_count = 0

    try:
        # Send each top news item
        for idx, news in enumerate(top_news, 1):
            if not news.raw_news:
                print(f"\n    Skipping news {idx}/{len(top_news)}: No raw_news relationship")
                failed_count += 1
                continue

            title = news.raw_news.title[:50] if news.raw_news.title else "Unknown"
            print(f"\n    Sending news {idx}/{len(top_news)}: {title}...")

            try:
                # Use summary_pro for professional summary, or raw content
                summary = news.summary_pro or news.summary_sci or "No summary available"
                content = news.raw_news.content or "No content available"
                author = news.raw_news.source_name or news.raw_news.author or "Unknown Source"
                source_url = news.raw_news.url or "https://deepdive-tracking.github.io"

                result = await publisher.publish_article(
                    title=news.raw_news.title,
                    content=content,
                    summary=summary,
                    author=author,
                    source_url=source_url,
                    score=float(news.score or 0),
                    category=news.category or "AI News",
                    email_list=[recipient_email]
                )

                if result and result.get("success"):
                    print(f"        [OK] Email sent successfully")
                    sent_count += 1
                else:
                    error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else "Unknown error"
                    print(f"        [WARNING] Email send returned: {error_msg}")
                    failed_count += 1

            except Exception as e:
                print(f"        [WARNING] Failed to send news {idx}: {e}")
                failed_count += 1

        print("\n" + "=" * 70)
        print("TOP NEWS EMAIL SENDING COMPLETE")
        print("=" * 70)
        print(f"\nResults:")
        print(f"  Successfully sent: {sent_count}/{len(top_news)} emails")
        if failed_count > 0:
            print(f"  Failed: {failed_count}/{len(top_news)} emails")
        print(f"\nEmails sent to: {recipient_email}")
        print("Please check your inbox for the AI news emails.")

        return True

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
