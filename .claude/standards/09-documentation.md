# 文档规范

**版本：** 1.0
**强制级别：** 🔴 MUST
**更新日期：** 2025-11-02

---

## 核心原则

```
✅ 文档即代码
✅ 文档要保持最新
✅ 文档应该准确完整
✅ 文档易于搜索和理解
✅ 代码和文档同步更新
```

---

## 代码注释规范

### 🔴 MUST - 严格遵守

1. **模块级注释（Docstring）**
   ```python
   """内容管理模块。

   负责内容的生命周期管理，包括创建、验证、编辑和发布。

   Key Classes:
       ContentManager: 主要的内容管理服务
       ContentValidator: 内容验证器

   Example:
       >>> from src.services.content import ContentManager
       >>> manager = ContentManager(db_session)
       >>> content = manager.create(news_id=123)
   """
   ```

2. **类级注释**
   ```python
   class ContentManager:
       """内容管理服务。

       负责内容的创建、更新、删除和查询。

       Attributes:
           db_session: 数据库会话
           cache: 缓存客户端
           logger: 日志对象
       """
   ```

3. **函数级注释（Google风格）**
   ```python
   def create_content(
       news_id: int,
       override_category: Optional[str] = None,
   ) -> Content:
       """从新闻创建内容。

       参数说明

       Args:
           news_id: 新闻ID，必须存在
           override_category: 可选，覆盖AI预测

       Returns:
           创建的Content对象

       Raises:
           NewsNotFoundError: 如果新闻不存在
           AIProcessingError: 如果AI处理失败

       Example:
           >>> content = create_content(123)
           >>> print(content.title)
           'OpenAI发布GPT-4'
       """
   ```

4. **只注释"为什么"，不注释"是什么"**
   ```python
   ✅ # 使用Simhash而不是TF-IDF因为对大文本更快
      is_duplicate = check_simhash(content)

   ✅ # 重试3次是为了应对API的临时超时
      for attempt in range(3):
          try:
              result = ai_service.process(content)
              break
          except TimeoutError:
              if attempt == 2:
                  raise

   ❌ # 检查是否重复
      is_duplicate = check_simhash(content)

   ❌ # 循环遍历items
      for item in items:
          process(item)
   ```

5. **复杂算法前的注释**
   ```python
   # 计算余弦相似度判重
   # 阈值0.85为重复标准（>0.85认为重复）
   # 这个阈值是通过1000条测试数据优化得出的
   similarity = compute_cosine_similarity(text1, text2)
   if similarity > 0.85:
       is_duplicate = True
   ```

6. **TODO/FIXME/HACK 注释**
   ```python
   # TODO: 后续优化数据库查询性能 (#123)
   # FIXME: 需要处理超长标题的截断
   # HACK: 临时解决方案，等待API更新后重构
   ```

### 🟡 SHOULD - 强烈建议

1. **在关键业务逻辑处添加说明**
   ```python
   # 根据业务规则，score >= 80分才能自动发布
   # 低于80分的内容需要人工审核
   if content.score >= 80:
       publish_content(content)
   else:
       queue_for_review(content)
   ```

2. **注释易于维护**
   ```python
   ✅ # 使用3作为重试次数，参考 RETRY_CONFIG常量
      for attempt in range(RETRY_COUNT):

   ❌ # 使用3
      for attempt in range(3):  (3是什么意思？)
   ```

---

## Docstring 格式详解

### Google 风格 Docstring

```python
def function_with_pep484_type_hints(
        param1: int,
        param2: str = "default"
) -> bool:
    """一行总结。

    可选的更详细的说明，可以跨越多行。
    可以包含更多的上下文和用例。

    Args:
        param1: 第一个参数的说明
        param2: 第二个参数的说明，默认为"default"

    Returns:
        返回值的说明。如果函数不返回任何内容，可以省略此部分。

    Raises:
        ValueError: 如果param1为负数
        TypeError: 如果param2不是字符串

    Example:
        >>> function_with_pep484_type_hints(5)
        True
        >>> function_with_pep484_type_hints(-5)
        Traceback (most recent call last):
        ...
        ValueError: param1 must be positive
    """
    pass
```

---

## 技术文档规范

### 🔴 MUST - 严格遵守

1. **文档位置**
   ```
   docs/
   ├── README.md                    (项目首页)
   ├── CONTRIBUTING.md              (贡献指南)
   ├── product/                     (产品文档)
   │   └── requirements.md
   ├── tech/                        (技术文档)
   │   ├── architecture.md
   │   ├── database-schema.md
   │   └── api-design.md
   ├── content/                     (内容管理)
   └── operations/                  (运维文档)
   ```

2. **README.md 格式**
   ```markdown
   # 项目名称

   一句话描述项目是什么

   ## Features
   - 功能1
   - 功能2
   - 功能3

   ## Quick Start
   ```bash
   git clone ...
   cd ...
   make setup
   make run
   ```

   ## Documentation
   - [API](docs/API.md)
   - [Architecture](docs/Architecture.md)

   ## Contributing
   See [CONTRIBUTING.md](CONTRIBUTING.md)

   ## License
   MIT
   ```

