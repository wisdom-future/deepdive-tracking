#!/usr/bin/env python3
"""
Send TOP AI News Digest - Send highest-scored AI articles in a single digest email

This script sends all TOP AI news articles in one consolidated email with card layout,
focused exclusively on AI/ML/LLM related content.
"""
import sys
import os
import asyncio
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.channels.email.email_publisher import EmailPublisher
from src.config.settings import get_settings
from src.models import ProcessedNews, RawNews
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, joinedload


# AI-related keywords and categories
AI_KEYWORDS = {
    'ai', 'artificial intelligence', 'machine learning', 'deep learning',
    'llm', 'large language model', 'generative ai', 'neural network',
    'ml', 'nlp', 'computer vision', 'transformer', 'bert', 'gpt',
    'openai', 'google', 'anthropic', 'meta ai', 'mistral',
    'algorithm', 'data science', 'model', 'training', 'inference',
    'chatgpt', 'claude', 'gemini', 'copilot', 'agent', 'rag',
    'embedding', 'vector', 'diffusion', 'vision model', 'robotics',
}


def is_ai_related(news: ProcessedNews) -> bool:
    """Check if a news article is AI-related"""
    if not news.raw_news:
        return False

    # Check category
    category = (news.category or "").lower()
    if any(keyword in category for keyword in ['ai', 'machine', 'deep', 'ml', 'llm']):
        return True

    # Check title
    title = (news.raw_news.title or "").lower()
    if any(keyword in title for keyword in AI_KEYWORDS):
        return True

    # Check summary
    summary = (news.summary_pro or news.summary_sci or "").lower()
    if summary and any(keyword in summary for keyword in AI_KEYWORDS):
        return True

    return False


def generate_digest_html(news_items: list) -> str:
    """Generate HTML for the digest email with card layout - bilingual"""
    cards_html = ""
    for idx, news in enumerate(news_items, 1):
        if not news.raw_news:
            continue

        title = news.raw_news.title or "Untitled"

        # Get Chinese summary (primary)
        summary_zh = news.summary_pro or news.summary_sci or news.raw_news.content or "No summary"

        # Get English summary (secondary)
        summary_en = news.summary_pro_en or news.summary_sci_en

        # Validate English summary
        if not summary_en or len(summary_en.strip()) < 20:
            summary_en = summary_zh  # Fallback to Chinese if English is invalid

        url = news.raw_news.url or "#"
        score = news.score or 0
        source = news.raw_news.source_name or news.raw_news.author or "Unknown"

        # For card display, use Chinese primary with English in parentheses
        summary = summary_zh
        if summary_en and summary_en != summary_zh:
            # Only add English if it's different from Chinese
            summary = f"{summary_zh}\n\n(EN: {summary_en})"

        # Truncate summary to 200 chars
        if len(summary) > 200:
            summary = summary[:197] + "..."

        score_color = "green" if score >= 80 else "orange" if score >= 60 else "gray"
        score_icon = "⭐" if score >= 80 else "✨" if score >= 60 else "📰"

        cards_html += f"""
        <div style="
            margin: 15px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #{('2ecc71' if score >= 80 else 'f39c12' if score >= 60 else 'bdc3c7')};
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <h3 style="
                        margin: 0 0 10px 0;
                        color: #1a1a1a;
                        font-size: 16px;
                        font-weight: 600;
                        line-height: 1.4;
                    ">{title}</h3>
                    <p style="
                        margin: 0 0 8px 0;
                        color: #555;
                        font-size: 14px;
                        line-height: 1.5;
                    ">{summary}</p>
                    <div style="
                        margin-top: 10px;
                        font-size: 12px;
                        color: #888;
                    ">
                        <span>📚 {source}</span>
                    </div>
                </div>
                <div style="
                    margin-left: 15px;
                    text-align: center;
                    padding: 10px 12px;
                    background-color: white;
                    border-radius: 4px;
                    white-space: nowrap;
                ">
                    <div style="font-size: 24px;">{score_icon}</div>
                    <div style="
                        font-size: 18px;
                        font-weight: bold;
                        color: #{('2ecc71' if score >= 80 else 'f39c12' if score >= 60 else 'bdc3c7')};
                    ">{score:.0f}</div>
                    <div style="font-size: 11px; color: #888;">score</div>
                </div>
            </div>
            <div style="margin-top: 10px;">
                <a href="{url}" style="
                    display: inline-block;
                    padding: 6px 12px;
                    background-color: #0066cc;
                    color: white;
                    text-decoration: none;
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: 500;
                ">Read Article →</a>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepDive Tracking - TOP AI News Digest</title>
</head>
<body style="
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
    font-family: 'Segoe UI', Arial, sans-serif;
">
    <div style="
        max-width: 600px;
        margin: 0 auto;
        background-color: white;
        padding: 30px 20px;
    ">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="
                color: #1a1a1a;
                margin: 0 0 10px 0;
                font-size: 28px;
            ">🤖 DeepDive Tracking</h1>
            <h2 style="
                color: #0066cc;
                margin: 0 0 5px 0;
                font-size: 20px;
                font-weight: 500;
            ">TOP AI News Digest</h2>
            <p style="
                color: #888;
                margin: 5px 0 0 0;
                font-size: 13px;
            ">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>

        <div style="
            background-color: #e3f2fd;
            border-left: 4px solid #0066cc;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 4px;
        ">
            <p style="
                margin: 0;
                color: #0066cc;
                font-size: 13px;
                line-height: 1.6;
            ">
                <strong>Welcome to the TOP AI News Digest!</strong><br>
                We've curated the highest-scored AI/ML/LLM news from today.
                Each article is carefully selected and scored by our AI system.
            </p>
        </div>

        <div style="margin-bottom: 25px;">
            {cards_html}
        </div>

        <div style="
            border-top: 1px solid #ddd;
            padding-top: 20px;
            margin-top: 30px;
            font-size: 12px;
            color: #888;
            text-align: center;
        ">
            <p style="margin: 0 0 10px 0;">
                📊 Powered by DeepDive Tracking AI System
            </p>
            <p style="margin: 0;">
                This is an automated daily digest. For more information, visit our platform.
            </p>
        </div>
    </div>
</body>
</html>"""

    return html


