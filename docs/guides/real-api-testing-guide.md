# 真实 API 测试指南

本指南将教您如何通过命令行使用真实的 OpenAI API 进行：
1. 真实数据获取
2. AI 新闻评分
3. 摘要生成

## 前置条件

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置 OpenAI API 密钥
编辑 `.env` 文件，确保设置了正确的 API 密钥：

```bash
# 编辑 .env
nano .env
```

在文件中找到并设置：
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

验证配置：
```bash
python -c "from src.config.settings import Settings; s=Settings(); print(f'✅ API Key configured: {s.openai_api_key[:10]}...')"
```

### 3. 初始化数据库
```bash
python -c "from src.database.connection import init_db; init_db(); print('✅ Database initialized')"
```

---

## 方案 1: 使用真实 API 运行 E2E 测试

这是最快的方式，会进行真实的 API 调用和完整的数据流程。

### 运行真实 API E2E 测试

```bash
# 设置环境变量并运行 E2E 测试
ENABLE_REAL_API_TESTS=1 pytest tests/e2e/test_real_api_optional.py -v -s
```

### 预期输出

```
tests/e2e/test_real_api_optional.py::TestRealAPIScoringIntegration::test_real_api_single_news_scoring PASSED

=============== REAL API TEST RESULTS ===============
News: OpenAI Releases GPT-4o Model

Scoring:
  Score: 85/100
  Category: ai_breakthrough
  Confidence: 92.50%

Key Points:
  1. GPT-4o demonstrates significant improvements in performance
  2. Enhanced capabilities for multimodal processing
  3. Represents major milestone in AI development

Keywords: gpt-4o, multimodal, ai, breakthrough, model

Professional Summary:
  OpenAI announced the release of GPT-4o, a new multimodal large language...

Scientific Summary:
  This advancement represents a significant breakthrough in artificial...

Cost Information:
  API Cost: $0.034567
  Processing Time: 3245ms
  Models Used: gpt-4o
```

### 测试包含内容

- ✅ 单个文章评分
- ✅ 批量文章处理（3 项）
- ✅ 令牌计数准确性验证
- ✅ 成本投影计算
- ✅ 完整的错误处理

### 成本计算

每次运行会显示实际成本，例如：
- 单篇文章：~$0.035
- 批量 3 篇：~$0.105
- 100 篇：~$3.50

---

## 方案 2: 使用 Python 交互式脚本

创建一个脚本进行单个真实 API 调用。

### 创建测试脚本

```bash
cat > test_real_api.py << 'EOF'
"""真实 API 测试脚本"""
import asyncio
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.settings import Settings
from src.models.base import Base
from src.models import DataSource, RawNews
from src.services.ai import ScoringService


async def main():
    # 初始化设置
    settings = Settings()
    print(f"✅ OpenAI API Key: {settings.openai_api_key[:10]}...")

    # 初始化数据库（内存 SQLite）
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()

    # 创建数据源
    data_source = DataSource(
        name="AI News Test",
        source_type="manual",
        url="https://example.com/ai-news",
        active=True,
    )
    db_session.add(data_source)
    db_session.commit()
    print(f"✅ Created data source: {data_source.name}")

    # 创建测试新闻
    raw_news = RawNews(
        source_id=data_source.id,
        title="Google Announces Revolutionary AI Breakthrough",
        url="https://example.com/google-ai-breakthrough",
        content="""
            Google announced today a major breakthrough in artificial intelligence research.
            The new model demonstrates unprecedented capabilities in understanding and
            generating natural language. The research team spent 18 months developing and
            testing the system, which shows improvements across multiple benchmarks.

            Key features include:
            - 40% improvement in reasoning tasks
            - Better handling of context and nuance
            - Improved performance on mathematical problems
            - Enhanced safety and alignment properties

            The company plans to make this technology available to researchers next month
            and to commercial partners by end of year.
        """,
        source_name=data_source.name,
        hash="test_hash_001",
        published_at=datetime.now(),
        fetched_at=datetime.now(),
        status="raw",
    )
    db_session.add(raw_news)
    db_session.commit()
    print(f"✅ Created raw news: {raw_news.title}")

    # 初始化评分服务（真实 API）
    print("\n🚀 Starting real API scoring...")
    service = ScoringService(settings, db_session)

    # 评分
    print("⏳ Scoring with OpenAI API (this will take 10-30 seconds)...")
    result = await service.score_news(raw_news)

    # 显示结果
    print("\n" + "="*60)
    print("📊 SCORING RESULTS")
    print("="*60)
    print(f"Score: {result.scoring.score}/100")
    print(f"Category: {result.scoring.category.value}")
    print(f"Confidence: {result.scoring.confidence:.1%}")
    print(f"\nKey Points:")
    for i, point in enumerate(result.scoring.key_points, 1):
        print(f"  {i}. {point}")

    print(f"\nKeywords: {', '.join(result.scoring.keywords)}")

    print(f"\n📝 Professional Summary:")
    print(f"  {result.summaries.summary_pro}")

    print(f"\n🔬 Scientific Summary:")
    print(f"  {result.summaries.summary_sci}")

    print(f"\n💰 Cost & Performance:")
    print(f"  API Cost: ${result.metadata.cost:.6f}")
    print(f"  Processing Time: {result.metadata.processing_time_ms}ms")
    print(f"  Models Used: {', '.join(result.metadata.ai_models_used)}")

    print(f"\n📊 Cost Breakdown:")
    for operation, cost in result.metadata.cost_breakdown.items():
        print(f"  {operation}: ${cost:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
EOF
```

