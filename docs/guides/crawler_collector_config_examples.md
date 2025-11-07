# Crawler Collector Configuration Examples

本文档提供CrawlerCollector的配置示例，用于从各类网站采集内容。

## 📋 配置说明

CrawlerCollector使用CSS选择器从网页提取内容，配置存储在`data_sources`表的`config`字段（JSONB类型）。

### 核心配置项

```json
{
  "list_url": "https://example.com/news",
  "list_selector": ".news-item",
  "title_selector": ".title",
  "url_selector": "a[href]",
  "date_selector": ".date",
  "content_selector": ".article-content",
  "author_selector": ".author",
  "fetch_detail": true,
  "use_newspaper": true,
  "pagination": {
    "enabled": true,
    "type": "url_param",
    "param_name": "page",
    "start": 1,
    "max_pages": 5
  }
}
```

---

## 🎯 配置示例

### 示例1：简单列表页（无分页）

适用于：新闻站首页、博客最新文章

```json
{
  "list_url": "https://techblog.example.com/latest",
  "list_selector": "article.post",
  "title_selector": "h2.post-title",
  "url_selector": "a.post-link",
  "date_selector": "time",
  "author_selector": ".author-name",
  "fetch_detail": true,
  "use_newspaper": true
}
```

**SQL插入示例：**
```sql
INSERT INTO data_sources (name, type, url, config, is_enabled, priority)
VALUES (
  'Tech Blog',
  'crawler',
  'https://techblog.example.com',
  '{
    "list_url": "https://techblog.example.com/latest",
    "list_selector": "article.post",
    "title_selector": "h2.post-title",
    "url_selector": "a.post-link",
    "date_selector": "time",
    "author_selector": ".author-name",
    "fetch_detail": true,
    "use_newspaper": true
  }'::jsonb,
  true,
  50
);
```

---

### 示例2：URL参数分页

适用于：大多数新闻站、论坛

```json
{
  "list_url": "https://news.example.com/ai",
  "list_selector": ".news-list .item",
  "title_selector": "h3.title",
  "url_selector": "a.link[href]",
  "date_selector": "span.publish-time",
  "content_selector": ".article-body",
  "pagination": {
    "enabled": true,
    "type": "url_param",
    "param_name": "page",
    "start": 1,
    "max_pages": 3
  },
  "fetch_detail": true,
  "use_newspaper": false
}
```

**说明：**
- `type: "url_param"` - 通过URL参数分页（如 ?page=1, ?page=2）
- `param_name: "page"` - 参数名称
- `start: 1` - 起始页码
- `max_pages: 3` - 最多爬取3页

**生成的URLs：**
```
https://news.example.com/ai?page=1
https://news.example.com/ai?page=2
https://news.example.com/ai?page=3
```

---

### 示例3："下一页"链接分页

适用于：传统论坛、某些新闻站

```json
{
  "list_url": "https://forum.example.com/ai-news",
  "list_selector": ".topic-row",
  "title_selector": ".topic-title a",
  "url_selector": ".topic-title a",
  "date_selector": ".topic-date",
  "author_selector": ".topic-author",
  "pagination": {
    "enabled": true,
    "type": "next_link",
    "next_selector": ".pagination .next-page",
    "max_pages": 5
  },
  "fetch_detail": true
}
```

**说明：**
- `type: "next_link"` - 通过"下一页"链接分页
- `next_selector` - "下一页"链接的CSS选择器
- 自动跟随链接直到没有"下一页"或达到max_pages

---

### 示例4：只爬列表页（不抓取详情）

适用于：列表页已有完整摘要

```json
{
  "list_url": "https://brief.example.com/ai-news",
  "list_selector": ".news-card",
  "title_selector": ".card-title",
  "url_selector": "a.read-more",
  "date_selector": ".card-date",
  "content_selector": ".card-summary",
  "fetch_detail": false,
  "use_newspaper": false
}
```

**说明：**
- `fetch_detail: false` - 不抓取详情页
- `content_selector` - 直接从列表项提取摘要
- 适用于列表页已包含足够内容的情况

---

### 示例5：使用newspaper3k智能提取

适用于：复杂页面结构、难以定位CSS选择器

```json
{
  "list_url": "https://complex-site.example.com/articles",
  "list_selector": ".article-item",
  "title_selector": "h2",
  "url_selector": "a",
  "date_selector": "time",
  "fetch_detail": true,
  "use_newspaper": true
}
```

**说明：**
- `use_newspaper: true` - 使用newspaper3k自动提取正文
- 无需配置 `content_selector`
- 自动识别正文、过滤广告和导航

---

### 示例6：复杂选择器

适用于：复杂HTML结构

```json
{
  "list_url": "https://complex.example.com/news",
  "list_selector": "div.container > div.row > div.col-md-8 > article",
  "title_selector": "header > h1.entry-title",
  "url_selector": "header > h1.entry-title > a[href]",
  "date_selector": "div.entry-meta time[datetime]",
  "author_selector": "span.author.vcard a",
  "content_selector": "div.entry-content",
  "pagination": {
    "enabled": true,
    "type": "url_param",
    "param_name": "paged",
    "start": 1,
    "max_pages": 2
  }
}
```