async def main():
    """Send TOP AI news digest"""
    settings = get_settings()

    print("=" * 70)
    print("TOP AI NEWS DIGEST - Consolidated Email")
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

    # Fetch all news and filter AI-related ones
    print("\n3. Fetching and filtering AI-related news...")
    try:
        engine = create_engine(settings.database_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Get all news sorted by score
        all_news = session.query(ProcessedNews).options(
            joinedload(ProcessedNews.raw_news)
        ).order_by(desc(ProcessedNews.score)).limit(100).all()

        # Filter AI-related articles
        ai_news = [news for news in all_news if is_ai_related(news)]

        session.close()

        if not ai_news:
            print("[WARNING] No AI-related news found in the database")
            print("Please run news collection first: python scripts/01-collection/collect_news.py")
            return False

        # Limit to top 10 AI articles
        top_ai_news = ai_news[:10]

        print(f"[OK] Found {len(top_ai_news)} AI-related news items (out of {len(all_news)} total)")
        for idx, news in enumerate(top_ai_news, 1):
            title = news.raw_news.title if news.raw_news else "Unknown"
            score = news.score or 0
            print(f"    {idx}. {title[:60]} (Score: {score})")

    except Exception as e:
        print(f"[FAILED] Database query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Generate and send digest email
    print("\n4. Sending TOP AI News Digest email...")
    recipient_email = settings.smtp_from_email or "hello.junjie.duan@gmail.com"
    print(f"    Recipient: {recipient_email}")

    try:
        # Generate digest HTML
        digest_html = generate_digest_html(top_ai_news)

        # Send as a single email with all articles
        result = await publisher.publish_article(
            title="TOP AI News Digest - " + datetime.now().strftime("%Y-%m-%d"),
            content=digest_html,
            summary=f"Daily digest of top {len(top_ai_news)} AI news articles",
            summary_en=f"Daily digest of top {len(top_ai_news)} AI news articles with bilingual summaries",
            author="DeepDive Tracking",
            source_url="https://deepdive-tracking.github.io",
            score=90.0,
            category="AI News Digest",
            email_list=[recipient_email]
        )

        if result and result.get("success"):
            print(f"[OK] Digest email sent successfully!")
            print(f"    Sent to: {recipient_email}")
            print(f"    Articles included: {len(top_ai_news)}")
            return True
        else:
            error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else "Unknown error"
            print(f"[FAILED] Email send failed: {error_msg}")
            return False

    except Exception as e:
        print(f"[FAILED] Exception during send: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print("\n" + "=" * 70)
        if success:
            print("TOP AI NEWS DIGEST SENT SUCCESSFULLY!")
            print("=" * 70)
            print("\nPlease check your inbox for the AI news digest email.")
        else:
            print("TOP AI NEWS DIGEST FAILED!")
            print("=" * 70)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