### 运行脚本

```bash
python test_real_api.py
```

### 预期输出

```
✅ OpenAI API Key: sk-proj-xx...
✅ Created data source: AI News Test
✅ Created raw news: Google Announces Revolutionary AI Breakthrough

🚀 Starting real API scoring...
⏳ Scoring with OpenAI API (this will take 10-30 seconds)...

============================================================
📊 SCORING RESULTS
============================================================
Score: 87/100
Category: ai_breakthrough
Confidence: 94.0%

Key Points:
  1. Google announced major AI breakthrough
  2. 40% improvement in reasoning tasks
  3. Technology available to researchers next month
  4. Commercial partners by end of year
  5. Enhanced safety and alignment properties

Keywords: google, ai, breakthrough, reasoning, language-model

📝 Professional Summary:
  Google announced a major breakthrough in artificial intelligence research.
  The new model demonstrates unprecedented capabilities in understanding and
  generating natural language with 40% improvement in reasoning tasks...

🔬 Scientific Summary:
  This represents a significant advancement in deep learning and natural
  language processing. The breakthrough shows improvements across multiple
  benchmarks including reasoning and mathematical problem-solving...

💰 Cost & Performance:
  API Cost: $0.034567
  Processing Time: 8234ms
  Models Used: gpt-4o

📊 Cost Breakdown:
  scoring: $0.019234
  summary_pro: $0.007667
  summary_sci: $0.007666
```

---

## 方案 3: 与真实 RSS 源集成

从真实的 RSS 源获取数据，然后进行评分。

### 创建 RSS 集成脚本

```bash
cat > test_rss_scoring.py << 'EOF'
"""从 RSS 源获取新闻并进行评分"""
import asyncio
import feedparser
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.settings import Settings
from src.models.base import Base
from src.models import DataSource, RawNews
from src.services.ai import ScoringService


async def fetch_and_score_from_rss():
    """从 RSS 源获取新闻并评分"""

    settings = Settings()

    # 初始化数据库
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()

    # 创建数据源
    data_source = DataSource(
        name="TechCrunch RSS",
        source_type="rss",
        url="https://feeds.techcrunch.com/",
        active=True,
    )
    db_session.add(data_source)
    db_session.commit()

    print(f"📰 Fetching from RSS: {data_source.url}")

    # 获取 RSS feed（使用公共 AI 新闻 feed）
    # 注：这是示例 URL，实际使用时需要替换为有效的 RSS feed
    feed_url = "https://feeds.bloomberg.com/markets/technology.rss"

    feed = feedparser.parse(feed_url)
    print(f"✅ Fetched {len(feed.entries)} entries from RSS")

    # 初始化评分服务
    service = ScoringService(settings, db_session)

    # 获取前 3 篇新闻
    for i, entry in enumerate(feed.entries[:3]):
        print(f"\n{'='*60}")
        print(f"📄 Article {i+1}: {entry.title}")
        print(f"{'='*60}")

        # 创建原始新闻记录
        raw_news = RawNews(
            source_id=data_source.id,
            title=entry.title,
            url=entry.link,
            content=entry.get('summary', entry.title),
            source_name=data_source.name,
            hash=entry.link,
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            status="raw",
        )
        db_session.add(raw_news)
        db_session.commit()

        # 评分
        try:
            print("⏳ Scoring...")
            result = await service.score_news(raw_news)

            print(f"✅ Score: {result.scoring.score}/100")
            print(f"   Category: {result.scoring.category.value}")
            print(f"   Keywords: {', '.join(result.scoring.keywords[:5])}")
            print(f"   Cost: ${result.metadata.cost:.6f}")

        except Exception as e:
            print(f"❌ Error scoring: {str(e)}")


if __name__ == "__main__":
    asyncio.run(fetch_and_score_from_rss())
EOF
```

### 运行 RSS 评分

```bash
python test_rss_scoring.py
```

---

## 方案 4: 批量处理真实数据

创建多篇文章并批量评分。

