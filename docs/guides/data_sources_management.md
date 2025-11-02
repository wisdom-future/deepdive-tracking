# 新闻数据源管理指南

## 概述

DeepDive Tracking 支持从多个数据源采集新闻：

- **RSS Feed** - 最常用，支持所有提供RSS的网站
- **Web Crawler** - 网页爬虫，支持复杂的数据提取
- **API** - 直接调用 API 接口获取数据
- **Twitter** - 社交媒体新闻源
- **Email** - 通过邮件接收内容

## 数据源配置位置

数据源配置存储在数据库中的 `data_sources` 表，包含以下信息：

### 数据源表字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | INT | 主键 | 1 |
| `name` | VARCHAR | 数据源名称 | OpenAI Blog |
| `type` | VARCHAR | 数据源类型 | rss / crawler / api / twitter / email |
| `url` | VARCHAR | URL 或 API 端点 | https://openai.com/blog/rss.xml |
| `priority` | INT | 优先级 (1-10) | 10 (越高越优先) |
| `refresh_interval` | INT | 刷新间隔 (分钟) | 30 |
| `max_items_per_run` | INT | 单次最多采集条数 | 50 |
| `is_enabled` | BOOLEAN | 是否启用 | true / false |
| `last_check_at` | DATETIME | 最后检查时间 | 2025-01-02 10:30:00 |
| `last_success_at` | DATETIME | 最后成功时间 | 2025-01-02 10:35:00 |
| `last_error` | TEXT | 最后的错误信息 | Connection timeout |
| `error_count` | INT | 累积错误次数 | 0 |
| `consecutive_failures` | INT | 连续失败次数 | 0 |
| `tags` | JSON | 标签列表 | ["ai", "llm"] |
| `default_author` | VARCHAR | 默认作者 | OpenAI |
| `description` | TEXT | 数据源描述 | OpenAI's official blog |

## 查看数据源

### 方法 1: 使用脚本查看

```bash
python scripts/show_data_sources.py
```

这将显示：
- 所有数据源的配置
- 启用/禁用状态
- 采集统计信息
- 错误日志

### 方法 2: 直接查询数据库

```bash
# 使用 SQLite
sqlite3 data/db/deepdive_tracking.db "SELECT id, name, type, url, is_enabled FROM data_sources;"

# 使用 PostgreSQL (如果配置)
psql -d deepdive_tracking -c "SELECT id, name, type, url, is_enabled FROM data_sources;"
```

### 方法 3: Python 代码查询

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models import DataSource

settings = get_settings()
engine = create_engine(settings.database_url)
Session = sessionmaker(bind=engine)
session = Session()

# 查询所有数据源
sources = session.query(DataSource).all()

for source in sources:
    print(f"{source.name}: {source.type} - {'启用' if source.is_enabled else '禁用'}")
```

## 添加新的数据源

### 方法 1: Python 代码添加

```python
from src.models import DataSource
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 创建新的数据源
new_source = DataSource(
    name="TechCrunch AI",
    type="rss",
    url="https://techcrunch.com/feed/?tag=ai",
    priority=8,
    refresh_interval=30,
    max_items_per_run=20,
    is_enabled=True,
    description="TechCrunch AI and ML news feed",
    tags=["ai", "tech", "news"]
)

