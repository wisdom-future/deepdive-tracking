#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
演示脚本 - 使用 Mock 数据显示完整的评分流程

这个脚本不需要真实的 OpenAI API，使用 Mock 数据演示：
1. 数据库初始化
2. 新闻创建
3. AI 评分流程
4. 摘要生成
5. 成本分析

用于演示和测试，无需 API 成本。
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
import io
import json

# 设置标准输出编码为 UTF-8 (Windows 兼容)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.config.settings import Settings
    from src.models.base import Base
    from src.models import DataSource, RawNews
    from src.services.ai import ScoringService
except ImportError as e:
    print(f"❌ Error importing modules: {str(e)}")
    sys.exit(1)


async def main():
    """运行演示"""

    print("\n" + "="*70)
    print("🎬 DeepDive Tracking - Demo with Mock Data")
    print("="*70)

    # 1. 初始化设置
    print("\n1️⃣  Loading Settings...")
    try:
        settings = Settings()
        print("✅ Settings loaded")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
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
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return

    # 3. 创建数据源
    print("\n3️⃣  Creating Data Source...")
    try:
        data_source = DataSource(
            name="Demo News Source",
            type="api",
            url="https://example.com/test",
            is_enabled=True,
        )
        db_session.add(data_source)
        db_session.commit()
        print(f"✅ Created: {data_source.name}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return

    # 4. 创建样本新闻
    print("\n4️⃣  Creating Sample News Article...")
    try:
        raw_news = RawNews(
            source_id=data_source.id,
            title="OpenAI Releases GPT-4o - New Multimodal AI Breakthrough",
            url="https://example.com/gpt-4o-release",
            content="""
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
for various industries including education, healthcare, and scientific research.
            """,
            source_name=data_source.name,
            hash="demo_gpt4o_20251102",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            status="raw",
        )
        db_session.add(raw_news)
        db_session.commit()
        print(f"✅ Created: {raw_news.title}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return

    # 5. 初始化评分服务
    print("\n5️⃣  Initializing Scoring Service...")
    try:
        service = ScoringService(settings, db_session)
        print("✅ Service initialized")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return

    # 6. 使用 Mock 执行评分
    print("\n6️⃣  Performing AI Scoring (with Mock Data)...")
    print("⏳ Simulating OpenAI API call...")

    try:
        # 创建 mock 响应
        with patch("src.services.ai.scoring_service.OpenAI"):
            service.client = Mock()

            # Mock 评分响应
            mock_scoring = Mock()
            mock_scoring.choices = [Mock()]
            mock_scoring.choices[0].message.content = json.dumps({
                "score": 87,
                "score_reasoning": "Major breakthrough in AI technology with significant implications",
                "category": "tech_breakthrough",
                "sub_categories": ["model_release", "research_advancement"],
                "confidence": 0.94,
                "key_points": [
                    "OpenAI released GPT-4o multimodal model",
                    "Enhanced capabilities for text, images, and audio",
                    "Improved reasoning and problem-solving",
                    "Cost-effective compared to previous versions",
                    "Major milestone in AI development"
                ],
                "keywords": ["gpt-4o", "multimodal", "ai", "breakthrough", "openai"],
                "entities": {
                    "companies": ["OpenAI"],
                    "technologies": ["GPT-4o", "AI", "NLP"],
                    "people": []
                },
                "impact_analysis": "High impact on AI industry, significant advancement in multimodal processing"
            })
            mock_scoring.usage.prompt_tokens = 500
            mock_scoring.usage.completion_tokens = 300

            # Mock 专业摘要
            mock_summary_pro = Mock()
            mock_summary_pro.choices = [Mock()]
            mock_summary_pro.choices[0].message.content = json.dumps({
                "summary_pro": "OpenAI released GPT-4o, a multimodal AI breakthrough. Enhanced capabilities for text, images, and audio processing with improved reasoning and cost efficiency. Significant milestone with broad implications for education, healthcare, and research."
            })
            mock_summary_pro.usage.prompt_tokens = 200
            mock_summary_pro.usage.completion_tokens = 100

            # Mock 科学摘要
            mock_summary_sci = Mock()
            mock_summary_sci.choices = [Mock()]
            mock_summary_sci.choices[0].message.content = json.dumps({
                "summary_sci": "GPT-4o advances deep learning architecture with multimodal capabilities. Demonstrates improved cross-modal understanding and reasoning. Enhanced performance across benchmarks with reduced computational costs and algorithmic improvements over previous generations."
            })
            mock_summary_sci.usage.prompt_tokens = 200
            mock_summary_sci.usage.completion_tokens = 100

            # 设置 mock 响应序列
            service.client.chat.completions.create.side_effect = [
                mock_scoring,
                mock_summary_pro,
                mock_summary_sci,
            ]

            # 执行评分
            result = await service.score_news(raw_news)
            print("✅ Scoring completed (using Mock data)")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # 7. 显示完整结果
    print("\n" + "="*70)
    print("📊 COMPLETE SCORING RESULTS")
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

    print(f"\n🏢 Entities Detected:")
    print(f"  Companies: {', '.join(result.scoring.entities.companies) or 'None'}")
    print(f"  Technologies: {', '.join(result.scoring.entities.technologies) or 'None'}")
    print(f"  People: {', '.join(result.scoring.entities.people) or 'None'}")

    print(f"\n📝 Professional Summary:")
    # 分行显示摘要
    summary_pro = result.summaries.summary_pro
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
    print(f"  Processing Time: {result.metadata.processing_time_ms}ms")
    print(f"  API Cost (Mock): $0.034567 (estimated)")
    print(f"  Models Used: {', '.join(result.metadata.ai_models_used)}")

    # 8. 成本投影
    print(f"\n📈 Cost Projections (Real API Pricing):")
    daily_items = [100, 300, 500]
    for count in daily_items:
        cost = 0.017 * count
        print(f"  {count:3d} articles/day: ${cost:7.2f}/day (${cost*30:7.2f}/month)")

    print("\n" + "="*70)
    print("✅ Demo Complete!")
    print("="*70)

    print("\n📚 Next Steps:")
    print("  1. Run diagnostic: python scripts/diagnose-api.py")
    print("  2. Run real API test: python scripts/test-real-api.py")
    print("  3. Run batch test: python scripts/test-batch-scoring.py 5")
    print("  4. Run E2E tests: ENABLE_REAL_API_TESTS=1 pytest tests/e2e/ -v -s")

    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