---

## 🔧 选择器调试技巧

### 1. 使用浏览器开发者工具

```javascript
// 在浏览器控制台测试选择器
document.querySelectorAll('.news-item').length
document.querySelector('.news-item .title').textContent
```

### 2. 验证选择器

```python
# test_selectors.py
from bs4 import BeautifulSoup
import requests

url = "https://example.com/news"
html = requests.get(url).text
soup = BeautifulSoup(html, 'html.parser')

# 测试列表选择器
items = soup.select('.news-item')
print(f"Found {len(items)} items")

# 测试标题选择器
for item in items[:3]:
    title = item.select_one('.title')
    print(f"Title: {title.get_text() if title else 'NOT FOUND'}")
```

### 3. 常用选择器模式

```css
/* 类选择器 */
.article-item

/* ID选择器 */
#main-content

/* 标签选择器 */
article

/* 属性选择器 */
a[href]
time[datetime]

/* 子选择器 */
div.container > article

/* 后代选择器 */
div.post h2.title

/* 伪类选择器 */
li:first-child
a:not(.external)

/* 组合选择器 */
h1.title, h2.title, h3.title
```

---

## 📊 完整配置示例（生产级）

```json
{
  "list_url": "https://ai-news.example.com/latest",
  "list_selector": "article.news-card",
  "title_selector": "h2.card-title",
  "url_selector": "a.card-link[href]",
  "date_selector": "time.publish-date[datetime]",
  "author_selector": "span.author-name",
  "content_selector": "div.article-body",
  "fetch_detail": true,
  "use_newspaper": true,
  "pagination": {
    "enabled": true,
    "type": "url_param",
    "param_name": "page",
    "start": 1,
    "max_pages": 5
  }
}
```

**数据源完整记录示例：**
```sql
INSERT INTO data_sources (
    name,
    type,
    url,
    priority,
    is_enabled,
    max_items_per_run,
    config,
    default_author,
    tags,
    description
) VALUES (
    'AI News Hub',
    'crawler',
    'https://ai-news.example.com',
    70,
    true,
    50,
    '{
      "list_url": "https://ai-news.example.com/latest",
      "list_selector": "article.news-card",
      "title_selector": "h2.card-title",
      "url_selector": "a.card-link[href]",
      "date_selector": "time.publish-date[datetime]",
      "author_selector": "span.author-name",
      "content_selector": "div.article-body",
      "fetch_detail": true,
      "use_newspaper": true,
      "pagination": {
        "enabled": true,
        "type": "url_param",
        "param_name": "page",
        "start": 1,
        "max_pages": 5
      }
    }'::jsonb,
    'AI News Hub',
    ARRAY['ai', 'machine-learning', 'technology'],
    'Leading AI news aggregator with comprehensive coverage'
);
```

---

## 🧪 测试配置

### 快速测试脚本

```python
# scripts/test_crawler_config.py
import asyncio
from src.database import SessionLocal
from src.models import DataSource
from src.services.collection.crawler_collector import CrawlerCollector

async def test():
    # 创建测试数据源
    source = DataSource(
        id=999,
        name="Test Crawler",
        type="crawler",
        url="https://example.com",
        config={
            "list_url": "https://example.com/news",
            "list_selector": ".news-item",
            "title_selector": ".title",
            "url_selector": "a[href]",
            "fetch_detail": False
        },
        is_enabled=True
    )

    collector = CrawlerCollector(source)
    articles = await collector.collect()

    print(f"Collected {len(articles)} articles")
    for article in articles[:3]:
        print(f"- {article['title']}")
        print(f"  URL: {article['url']}")

asyncio.run(test())
```

---

## ⚠️ 注意事项

### 1. 反爬虫策略

大多数网站有反爬虫措施：
- 使用合理的User-Agent（已内置）
- 添加请求延迟（已内置1秒延迟）
- 避免过度爬取（控制max_pages和max_items_per_run）

### 2. 选择器稳定性

- 优先使用语义化class（如 `.article`, `.post-title`）
- 避免使用生成的class（如 `.css-1xa2k3j`）
- 定期检查配置是否失效

### 3. 性能考虑

```json
{
  "pagination": {
    "max_pages": 3  // 不要设置太大，避免采集时间过长
  }
}
```

### 4. 内容质量

- 优先使用 `use_newspaper: true` 获取高质量内容
- 如果newspaper3k失败，会自动降级到CSS选择器
- 确保 `content_selector` 作为备用方案

---

## 📚 参考资源

- [CSS选择器教程](https://www.w3schools.com/cssref/css_selectors.asp)
- [BeautifulSoup文档](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [newspaper3k文档](https://newspaper.readthedocs.io/)

---

**更新日期：** 2025-11-07
**版本：** 1.0
