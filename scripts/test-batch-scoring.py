#!/usr/bin/env python
"""
真实 API 批量评分脚本

使用方法:
    python scripts/test-batch-scoring.py [count]

参数:
    count: 要评分的文章数（默认 5）

这个脚本会:
1. 创建多篇样本新闻
2. 使用真实 API 批量评分
3. 显示成本汇总
4. 生成性能分析
"""

import asyncio
import sys
from datetime import datetime

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
except ImportError:
    print("❌ SQLAlchemy not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

from src.config.settings import Settings
from src.models.base import Base
from src.models import DataSource, RawNews
from src.services.ai import ScoringService


# 样本文章数据
SAMPLE_ARTICLES = [
    {
        "title": "OpenAI Releases GPT-4o Multimodal Model",
        "content": "OpenAI announced GPT-4o with enhanced multimodal capabilities for "
                  "processing text, images, and audio. The model shows improved "
                  "reasoning and reduced costs compared to previous versions.",
    },
    {
        "title": "Google DeepMind Solves Protein Structure Prediction",
        "content": "DeepMind's AlphaFold achieved breakthrough in protein structure "
                  "prediction with 99% accuracy. This advancement has major implications "
                  "for drug discovery and biological research.",
    },
    {
        "title": "Meta Releases Llama 2 Open Source AI Model",
        "content": "Meta made Llama 2, its latest large language model, available as "
                  "open source. The model demonstrates strong performance across multiple "
                  "benchmarks and is suitable for various applications.",
    },
    {
        "title": "Microsoft Invests $10 Billion in Anthropic AI Safety",
        "content": "Microsoft announced a major investment in AI safety company Anthropic. "
                  "The investment demonstrates growing focus on developing safe and "
                  "beneficial artificial intelligence systems.",
    },
    {
        "title": "Tesla Advances Full Self-Driving Capabilities",
        "content": "Tesla released new Full Self-Driving beta with improved handling of "
                  "complex driving scenarios. The system continues to improve through "
                  "machine learning and real-world data.",
    },
    {
        "title": "Google Announces Gemini AI Model Family",
        "content": "Google unveiled Gemini, a new family of multimodal AI models with "
                  "state-of-the-art performance on various benchmarks. Available in "
                  "different sizes for various applications.",
    },
    {
        "title": "Anthropic Releases Claude 2 Large Language Model",
        "content": "Anthropic introduced Claude 2 with improved performance and safety. "
                  "The model demonstrates better reasoning, coding, and analysis "
                  "capabilities compared to previous versions.",
    },
    {
        "title": "Stability AI Releases SDXL Image Generation Model",
        "content": "Stability AI launched SDXL, an improved text-to-image generation model "
                  "with better quality and consistency. The model is available for "
                  "open source use.",
    },
    {
        "title": "IBM Quantum Computing Advances Reach 1000 Qubits",
        "content": "IBM announced quantum processors with over 1000 qubits. The advancement "
                  "brings practical quantum computing closer to reality with implications "
                  "for optimization and cryptography.",
    },
    {
        "title": "Amazon Launches AI Shopping Assistant",
        "content": "Amazon introduced an AI-powered shopping assistant that provides "
                  "personalized recommendations. The system uses advanced NLP and machine "
                  "learning to understand customer preferences.",
    },
]


async def main():
    """运行批量评分"""

    # 解析命令行参数
    count = 5
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
            if count < 1 or count > len(SAMPLE_ARTICLES):
                print(f"❌ Count must be between 1 and {len(SAMPLE_ARTICLES)}")
                sys.exit(1)
        except ValueError:
            print("❌ Invalid count. Usage: python scripts/test-batch-scoring.py [count]")
            sys.exit(1)

    print("\n" + "="*70)
    print(f"🚀 DeepDive Tracking - Batch Scoring Test ({count} articles)")
    print("="*70)

    # 1. 验证配置
    print("\n1️⃣  Verifying Configuration...")
    try:
        settings = Settings()
        if not settings.openai_api_key or settings.openai_api_key.startswith("mock"):
            print("❌ OpenAI API Key not configured")
            return
        print("✅ Configuration verified")
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
            name="Batch Test Source",
            source_type="manual",
            url="https://example.com/test",
            active=True,
        )
        db_session.add(data_source)
        db_session.commit()
        print("✅ Data source created")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return

    # 4. 创建样本新闻
    print(f"\n4️⃣  Creating {count} Sample Articles...")
    try:
        news_items = []
        for i in range(count):
            article = SAMPLE_ARTICLES[i % len(SAMPLE_ARTICLES)]
            raw_news = RawNews(
                source_id=data_source.id,
                title=article["title"],
                url=f"https://example.com/article-{i}",
                content=article["content"],
                source_name=data_source.name,
                hash=f"batch_test_{i}",
                published_at=datetime.now(),
                fetched_at=datetime.now(),
                status="raw",
            )
            db_session.add(raw_news)
            news_items.append(raw_news)

        db_session.commit()
        print(f"✅ Created {count} articles")
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

    # 6. 批量评分
    print(f"\n6️⃣  Batch Scoring {count} Articles with Real API...")
    print("⏳ Processing... (this will take 30 seconds to several minutes)")

    try:
        results, errors = await service.batch_score(news_items)
        print(f"✅ Batch scoring completed")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return

    # 7. 显示详细结果
    print("\n" + "="*70)
    print("📊 BATCH SCORING RESULTS")
    print("="*70)

    if errors:
        print(f"\n⚠️  Errors: {len(errors)}")
        for error in errors:
            print(f"  - {error['title']}: {error['error']}")

    if results:
        print(f"\n✅ Successfully Scored: {len(results)} articles\n")

        # 显示详细结果表
        print(f"{'#':<3} {'Article Title':<40} {'Score':<8} {'Category':<15} {'Cost':<10}")
        print("-" * 80)

        for i, result in enumerate(results, 1):
            title = news_items[i-1].title[:38]
            print(f"{i:<3} {title:<40} {result.scoring.score:<8} "
                  f"{result.scoring.category.value:<15} ${result.metadata.cost:>8.6f}")

    # 8. 成本汇总
    print("\n" + "="*70)
    print("💰 COST SUMMARY")
    print("="*70)

    if results:
        total_cost = sum(r.metadata.cost for r in results)
        avg_cost = total_cost / len(results)

        print(f"\nTotal Cost: ${total_cost:.6f}")
        print(f"Average Cost per Article: ${avg_cost:.6f}")

        # 成本投影
        print(f"\n📈 Cost Projections:")
        for multiplier, label in [
            (10, "10 articles"),
            (100, "100 articles (1 day)"),
            (3000, "3,000 articles (1 month)"),
            (36000, "36,000 articles (1 year)"),
        ]:
            projected_cost = avg_cost * multiplier
            print(f"  {label:<30} ${projected_cost:>10.2f}")

    # 9. 性能分析
    if results:
        print(f"\n⏱️  PERFORMANCE ANALYSIS:")
        total_time = sum(r.metadata.processing_time_ms for r in results)
        avg_time = total_time / len(results)
        print(f"  Total Processing Time: {total_time}ms")
        print(f"  Average per Article: {avg_time:.0f}ms")
        print(f"  Processing Rate: {1000/avg_time:.2f} articles/second")

    # 10. 完成
    print("\n" + "="*70)
    print("✅ Batch Scoring Test Completed Successfully!")
    print("="*70)

    print("\n📚 Next Steps:")
    print("  1. Review scoring accuracy and relevance")
    print("  2. Evaluate summary quality")
    print("  3. Verify cost estimates")
    print("  4. Run real-time monitoring: python scripts/monitor-cost.py")
    print("  5. Deploy to production when ready")

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
