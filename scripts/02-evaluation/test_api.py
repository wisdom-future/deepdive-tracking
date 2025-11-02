#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
真实 API 快速测试脚本

使用方法:
    python scripts/test-real-api.py
    # 或从项目根目录
    cd deepdive-tracking && python scripts/test-real-api.py

这个脚本会:
1. 验证 OpenAI API 配置
2. 创建样本新闻
3. 使用真实 API 进行评分
4. 生成专业和科学摘要
5. 显示成本分析
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
import io

# 设置标准输出编码为 UTF-8 (Windows 兼容)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置日志为 DEBUG 以查看详细信息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
except ImportError:
    print("❌ SQLAlchemy not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

try:
    from src.config.settings import Settings
    from src.models.base import Base
    from src.models import DataSource, RawNews
    from src.services.ai import ScoringService
except ImportError as e:
    print(f"❌ Error importing modules: {str(e)}")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path[:3]}")
    sys.exit(1)


async def main():
    """运行真实 API 测试"""

    print("\n" + "="*70)
    print("🚀 DeepDive Tracking - Real API Quick Test")
    print("="*70)

    # 1. 验证配置
    print("\n1️⃣  Verifying OpenAI API Configuration...")
    try:
        settings = Settings()
        if not settings.openai_api_key or settings.openai_api_key.startswith("mock"):
            print("❌ OpenAI API Key not configured or using mock key")
            print("   Please set OPENAI_API_KEY in .env file")
            return
        print(f"✅ API Key configured: {settings.openai_api_key[:20]}...")
    except Exception as e:
        print(f"❌ Error loading settings: {str(e)}")
        return

    # 2. 初始化数据库
    print("\n2️⃣  Initializing Database...")
    try:
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db_session = Session()
        print("✅ Database initialized (in-memory SQLite)")
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return

    # 3. 创建数据源
    print("\n3️⃣  Creating Data Source...")
    try:
        data_source = DataSource(
            name="Quick Test Source",
            type="api",  # 必须是: rss, crawler, api, twitter, email
            url="https://example.com/test",
            is_enabled=True,
        )
        db_session.add(data_source)
        db_session.commit()
        print(f"✅ Created data source: {data_source.name}")
    except Exception as e:
        print(f"❌ Error creating data source: {str(e)}")
        return

    # 4. 创建样本新闻
    print("\n4️⃣  Creating Sample News Article...")
    sample_content = """
OpenAI released GPT-4o, a new multimodal AI model that represents a significant
advancement in artificial intelligence. The model demonstrates enhanced capabilities
for processing text, images, and audio simultaneously.

Key Features:
- Improved reasoning and problem-solving abilities
- Better understanding of nuanced language and context
- Enhanced multimodal processing capabilities
- Increased safety and alignment measures
- More cost-effective than previous versions

The release marks a major milestone in AI development and has significant implications
for various industries including education, healthcare, and scientific research. The
model is being made available to researchers and developers through OpenAI's API.
    """

    try:
        raw_news = RawNews(
            source_id=data_source.id,
            title="OpenAI Releases GPT-4o - New Multimodal AI Breakthrough",
            url="https://example.com/gpt-4o-release",
            content=sample_content,
            source_name=data_source.name,
            hash="test_gpt4o_20251102",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            status="raw",
        )
        db_session.add(raw_news)
        db_session.commit()
        print(f"✅ Created news: {raw_news.title}")
    except Exception as e:
        print(f"❌ Error creating news: {str(e)}")
        return

    # 5. 初始化评分服务
    print("\n5️⃣  Initializing Scoring Service...")
    try:
        service = ScoringService(settings, db_session)
        print("✅ Scoring service initialized")
    except Exception as e:
        print(f"❌ Error initializing service: {str(e)}")
        return

    # 6. 执行评分（真实 API）
    print("\n6️⃣  Scoring News with Real OpenAI API...")
    print("⏳ This will take 10-30 seconds...")
    try:
        result = await service.score_news(raw_news)
        print("✅ Scoring completed successfully")
    except Exception as e:
        print(f"❌ Error scoring news: {str(e)}")
        print(f"   Please check your OpenAI API key and account balance")
        return

    # 7. 显示结果
    print("\n" + "="*70)
    print("📊 SCORING RESULTS")
    print("="*70)

    print(f"\n📰 Article: {raw_news.title}")

    print(f"\n🎯 Scoring:")
    print(f"  Score: {result.scoring.score}/100")
    print(f"  Category: {result.scoring.category.value}")
    print(f"  Confidence: {result.scoring.confidence:.1%}")
    print(f"  Quality Score: {result.quality_score:.2f}/1.00")

    print(f"\n📌 Key Points:")
    for i, point in enumerate(result.scoring.key_points, 1):
        print(f"  {i}. {point}")

    print(f"\n🏷️  Keywords:")
    print(f"  {', '.join(result.scoring.keywords)}")

    print(f"\n📝 Professional Summary:")
    summary_pro = result.summaries.summary_pro
    # 分行显示摘要
    words = summary_pro.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 <= 66:
            line += word + " "
        else:
            print(f"  {line}")
            line = word + " "
    if line:
        print(f"  {line}")

    print(f"\n🔬 Scientific Summary:")
    summary_sci = result.summaries.summary_sci
    words = summary_sci.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 <= 66:
            line += word + " "
        else:
            print(f"  {line}")
            line = word + " "
    if line:
        print(f"  {line}")

    print(f"\n💰 Cost & Performance:")
    print(f"  API Cost: ${result.metadata.cost:.6f}")
    print(f"  Processing Time: {result.metadata.processing_time_ms}ms")
    print(f"  Models Used: {', '.join(result.metadata.ai_models_used)}")

    print(f"\n📊 Cost Breakdown:")
    for operation, cost in result.metadata.cost_breakdown.items():
        print(f"  {operation}: ${cost:.6f}")

    # 8. 成本投影
    print(f"\n📈 Cost Projections (based on $0.017 per article):")
    projections = [
        ("Daily (100 articles)", 100),
        ("Daily (300 articles)", 300),
        ("Monthly (3,000 articles)", 3000),
        ("Monthly (10,000 articles)", 10000),
    ]
    for label, count in projections:
        cost = 0.017 * count
        print(f"  {label}: ${cost:.2f}")

    print("\n" + "="*70)
    print("✅ Real API Test Completed Successfully!")
    print("="*70)

    print("\n📚 Next Steps:")
    print("  1. Review the evaluation accuracy")
    print("  2. Check if summaries are high quality")
    print("  3. Verify cost calculations")
    print("  4. Run with more articles: scripts/test-batch-scoring.py")
    print("  5. Run E2E tests: ENABLE_REAL_API_TESTS=1 pytest tests/e2e/ -v -s")

    print("\n📖 See docs/guides/real-api-testing-guide.md for more options")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
