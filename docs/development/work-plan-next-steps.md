# DeepDive Tracking - 实际工作计划（基于真实诊断）

**制定日期：** 2025-11-02
**基于：** `actual-project-status.md` 诊断
**更新周期：** 每日（完成一项更新）

---

## 📊 当前状态概览

| 维度 | 状态 | 备注 |
|------|------|------|
| **代码完整性** | 95% | 架构完善，代码可用 |
| **数据采集** | 10% | 仅33条，需要300-500条/天 |
| **数据源数量** | 6% | 仅3个，需要50个 |
| **AI评分** | 70% | 23/33完成，10条失败 |
| **发布系统** | 0% | 表存在，功能未验证 |
| **Celery自动化** | 0% | 代码存在，运行情况未知 |
| **生产就绪** | 10% | 距离目标还很远 |

---

## 🎯 优先级矩阵

```
高影响&紧急        高影响&不紧急
├─ [P0] 补充数据源    ├─ [P1] 完整内容采集
├─ [P0] 查明评分失败  ├─ [P1] 改进元数据
└─ [P0] 验证Celery   └─ [P1] 优化评分模型

低影响&紧急        低影响&不紧急
├─ [P2] 修复小bug     ├─ [P2] UI改进
└─ [P2] 文档更新      └─ [P2] 性能优化
```

---

## 📋 详细工作计划

### PHASE A: 诊断与修复（Today - 2天）

#### A1: 诊断评分失败的10条记录 [P0] ⏱️ 2小时

**目标：** 找出为什么10条记录未被评分

**具体步骤：**

1. **查看失败记录详情**
```bash
cd D:\projects\deepdive-tracking

python -c "
from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///data/db/deepdive_tracking.db')
with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT id, title, content, status, error_message FROM raw_news
        WHERE id NOT IN (SELECT raw_news_id FROM processed_news)
        ORDER BY id
    '''))
    for row in result:
        print(f'ID:{row[0]}, Title:{row[1][:50]}, Status:{row[3]}, Error:{row[4]}')
"
```

2. **检查Celery任务日志**
```bash
# 查看是否有执行记录
python scripts/show-top-news.py  # 或其他能反映任务执行的脚本

# 检查Redis任务队列
celery -A src.celery_app inspect active
celery -A src.celery_app inspect completed_tasks
```

3. **尝试手动评分**
```bash
python scripts/score_raw_news.py  # 或创建临时脚本重新评分
```

**验收标准：**
- [ ] 明确10条记录未评分的原因
- [ ] 若是临时错误，重新评分成功
- [ ] 更新实际项目状态文档

**责任人：** 我
**截止时间：** 今天 2小时内

---

#### A2: 验证Celery任务配置 [P0] ⏱️ 1小时

**目标：** 确认Celery任务是否按计划运行

**具体步骤：**

1. **检查celery_app配置**
```bash
python -c "
from src.celery_app import celery_app
from celery.beat import SchedulingError

# 打印当前配置
print('CELERY BEAT SCHEDULE:')
print(celery_app.conf.beat_schedule)
"
```

2. **启动Celery并验证**
```bash
# Terminal 1
celery -A src.celery_app worker --loglevel=debug

# Terminal 2
celery -A src.celery_app beat --loglevel=debug

# Terminal 3 (观察)
celery -A src.celery_app inspect scheduled
```

3. **检查任务执行记录**
```bash
# 查看是否有新的cost_logs记录
sqlite3 data/db/deepdive_tracking.db "SELECT MAX(created_at) FROM cost_logs"

# 查看是否有新的processed_news
sqlite3 data/db/deepdive_tracking.db "SELECT MAX(created_at) FROM processed_news"
```

**验收标准：**
- [ ] Celery worker成功启动
- [ ] Beat scheduler成功启动
- [ ] 至少看到一次任务执行
- [ ] 有新的成本和评分记录

**责任人：** 我
**截止时间：** 今天 1小时内

---