```bash
cat > test_batch_scoring.py << 'EOF'
"""批量处理真实数据"""
import asyncio
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.settings import Settings
from src.models.base import Base
from src.models import DataSource, RawNews
from src.services.ai import ScoringService


async def batch_score():
    settings = Settings()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()

    # 创建数据源
    data_source = DataSource(
        name="AI News Batch Test",
        source_type="manual",
        url="https://example.com",
        active=True,
    )
    db_session.add(data_source)
    db_session.commit()

    # 创建 5 篇测试文章
    test_articles = [
        {
            "title": "OpenAI Releases GPT-4 Turbo",
            "content": "OpenAI announced GPT-4 Turbo with improved performance and lower costs..."
        },
        {
            "title": "Google DeepMind Solves Protein Folding",
            "content": "DeepMind made a breakthrough in protein structure prediction using AI..."
        },
        {
            "title": "Meta Releases Llama 2 Open Source",
            "content": "Meta made their latest language model available as open source..."
        },
        {
            "title": "Microsoft Invests in Anthropic",
            "content": "Microsoft announced a $10 billion investment in AI safety startup..."
        },
        {
            "title": "Tesla Advances Full Self-Driving",
            "content": "Tesla released new version of Full Self-Driving beta with improvements..."
        },
    ]

    # 创建 RawNews 记录
    news_items = []
    for i, article in enumerate(test_articles):
        raw_news = RawNews(
            source_id=data_source.id,
            title=article["title"],
            url=f"https://example.com/article-{i}",
            content=article["content"],
            source_name=data_source.name,
            hash=f"hash_{i}",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            status="raw",
        )
        db_session.add(raw_news)
        news_items.append(raw_news)

    db_session.commit()
    print(f"✅ Created {len(news_items)} news items")

    # 批量评分
    print("\n🚀 Starting batch scoring with real API...")
    service = ScoringService(settings, db_session)
    results, errors = await service.batch_score(news_items)

    # 显示结果汇总
    print(f"\n{'='*60}")
    print(f"📊 BATCH SCORING RESULTS")
    print(f"{'='*60}")
    print(f"✅ Successful: {len(results)}")
    print(f"❌ Failed: {len(errors)}")

    total_cost = sum(r.metadata.cost for r in results)
    print(f"\n💰 Total Cost: ${total_cost:.6f}")
    print(f"💰 Cost per Item: ${total_cost/len(results):.6f}")

    print(f"\n📋 Results Summary:")
    print(f"{'Article':<40} {'Score':<8} {'Category':<20} {'Cost':<10}")
    print(f"{'-'*78}")

    for result in results:
        article_title = result.scoring.__dict__.get('title', 'Unknown')[:38]
        print(f"{article_title:<40} {result.scoring.score:<8} "
              f"{result.scoring.category.value:<20} ${result.metadata.cost:>8.6f}")


if __name__ == "__main__":
    asyncio.run(batch_score())
EOF
```

### 运行批量评分

```bash
python test_batch_scoring.py
```

### 预期输出

```
✅ Created 5 news items

🚀 Starting batch scoring with real API...

============================================================
📊 BATCH SCORING RESULTS
============================================================
✅ Successful: 5
❌ Failed: 0

💰 Total Cost: $0.172834
💰 Cost per Item: $0.034567

📋 Results Summary:
Article                                  Score   Category             Cost
-------------------------------
OpenAI Releases GPT-4 Turbo              85      ai_breakthrough      $ 0.034567
Google DeepMind Solves Protein Folding   82      research_discovery   $ 0.033456
Meta Releases Llama 2 Open Source        78      model_release        $ 0.034234
Microsoft Invests in Anthropic           75      company_news         $ 0.034578
Tesla Advances Full Self-Driving         80      autonomous_vehicle   $ 0.035999
```

---

## 方案 5: 监控成本与性能

实时跟踪 API 调用的成本和性能。