# 添加到数据库
session.add(new_source)
session.commit()
print(f"✓ 数据源已添加: {new_source.name}")
```

### 方法 2: 数据库 SQL 添加

```sql
INSERT INTO data_sources (
    name, type, url, priority, refresh_interval,
    max_items_per_run, is_enabled, description
) VALUES (
    'Hugging Face Blog',
    'rss',
    'https://huggingface.co/blog/feed.xml',
    9,
    30,
    15,
    true,
    'Hugging Face AI research and product updates'
);
```

## 修改数据源

### 启用/禁用数据源

```python
source = session.query(DataSource).filter_by(name="OpenAI Blog").first()
source.is_enabled = False  # 禁用
session.commit()
```

### 修改采集参数

```python
source = session.query(DataSource).filter_by(name="OpenAI Blog").first()
source.priority = 10           # 最高优先级
source.refresh_interval = 15   # 更频繁的采集
source.max_items_per_run = 30  # 增加单次采集数量
session.commit()
```

## 常见的数据源配置

### 1. RSS Feed 类型

这是最常见的类型，支持大多数新闻网站。

**配置示例：**

| 数据源 | URL | 优先级 | 刷新间隔 |
|--------|-----|--------|---------|
| OpenAI Blog | https://openai.com/blog/rss.xml | 10 | 30 |
| Anthropic News | https://www.anthropic.com/news/rss.xml | 10 | 30 |
| HuggingFace Blog | https://huggingface.co/blog/feed.xml | 9 | 30 |
| ArXiv AI Papers | https://export.arxiv.org/rss/cs.AI | 8 | 60 |
| TechCrunch AI | https://techcrunch.com/feed/?tag=ai | 7 | 30 |
| VentureBeat AI | https://venturebeat.com/feed/ | 7 | 30 |
| The Verge | https://www.theverge.com/rss/index.xml | 6 | 120 |

### 2. Crawler 类型 (网页爬虫)

用于从网站直接提取信息。

**配置示例：**

```python
DataSource(
    name="Example News Website",
    type="crawler",
    url="https://example.com/news",
    priority=5,
    refresh_interval=60,
    is_enabled=True,
    css_selectors={
        "title": "h1.article-title",
        "content": "div.article-content",
        "author": "span.author-name",
        "published_at": "time.publish-date"
    }
)
```

### 3. API 类型

调用 API 接口获取数据。

**配置示例：**

```python
DataSource(
    name="News API",
    type="api",
    url="https://newsapi.org/v2/everything",
    priority=7,
    refresh_interval=30,
    is_enabled=True,
    params={
        "q": "AI OR artificial intelligence",
        "sortBy": "publishedAt",
        "apiKey": "your_api_key"
    },
    headers={
        "User-Agent": "DeepDive Tracking"
    }
)
```

### 4. Twitter 类型

从 Twitter/X 获取推文。

**配置示例：**

```python
DataSource(
    name="OpenAI Twitter",
    type="twitter",
    url="https://twitter.com/OpenAI",
    priority=6,
    refresh_interval=15,
    is_enabled=True,
    auth_type="bearer",
    auth_token="your_twitter_api_token"
)
```

## 采集流程

### 1. 采集初始化

系统启动采集时会：
- 查询所有启用的数据源 (`is_enabled = true`)
- 按优先级排序
- 逐个采集

### 2. 采集执行

对于每个数据源：
- 根据类型选择相应的采集器 (RSSCollector, CrawlerCollector 等)
- 获取最新内容
- 去重 (使用 SimHash 算法)
- 保存到 `raw_news` 表

### 3. 采集结果

采集完成后，数据源的以下字段会被更新：
- `last_check_at`: 检查时间
- `last_success_at`: 成功时间
- `last_error`: 错误信息 (如有)
- `error_count`: 错误计数
- `consecutive_failures`: 连续失败计数

## 采集命令

### 运行采集

```bash
# 采集一次
python scripts/01-collection/collect_news.py

# 或使用完整的 E2E 测试
python scripts/run_complete_e2e_test.py 10

# 诊断数据源配置
python scripts/01-collection/diagnose_sources.py
```

### 查看采集结果

```bash
# 显示最新采集的新闻
python scripts/show-top-news.py
```

## 数据源故障排查

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 数据源无法连接 | 网络问题或 URL 错误 | 检查 URL 和网络连接 |
| 采集数据为空 | RSS URL 失效或格式不支持 | 验证 RSS URL 有效性 |
| 采集到重复新闻 | 去重算法失效 | 检查去重配置 |
| 某个数据源持续失败 | API 限流或认证过期 | 重新配置认证令牌 |
| 采集速度慢 | 并发数不够或源响应慢 | 增加并发数或调整超时时间 |

### 调试数据源

```python
# 测试单个数据源
from src.services.collection import RSSCollector
from src.models import DataSource

source = session.query(DataSource).filter_by(name="OpenAI Blog").first()
collector = RSSCollector(source)

try:
    items = asyncio.run(collector.collect())
    print(f"✓ 采集成功: {len(items)} 条新闻")
    for item in items[:3]:
        print(f"  - {item['title']}")
except Exception as e:
    print(f"✗ 采集失败: {str(e)}")
```

## 最佳实践

### 1. 优先级设置

```
10: 官方资讯 (OpenAI, Anthropic, Google)
9:  重要科技媒体 (TechCrunch, VentureBeat)
8:  学术资源 (ArXiv)
7:  综合媒体 (The Verge)
5:  第二类渠道
```

### 2. 刷新间隔

```
- 高频内容 (Twitter): 15-30 分钟
- 定期更新 (Blog): 30-60 分钟
- 低频更新 (周刊): 12-24 小时
- 学术资源 (ArXiv): 24+ 小时
```

### 3. 采集数量

```
- 高优先级: 20-50 条
- 中等优先级: 10-30 条
- 低优先级: 5-15 条
```

### 4. 定期维护

```bash
# 定期检查数据源状态
python scripts/show_data_sources.py

# 禁用持续失败的数据源
# UPDATE data_sources SET is_enabled = false WHERE consecutive_failures > 5;

# 重置错误计数
# UPDATE data_sources SET error_count = 0, consecutive_failures = 0;
```

## 数据源扩展

### 添加新的采集器类型

1. 创建新的采集器类 (继承 `BaseCollector`)
2. 在 `CollectionManager._get_collector()` 中注册
3. 定义对应的 `type` 值

**示例：**

```python
# src/services/collection/custom_collector.py
from src.services.collection.base_collector import BaseCollector

class CustomCollector(BaseCollector):
    async def collect(self):
        """采集实现"""
        pass
```

## 总结

数据源配置允许：

✅ 灵活添加/删除数据源
✅ 动态启用/禁用数据源
✅ 调整采集参数优化性能
✅ 追踪采集统计和错误
✅ 支持多种数据源类型

通过合理配置数据源，可以构建覆盖全面的新闻采集系统！
