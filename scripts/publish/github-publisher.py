#!/usr/bin/env python3
"""
GitHub Publisher - Publish TOP news items to GitHub Pages with date-based summaries
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config.settings import get_settings
from src.models import ProcessedNews
from src.database.connection import get_session
from sqlalchemy import desc
from sqlalchemy.orm import joinedload


def get_score_color(score: float) -> str:
    """Get color CSS class based on score"""
    if score >= 80:
        return "#10b981"  # 绿色
    elif score >= 60:
        return "#3b82f6"  # 蓝色
    elif score >= 40:
        return "#f59e0b"  # 橙色
    elif score >= 20:
        return "#ef4444"  # 红色
    else:
        return "#6b7280"  # 灰色


def generate_news_html(news_items: list) -> str:
    """Generate HTML for news items"""
    html_parts = []

    for idx, news in enumerate(news_items, 1):
        if not news.raw_news:
            continue

        # Get summary and limit to ~100 characters
        summary = news.summary_pro or news.summary_sci or "No summary available"
        if len(summary) > 120:
            summary = summary[:120].rsplit(' ', 1)[0] + "..."

        source_url = news.raw_news.url or "https://deepdive-tracking.github.io"
        author = news.raw_news.source_name or news.raw_news.author or "Unknown"
        score = news.score or 0
        category = news.category or "AI News"
        color = get_score_color(score)

        html = f"""
        <div class="news-card">
            <div class="news-header">
                <h3 class="news-title">{idx}. {news.raw_news.title}</h3>
                <span class="news-score" style="background: {color};">Score: {score}/100</span>
            </div>
            <div class="news-summary">{summary}</div>
            <div class="news-meta">
                <span class="meta-item">📌 {category}</span>
                <span class="meta-item">📝 {author}</span>
                <a href="{source_url}" target="_blank" class="news-link" style="color: {color};">Read Full →</a>
            </div>
        </div>
"""
        html_parts.append(html)

    return ''.join(html_parts)


def generate_digest_html(date: str, news_items: list) -> str:
    """Generate complete digest HTML page"""
    news_html = generate_news_html(news_items)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Digest - {date}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.8;
            color: #1f2937;
            background: #f9fafb;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        .header {{
            background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
            color: white;
            padding: 60px 40px;
            border-radius: 12px;
            margin-bottom: 40px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 15px;
            font-weight: 700;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.95;
        }}

        .digest-info {{
            display: flex;
            gap: 40px;
            margin-top: 25px;
            flex-wrap: wrap;
        }}

        .info-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .info-label {{
            opacity: 0.8;
            font-size: 0.95em;
        }}

        .info-value {{
            font-weight: 600;
            font-size: 1.1em;
        }}

        .news-grid {{
            display: grid;
            gap: 24px;
            margin-bottom: 40px;
        }}

        .news-card {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            border-left: 5px solid #3b82f6;
        }}

        .news-card:hover {{
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }}

        .news-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            gap: 20px;
            margin-bottom: 15px;
        }}

        .news-title {{
            font-size: 1.2em;
            font-weight: 700;
            color: #1f2937;
            margin: 0;
            line-height: 1.5;
            flex: 1;
        }}

        .news-score {{
            background: #3b82f4;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.9em;
            white-space: nowrap;
        }}

        .news-summary {{
            color: #4b5563;
            margin-bottom: 15px;
            line-height: 1.7;
            font-size: 0.95em;
        }}

        .news-meta {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
            font-size: 0.9em;
            color: #6b7280;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .news-link {{
            color: #3b82f6;
            text-decoration: none;
            font-weight: 600;
            margin-left: auto;
        }}

        .news-link:hover {{
            text-decoration: underline;
        }}

        .back-link {{
            display: inline-block;
            margin-bottom: 30px;
            padding: 12px 24px;
            background: #f3f4f6;
            color: #1f2937;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.3s;
        }}

        .back-link:hover {{
            background: #e5e7eb;
        }}

        .footer {{
            text-align: center;
            padding: 40px 20px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280;
            font-size: 0.9em;
        }}

        .footer a {{
            color: #3b82f6;
            text-decoration: none;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← Back to All Digests</a>

        <div class="header">
            <h1>📰 AI News Daily Digest</h1>
            <p>Curated top AI news items from 300+ sources</p>
            <div class="digest-info">
                <div class="info-item">
                    <span class="info-label">Published:</span>
                    <span class="info-value">{date}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Total Items:</span>
                    <span class="info-value">{len(news_items)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Updated:</span>
                    <span class="info-value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
            </div>
        </div>

        <div class="news-grid">
            {news_html}
        </div>

        <div class="footer">
            <p>Generated by <a href="https://deepdive-tracking.github.io">DeepDive Tracking</a> - AI News Intelligence Platform</p>
            <p style="margin-top: 15px; opacity: 0.7;">© 2025 DeepDive Tracking. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""


def generate_index_html(digests: list) -> str:
    """Generate index.html listing all digests"""
    digest_items = []
    for digest in sorted(digests, reverse=True):
        date_str = digest.replace('.html', '')
        digest_items.append(f"""
        <div class="digest-item">
            <a href="{digest}" class="digest-link">
                <span class="digest-date">📅 {date_str}</span>
                <span class="digest-arrow">→</span>
            </a>
        </div>