```bash
cat > monitor_cost.py << 'EOF'
"""监控评分成本和性能"""
import asyncio
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.settings import Settings
from src.models.base import Base
from src.models import DataSource, RawNews, CostLog
from src.services.ai import ScoringService


async def monitor_scoring():
    settings = Settings()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()

    # 创建数据源
    data_source = DataSource(
        name="Cost Monitoring Test",
        source_type="manual",
        url="https://example.com",
        active=True,
    )
    db_session.add(data_source)
    db_session.commit()

    # 创建 10 篇测试文章
    print("📝 Creating 10 test articles...")
    news_items = []
    for i in range(10):
        raw_news = RawNews(
            source_id=data_source.id,
            title=f"AI News Article {i+1}",
            url=f"https://example.com/article-{i}",
            content=f"This is article {i+1} about artificial intelligence developments "
                   f"and recent breakthroughs in machine learning technology.",
            source_name=data_source.name,
            hash=f"hash_{i}",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            status="raw",
        )
        db_session.add(raw_news)
        news_items.append(raw_news)

    db_session.commit()

    # 评分并监控成本
    print("\n🚀 Scoring and monitoring costs...")
    print(f"{'Article':<20} {'Time(ms)':<10} {'Cost':<12} {'Speed(tok/s)':<15}")
    print("-" * 60)

    service = ScoringService(settings, db_session)
    total_cost = 0
    total_tokens = 0

    for i, news in enumerate(news_items):
        result = await service.score_news(news)

        processing_time = result.metadata.processing_time_ms
        cost = result.metadata.cost
        total_cost += cost

        # 显示统计
        article_label = f"Article {i+1}"
        speed_estimate = 1000 / max(processing_time, 1)  # 粗略估计

        print(f"{article_label:<20} {processing_time:<10.0f} "
              f"${cost:<11.6f} {speed_estimate:<15.1f}")

    # 汇总信息
    print("\n" + "="*60)
    print("📊 COST MONITORING SUMMARY")
    print("="*60)
    print(f"Total Articles: 10")
    print(f"Total Cost: ${total_cost:.6f}")
    print(f"Cost per Article: ${total_cost/10:.6f}")
    print(f"Daily Cost (100 articles): ${(total_cost/10)*100:.2f}")
    print(f"Monthly Cost (3000 articles): ${(total_cost/10)*3000:.2f}")
    print(f"\n✅ Cost monitoring complete")


if __name__ == "__main__":
    asyncio.run(monitor_scoring())
EOF
```

### 运行成本监控

```bash
python monitor_cost.py
```

---

## 故障排除

### 问题 1: 无效的 API 密钥

```bash
# 错误消息
"Error: 401 Unauthorized - Invalid API key"

# 解决方案
1. 验证 .env 文件中的密钥：
   grep OPENAI_API_KEY .env

2. 检查密钥格式（应以 sk- 开头）：
   python -c "from src.config.settings import Settings; s=Settings(); print(s.openai_api_key[:5])"

3. 重新生成密钥：
   https://platform.openai.com/account/api-keys
```

### 问题 2: 超时错误

```bash
# 错误消息
"Error: Request timeout after 30 seconds"

# 解决方案
1. 检查网络连接：
   ping api.openai.com

2. 检查 OpenAI 服务状态：
   https://status.openai.com/

3. 增加超时时间（在代码中修改）
```

### 问题 3: 高成本

```bash
# 消息
"Total cost: $50 for 100 articles"

# 解决方案
1. 使用 GPT-3.5-turbo 而不是 GPT-4（更便宜）
2. 缩短摘要长度
3. 减少 token 数量
4. 使用批处理 API（如果可用）
```

---

## 常见命令

### 快速测试单篇文章

```bash
python -c "
import asyncio
from src.config.settings import Settings
from src.models import RawNews
from src.services.ai import ScoringService
from datetime import datetime

async def test():
    settings = Settings()
    news = RawNews(
        source_id=1,
        title='Test Article',
        content='This is a test article about AI.',
        url='https://example.com',
        source_name='Test',
        hash='test',
        published_at=datetime.now(),
        fetched_at=datetime.now(),
        status='raw'
    )
    service = ScoringService(settings, None)
    result = await service.score_news(news)
    print(f'Score: {result.scoring.score}')

asyncio.run(test())
"
```

### 查看成本估算

```bash
python -c "
# 计算成本（基于 GPT-4o 价格）
articles = [100, 300, 500, 1000]
cost_per_article = 0.017

for count in articles:
    daily_cost = cost_per_article * count
    monthly_cost = daily_cost * 30
    print(f'{count} articles/day: ${daily_cost:.2f}/day (${monthly_cost:.2f}/month)')
"
```

### 运行所有 E2E 测试

```bash
ENABLE_REAL_API_TESTS=1 pytest tests/e2e/ -v -s --tb=short
```

---

## 成本参考

| 场景 | 成本 |
|------|------|
| 单篇文章（评分+2摘要） | ~$0.017 |
| 100 篇/天 | ~$1.70/天 ($51/月) |
| 300 篇/天 | ~$5.10/天 ($153/月) |
| 500 篇/天 | ~$8.50/天 ($255/月) |
| 1000 篇/天 | ~$17/天 ($510/月) |

---

## 下一步

完成真实 API 测试后：

1. ✅ 验证评分准确性
2. ✅ 验证摘要质量
3. ✅ 确认成本计算
4. ✅ 准备生产部署
5. ⏳ 实现人工审核流程
6. ⏳ 实现多渠道发布

---

**文档版本**: 1.0
**最后更新**: 2025-11-02
**状态**: 可用于测试