3. **API 文档**
   ```markdown
   # API Reference

   ## GET /api/v1/contents

   获取内容列表

   ### Parameters
   - `limit` (optional, int): 最多返回条数，默认10，最多100
   - `offset` (optional, int): 偏移量，默认0
   - `status` (optional, string): 过滤状态，可选值：draft, published, archived

   ### Response
   ```json
   {
       "code": 0,
       "message": "success",
       "data": {
           "items": [...],
           "total": 100,
           "limit": 10,
           "offset": 0
       }
   }
   ```

   ### Example
   ```bash
   curl -X GET "http://localhost:8000/api/v1/contents?limit=10"
   ```

   ## POST /api/v1/contents

   创建新内容

   ### Request Body
   ```json
   {
       "title": "...",
       "body": "...",
       "category": "AI"
   }
   ```

   ### Response
   201 Created with created content object
   ```

4. **架构文档**
   ```markdown
   # System Architecture

   ## Overview
   系统整体设计说明

   ## Components
   描述各个组件及其职责

   ## Data Flow
   数据流转说明

   ## Deployment
   部署架构图
   ```

5. **故障排查文档**
   ```markdown
   # Troubleshooting

   ## Issue: AI Service Timeout

   ### Symptoms
   - 内容处理超时
   - 日志中出现 "AI service timeout" 错误

   ### Root Cause
   大文本处理超过了30秒的超时设置

   ### Solution
   1. 增加超时时间：`AI_SERVICE_TIMEOUT=60`
   2. 使用流式处理：`enable_streaming=true`
   3. 拆分大文本

   ### Prevention
   - 监控AI服务响应时间
   - 定期优化模型性能
   ```

### 🟡 SHOULD - 强烈建议

1. **使用 Markdown 格式**
   ```markdown
   # 标题一级
   ## 标题二级
   ### 标题三级

   **加粗**
   *斜体*
   `代码`

   ```python
   # 代码块
   def function():
       pass
   ```

   - 列表项1
   - 列表项2

   > 引用
   ```

2. **包含示例和用例**
   ```markdown
   ## Usage Example

   ```python
   from src.services.content import ContentManager

   manager = ContentManager(db_session)
   content = manager.create(news_id=123)
   print(content.title)
   ```
   ```

3. **定期更新文档**
   ```
   - 功能实现时同步更新文档
   - API改动时更新API文档
   - 架构变化时更新架构文档
   ```

---

## CHANGELOG 规范

### 🔴 MUST - 严格遵守

1. **CHANGELOG.md 格式**
   ```markdown
   # Changelog

   All notable changes to this project will be documented in this file.

   ## [1.0.0] - 2025-11-02

   ### Added
   - Support for RSS feed collection
   - AI scoring system with 8 categories
   - Multi-channel publishing (WeChat, Xiaohongshu)

   ### Changed
   - Improved database query performance by 40%
   - Refactored content validation logic

   ### Fixed
   - Fixed timeout issue in AI service
   - Fixed duplicate detection algorithm

   ### Deprecated
   - Old API endpoints (will be removed in v2.0.0)

   ### Removed
   - Support for old configuration format

   ### Security
   - Fixed SQL injection vulnerability in search
   - Updated dependencies for security patches

   ## [0.9.0] - 2025-10-01

   ### Added
   - Beta release with core features
   ```

2. **每个发布版本都要更新 CHANGELOG**
   ```
   发布前必须更新CHANGELOG
   包括Added, Changed, Fixed, Removed等所有改动
   ```

---

## 代码示例文档

### 🔴 MUST - 严格遵守

1. **包含完整可运行的示例**
   ```python
   """
   Example: How to create and publish content

   This example demonstrates the complete workflow from creating
   raw news to publishing it on multiple channels.

   Requirements:
       - Database must be initialized
       - AI service must be running
       - WeChat API credentials configured
   """

   from src.models import News, Content
   from src.services.content import ContentManager
   from src.services.publishing import PublishingService

   # 1. Create raw news (assuming it exists)
   news = get_news_by_id(123)

   # 2. Create content from news
   manager = ContentManager(db_session)
   content = manager.create(news_id=news.id)
   print(f"Created content: {content.id}")

   # 3. Publish to WeChat
   publisher = PublishingService(db_session)
   result = publisher.publish(content.id, channel="wechat")
   print(f"Published to WeChat: {result.status}")
   ```

---

## 文档检查清单

提交代码前检查：

- [ ] 所有新函数都有 docstring
- [ ] 所有新类都有 docstring
- [ ] 复杂逻辑前有注释说明
- [ ] Docstring 遵循 Google 风格
- [ ] 包含 Args, Returns, Raises 说明
- [ ] Docstring 中有使用示例
- [ ] 注释解释"为什么"而不是"是什么"
- [ ] 没有过时或错误的注释
- [ ] 相关技术文档已更新
- [ ] CHANGELOG.md 已更新

---

**记住：** 好的文档是代码质量的体现。文档越清晰，代码就越易于维护和使用。