""")

    digest_html = ''.join(digest_items)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Daily Digests</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.8;
            color: #1f2937;
            background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
            padding: 60px 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 50px;
        }}

        .header h1 {{
            font-size: 3em;
            font-weight: 700;
            margin-bottom: 15px;
            background: linear-gradient(135deg, #1f2937 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .header p {{
            font-size: 1.2em;
            color: #6b7280;
            margin-bottom: 10px;
        }}

        .header-meta {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}

        .meta-item {{
            text-align: center;
        }}

        .meta-label {{
            font-size: 0.9em;
            color: #6b7280;
        }}

        .meta-value {{
            font-size: 1.5em;
            font-weight: 700;
            color: #3b82f6;
        }}

        .digests-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 60px;
        }}

        .digest-item {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
        }}

        .digest-item:hover {{
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            transform: translateY(-4px);
        }}

        .digest-link {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 25px 30px;
            text-decoration: none;
            color: inherit;
        }}

        .digest-date {{
            font-size: 1.1em;
            font-weight: 600;
            color: #1f2937;
        }}

        .digest-arrow {{
            font-size: 1.5em;
            color: #3b82f6;
        }}

        .footer {{
            text-align: center;
            padding: 40px 20px;
            color: #6b7280;
            font-size: 0.9em;
        }}

        .footer a {{
            color: #3b82f6;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 AI News Daily Digests</h1>
            <p>Your curated source for top AI news and insights</p>
            <div class="header-meta">
                <div class="meta-item">
                    <div class="meta-label">Total Digests</div>
                    <div class="meta-value">{len(digests)}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Latest Update</div>
                    <div class="meta-value">{datetime.now().strftime('%Y-%m-%d')}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Sources</div>
                    <div class="meta-value">300+</div>
                </div>
            </div>
        </div>

        <div class="digests-grid">
            {digest_html}
        </div>

        <div class="footer">
            <p>Powered by <a href="https://deepdive-tracking.github.io">DeepDive Tracking</a> - AI News Intelligence Platform</p>
            <p style="margin-top: 15px;">© 2025 DeepDive Tracking. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""


def publish_to_github():
    """Publish TOP news to GitHub"""
    settings = get_settings()

    print("=" * 70)
    print("GITHUB PUBLISHER - Publish TOP News Digest")
    print("=" * 70)

    # Fetch TOP news from database
    print("\n1. Fetching TOP news from database...")
    try:
        session = get_session()

        top_news = session.query(ProcessedNews).options(
            joinedload(ProcessedNews.raw_news)
        ).order_by(
            desc(ProcessedNews.score)
        ).limit(10).all()

        session.close()

        if not top_news:
            print("[FAILED] No news found in database")
            return False

        print(f"[OK] Found {len(top_news)} news items")
        for idx, news in enumerate(top_news, 1):
            title = news.raw_news.title if news.raw_news else "Unknown"
            score = news.score or 0
            print(f"    {idx}. {title} (Score: {score})")

    except Exception as e:
        print(f"[FAILED] Database query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Generate HTML files
    print("\n2. Generating HTML pages...")
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        digest_filename = f"{date_str}.html"

        # Create digests directory if it doesn't exist
        digests_dir = Path("docs/digests")
        digests_dir.mkdir(parents=True, exist_ok=True)

        # Generate and save digest HTML
        digest_html = generate_digest_html(date_str, top_news)
        digest_path = digests_dir / digest_filename

        with open(digest_path, 'w', encoding='utf-8') as f:
            f.write(digest_html)

        print(f"[OK] Generated digest: {digest_path}")

        # Get all digest files for index
        digest_files = [f.name for f in digests_dir.glob("*.html") if f.name != "index.html"]

        # Generate and save index.html
        index_html = generate_index_html(digest_files)
        index_path = Path("docs/index.html")
        index_path.parent.mkdir(parents=True, exist_ok=True)

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)

        print(f"[OK] Generated index: {index_path}")

    except Exception as e:
        print(f"[FAILED] HTML generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 70)
    print("GITHUB PUBLISHING COMPLETE")
    print("=" * 70)
    print(f"\n[OK] Published digest for {date_str}")
    print(f"[OK] Updated index.html with {len(digest_files)} digests")
    print("\nFiles generated:")
    print(f"  - {digest_path}")
    print(f"  - {index_path}")

    return True


if __name__ == "__main__":
    try:
        success = publish_to_github()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