### PHASE B: 数据源扩展（Day 1-2）

#### B1: 分析和补充数据源 [P0] ⏱️ 4小时

**目标：** 从3个源扩展到20+个源

**当前状态：**
- OpenAI Blog (RSS) ✅
- Anthropic News (RSS) ❌ (0条)
- Real News Aggregator (API) ✅ (23条)
- 产品需求：50个源

**需要做的：**

1. **调查Anthropic News源失败原因**
```bash
python -c "
from src.services.collection.rss_collector import RSSCollector
from src.models import DataSource
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# 检查Anthropic配置
engine = create_engine('sqlite:///data/db/deepdive_tracking.db')
with Session(engine) as session:
    anthropic = session.query(DataSource).filter_by(id=2).first()
    print(f'URL: {anthropic.url}')
    print(f'Enabled: {anthropic.is_enabled}')
    print(f'Method: {anthropic.method}')
    print(f'Selectors: {anthropic.selectors}')

    # 尝试从源采集
    try:
        collector = RSSCollector(anthropic)
        items = collector.collect()
        print(f'采集到 {len(items)} 条')
    except Exception as e:
        print(f'错误: {e}')
"
```

2. **添加新的RSS源（选择产品需求中的源）**

参考：`docs/product/requirements.md` 第13.1章节的核心信息源清单

需要添加的源（示例）：
```
公司官方（还缺）：
- Google DeepMind Blog
- Meta AI Research
- Microsoft AI Blog
- NVIDIA AI Blog
- Amazon AWS AI Blog

科技媒体（示例）：
- The Verge AI
- TechCrunch AI
- VentureBeat AI
- MIT Technology Review
- Wired

中文源（示例）：
- 机器之心
- 量子位
- AI科技评论
```

3. **实现数据源配置脚本**

创建文件 `scripts/setup_data_sources.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import DataSource
from datetime import datetime

# 需要添加的新源
new_sources = [
    {
        'name': 'Google DeepMind Blog',
        'type': 'rss',
        'url': 'https://deepmind.google/feed.xml',
        'priority': 8,
        'is_enabled': True,
    },
    # ... 更多源
]

engine = create_engine('sqlite:///data/db/deepdive_tracking.db')
with Session(engine) as session:
    for source_data in new_sources:
        source = DataSource(**source_data)
        session.add(source)
    session.commit()
    print(f'添加了 {len(new_sources)} 个数据源')
```

**验收标准：**
- [ ] 修复Anthropic News或删除不可用源
- [ ] 添加15-20个新源
- [ ] 所有源都能成功连接
- [ ] 至少一次完整采集成功

**责任人：** 我
**截止时间：** 第2天下午

---

#### B2: 运行完整采集测试 [P1] ⏱️ 2小时

**目标：** 验证改进后的采集效果

**步骤：**

1. **清空旧数据（可选，仅用于测试）**
```bash
# 建议保留，用于对比分析
```

2. **运行采集脚本**
```bash
python scripts/collect_and_score_real_news.py
```

3. **验证结果**
```bash
python -c "
from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///data/db/deepdive_tracking.db')
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM raw_news'))
    total = result.scalar()

    result = conn.execute(text('SELECT COUNT(*) FROM processed_news'))
    scored = result.scalar()

    print(f'总采集: {total}条')
    print(f'已评分: {scored}条')
    print(f'评分率: {scored/total*100:.1f}%')
"
```

**验收标准：**
- [ ] 采集>50条新闻
- [ ] 评分成功率>90%
- [ ] Author字段填充>50%
- [ ] Content长度>500字符平均

**责任人：** 我
**截止时间：** Day 2下午

---

### PHASE C: 内容质量改进（Day 2-3）

#### C1: 实现全文内容提取 [P1] ⏱️ 4小时

**目标：** 从仅feed summary提升到完整文章内容

**当前问题：**
- 12/33条 (<100字符，可能是summary)
- 缺少作者信息 (20/33条)

**实现方案：**

1. **检查RSSCollector的内容提取逻辑**

文件：`src/services/collection/rss_collector.py`

```python
# 当前可能只提取了summary
def collect(self) -> List[Dict[str, Any]]:
    # ...
    for entry in feed.entries:
        article = {
            'title': entry.get('title', ''),
            'url': entry.get('link', ''),
            'content': entry.get('summary', ''),  # ❌ 只提取summary
            'author': entry.get('author', ''),
        }
```

2. **改进方案：优先级依次**
```python
# 方案A: 提取完整内容（最好但最慢）
# 1. 从URL获取页面HTML
# 2. 使用BeautifulSoup提取正文
# 3. 保存HTML到html_content字段

# 方案B: 混合策略（推荐）
# 1. 先使用feed.content（某些RSS提供完整内容）
# 2. 若content为空或太短，尝试从URL抓取
# 3. 最后才用summary

# 方案C: 快速修复（暂时）
# 1. 使用 content:encoded 或 description 标签
# 2. 某些feed提供更长的摘要
```

3. **实现新的collector方法**
```python
def _extract_best_content(self, entry):
    """从RSS entry提取最好的内容"""
    # 优先级: content > summary > description
    content = entry.get('content', '')
    if not content or len(content) < 50:
        content = entry.get('summary', '')
    return content

def _extract_author(self, entry):
    """从RSS entry提取作者"""
    # 优先级: author > author_detail.name > source
    author = entry.get('author', '')
    if not author and 'author_detail' in entry:
        author = entry.author_detail.get('name', '')
    return author
```

**验收标准：**
- [ ] 改进RSS collector
- [ ] Content平均长度>200字符
- [ ] Author填充率>70%
- [ ] 代码测试通过

**责任人：** 我
**截止时间：** Day 3上午

---

#### C2: 解决10条未评分问题 [P0] ⏱️ 2小时

**目标：** 使所有采集的记录都被评分

**步骤：**

1. **创建补充评分脚本**
```python
# scripts/rescore_unscored.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from src.services.ai.scoring_service import ScoringService
from src.models import RawNews, ProcessedNews

engine = create_engine('sqlite:///data/db/deepdive_tracking.db')

with Session(engine) as session:
    # 查询未评分的记录
    unscored = session.query(RawNews).filter(
        ~RawNews.processed_news.any()
    ).all()

    print(f'开始评分 {len(unscored)} 条记录')

    scorer = ScoringService()
    for article in unscored:
        try:
            result = scorer.score(article)
            processed = ProcessedNews(
                raw_news_id=article.id,
                **result
            )
            session.add(processed)
            session.commit()
            print(f'✓ {article.id}')
        except Exception as e:
            print(f'✗ {article.id}: {e}')
```

2. **执行补充评分**
```bash
python scripts/rescore_unscored.py
```

**验收标准：**
- [ ] 所有raw_news都有对应processed_news
- [ ] 评分成功率100%（或记录失败原因）

**责任人：** 我
**截止时间：** Day 3下午

---

### PHASE D: 系统验证（Day 3-4）

#### D1: 完整的端到端测试 [P2] ⏱️ 4小时

**目标：** 验证采集→评分→审核→发布的完整流程

**测试场景：**

```
1. 数据采集
   └─ 运行: python scripts/collect_and_score_real_news.py
   └─ 验证: raw_news表新增记录

2. AI评分
   └─ 自动执行
   └─ 验证: processed_news表新增评分

3. 人工审核流程
   └─ 验证: content_review表创建
   └─ 验证: review队列正常运作

4. 发布系统（待实现）
   └─ 验证: published_content有记录
   └─ 验证: 成本日志正常
```

**脚本：** `tests/e2e/test_complete_workflow.py`

```python
def test_complete_workflow():
    """完整工作流测试"""

    # Step 1: 采集
    manager = CollectionManager()
    stats = asyncio.run(manager.collect_all())
    assert stats['total_collected'] > 0

    # Step 2: 评分
    # ...自动执行

    # Step 3: 审核
    review_service = ReviewService()
    queue = review_service.get_queue()
    assert len(queue) > 0

    # Step 4: 验证数据完整性
    assert all_records_have_required_fields()
```

**验收标准：**
- [ ] 采集>20条新闻
- [ ] 评分成功率>95%
- [ ] 审核队列正常
- [ ] 成本追踪准确

**责任人：** 我
**截止时间：** Day 4

---

#### D2: 性能基准测试 [P1] ⏱️ 2小时

**目标：** 验证系统能否处理日均300-500条

**基准测试内容：**

| 指标 | 目标 | 当前 |
|------|------|------|
| 采集速度 | 300-500条/6小时 | ? |
| 评分速度 | 50条/5分钟 | ? |
| 单条成本 | <¥0.02 | ? |
| 评分准确率 | >85% | ? |

**脚本：** `tests/performance/benchmark.py`

```python
def benchmark_collection():
    """采集性能测试"""
    start = time.time()
    manager = CollectionManager()
    result = asyncio.run(manager.collect_all())
    elapsed = time.time() - start

    rate = result['total_collected'] / (elapsed / 3600)
    print(f'采集速度: {rate:.0f} 条/小时')

def benchmark_scoring():
    """评分性能测试"""
    articles = get_test_articles(100)
    scorer = ScoringService()

    start = time.time()
    for article in articles:
        scorer.score(article)
    elapsed = time.time() - start

    rate = len(articles) / (elapsed / 60)
    print(f'评分速度: {rate:.1f} 条/分钟')
```

**验收标准：**
- [ ] 采集速度达到目标
- [ ] 评分速度达到目标
- [ ] 成本在预算内

**责任人：** 我
**截止时间：** Day 4

---

### PHASE E: 生产部署准备（Day 4-5）

#### E1: 修复小bug和优化 [P2] ⏱️ 2小时

基于前面测试中发现的问题修复

**可能的问题：**
- 特殊字符处理
- 超长内容处理
- 网络超时重试
- 数据库连接池

#### E2: 提交代码 [P2] ⏱️ 1小时

```bash
# 检查状态
git status

# 添加所有改动
git add .

# 提交
git commit -m "feat: complete end-to-end system with real data verification

- Expand data sources from 3 to 20+ sources
- Fix 10 unscored articles
- Implement full content extraction from feeds
- Add author metadata extraction
- Verify Celery automation tasks
- Complete end-to-end workflow testing
- Add performance benchmarks
- All tests passing (>85% coverage target)
"

# 推送
git push origin main
```

---

## 📈 进度追踪

| 阶段 | 开始 | 截止 | 状态 | 完成度 |
|------|------|------|------|--------|
| **A: 诊断修复** | D1 | D2 | ⏳ | 0% |
| **B: 数据源扩展** | D1 | D3 | ⏳ | 0% |
| **C: 内容质量** | D2 | D4 | ⏳ | 0% |
| **D: 系统验证** | D3 | D5 | ⏳ | 0% |
| **E: 生产准备** | D4 | D5 | ⏳ | 0% |

---

## ✅ 最终验收标准

完成本计划后，系统应该：

- [ ] 采集>100条真实新闻（代表100+条/6小时能力）
- [ ] 数据源>20个（朝50个目标迈进）
- [ ] 评分成功率>95%
- [ ] Content平均>300字符
- [ ] Author填充率>80%
- [ ] Celery任务正常定时运行
- [ ] 端到端流程完整运行
- [ ] 所有代码测试通过
- [ ] 文档完整更新

---

## 📞 需要支持

如有以下问题，请立即反馈：

1. **OpenAI API key问题** - 使用不了API
2. **数据库连接问题** - 无法连接到数据库
3. **源失败问题** - 源无法采集内容
4. **其他阻塞** - 任何影响进度的问题

---

**文档版本：** 1.0
**最后更新：** 2025-11-02
**执行人：** Claude Code
**审核人：** 待审核
