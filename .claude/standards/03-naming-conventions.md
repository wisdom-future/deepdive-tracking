# 命名规范

**版本：** 1.0
**强制级别：** 🔴 MUST
**更新日期：** 2025-11-02

---

## 核心原则

```
✅ 清晰和一致 > 简洁
✅ 名字应该表达意图和用途
✅ 避免歧义和缩写
✅ 保持团队命名风格统一
```

---

## 文件和目录命名

### 🔴 MUST - 严格遵守

1. **源代码文件**
   ```
   ✅ content_manager.py
   ✅ rss_collector.py
   ✅ ai_processor.py
   ❌ ContentManager.py (错误：应该是snake_case)
   ❌ content-manager.py (错误：应该是snake_case，不是kebab-case)
   ❌ contentManager.py (错误：camelCase不允许)
   ```

2. **测试文件**
   ```
   ✅ test_content_manager.py
   ✅ test_rss_collector.py
   ✅ test_ai_processor.py
   ❌ ContentManagerTest.py
   ❌ content_manager_test.py (测试文件必须以test_开头)
   ```

3. **目录名**
   ```
   ✅ src/services/collection/
   ✅ src/models/
   ✅ tests/unit/services/
   ❌ src/Services/ (应该是小写)
   ❌ src/Collection/ (应该是小写)
   ```

4. **配置文件**
   ```
   ✅ .env.example
   ✅ pyproject.toml
   ✅ .pre-commit-config.yaml
   ❌ config.py (配置应该用环境变量或toml)
   ```

5. **Markdown 文档文件**
   ```
   ✅ 00-overview.md
   ✅ quick-reference.md
   ✅ system-design-summary.md
   ✅ architecture-diagrams.md
   ✅ README.md
   ❌ 00_overview.md (文档用kebab-case，不是snake_case)
   ❌ QuickReference.md (文档用小写)
   ```

   **说明：** Markdown 文档文件使用 `kebab-case`（间隔号）而不是 `snake_case`
   - 更易读：`quick-reference` vs `quick_reference`
   - 符合 Web 标准：GitHub, GitLab, 文档网站都采用这种格式
   - 更适合 URL：`/docs/quick-reference` 比 `/docs/quick_reference` 看起来更自然

### 🟡 SHOULD - 强烈建议

1. **文件名应该反映功能**
   - `user_manager.py` 而不是 `um.py`
   - `database_connection.py` 而不是 `db.py`

2. **相关文件使用相同前缀**
   ```
   ✅ content_manager.py
      test_content_manager.py
      (有明确的对应关系)
   ```

---

## 类和接口命名

### 🔴 MUST - 严格遵守

1. **类名使用 PascalCase**
   ```python
   ✅ class ContentManager:
   ✅ class RSSCollector:
   ✅ class AIProcessor:
   ❌ class content_manager:
   ❌ class ContentManger (拼写错误)
   ```

2. **抽象类和接口**
   ```python
   ✅ class BaseCollector:
   ✅ class IDataSource:
   ✅ class AbstractProcessor:
   ❌ class Collector (不清晰是否抽象)
   ```

3. **异常类名**
   ```python
   ✅ class ContentNotFoundError(Exception):
   ✅ class InvalidConfigError(Exception):
   ✅ class DatabaseConnectionError(Exception):
   ❌ class ErrorContent (顺序错误)
   ❌ class Error (太通用)
   ```

4. **类名应该是名词，表达实体或概念**
   ```python
   ✅ class NewsItem:
   ✅ class PublishingSchedule:
   ✅ class ReviewQueue:
   ❌ class ProcessNews (动词开头)
   ❌ class GettingData (动词开头)
   ```

### 🟡 SHOULD - 强烈建议

1. **相关的类放在同一个文件中**
   ```python
   # content_manager.py
   class ContentManager:
       pass

   class ContentValidator:
       pass

   class ContentFormatter:
       pass
   ```

2. **类名长度3-30个字符**
   ```
   ✅ ContentManager (14个字符)
   ✅ RSSCollector (12个字符)
   ❌ C (太短，不清晰)
   ❌ VeryLongDescriptiveContentManagementProcessorClass (太长)
   ```

---

## 函数和方法命名

### 🔴 MUST - 严格遵守

1. **函数名使用 snake_case**
   ```python
   ✅ def get_content(content_id: int) -> Content:
   ✅ def create_content_from_news(news_id: int) -> Content:
   ✅ def validate_content_format(content: Content) -> bool:
   ❌ def getContent():
   ❌ def GetContent():
   ❌ def get-content():
   ```

2. **函数名应该是动词或动词短语**
   ```python
   ✅ def fetch_data():
   ✅ def validate_input():
   ✅ def publish_to_wechat():
   ✅ def is_duplicate():
   ✅ def has_valid_license():
   ❌ def data():
   ❌ def input():
   ❌ def content_manager():
   ```

3. **布尔值返回的函数使用 is_/has_/can_ 前缀**
   ```python
   ✅ def is_valid():
   ✅ def is_duplicate():
   ✅ def has_permission():
   ✅ def can_publish():
   ❌ def valid():
   ❌ def duplicate():
   ```

4. **异步函数与普通函数命名一致**
   ```python
   ✅ async def fetch_data():
   ✅ async def process_content():
   (不需要特殊前缀)
   ```

5. **私有方法使用下划线前缀**
   ```python
   class ContentManager:
       def public_method(self):
           pass

       def _private_method(self):
           pass

       def __very_private_method(self):
           pass
   ```

### 🟡 SHOULD - 强烈建议

1. **函数名长度3-40个字符**
   ```
   ✅ get_content()
   ✅ validate_email_format()
   ❌ f()
   ❌ very_long_function_name_that_does_something_very_specific()
   ```

2. **相关的函数使用相同的动词**
   ```python
   ✅ get_content()
      get_user()
      get_config()

   ❌ get_content()
      fetch_user()
      retrieve_config()
   ```

---

## 变量和常量命名

### 🔴 MUST - 严格遵守

1. **本地变量和参数使用 snake_case**
   ```python
   ✅ user_id = 123
   ✅ content_list = []
   ✅ is_active = True
   ✅ max_retry_count = 3
   ❌ userId = 123
   ❌ contentList = []
   ❌ IsActive = True
   ```

2. **常量使用 UPPER_CASE**
   ```python
   ✅ MAX_RETRY_COUNT = 3
   ✅ DEFAULT_TIMEOUT = 30
   ✅ BATCH_SIZE = 100
   ✅ API_BASE_URL = "https://api.example.com"
   ❌ max_retry_count = 3 (常量不能用snake_case)
   ❌ MaxRetryCount = 3 (常量不能用PascalCase)
   ```

3. **环境变量使用 UPPER_CASE**
   ```python
   ✅ API_KEY = getenv('OPENAI_API_KEY')
   ✅ DATABASE_URL = getenv('DATABASE_URL')
   ✅ LOG_LEVEL = getenv('LOG_LEVEL', 'INFO')
   ❌ api_key = getenv('api_key')
   ```

4. **布尔变量使用 is_/has_/can_ 前缀**
   ```python
   ✅ is_valid = True
   ✅ is_active = False
   ✅ has_permission = True
   ✅ can_publish = False
   ❌ valid = True
   ❌ active = False
   ```

5. **集合变量名应该复数**
   ```python
   ✅ users = []
   ✅ content_items = []
   ✅ error_messages = {}
   ❌ user = []
   ❌ content = []
   ```

### 🟡 SHOULD - 强烈建议

1. **变量名3-30个字符**
   ```
   ✅ user_id
   ✅ active_status
   ❌ x
   ❌ very_long_variable_name_that_is_descriptive_but_takes_forever_to_type
   ```

2. **单字母变量仅在循环中使用**
   ```python
   ✅ for i in range(10):
           print(i)

   ✅ for item in items:
           process(item)

   ❌ x = get_user_data()  (不允许)
   ```

3. **临时变量使用 tmp_ 前缀**
   ```python
   ✅ tmp_result = expensive_operation()
   ✅ tmp_list = []
   ```

---

## 数据库命名

### 🔴 MUST - 严格遵守

1. **表名使用 snake_case，复数形式**
   ```sql
   ✅ CREATE TABLE users (...)
   ✅ CREATE TABLE content_items (...)
   ✅ CREATE TABLE data_sources (...)
   ❌ CREATE TABLE User (...)
   ❌ CREATE TABLE user (单数)
   ❌ CREATE TABLE UserTable (...)
   ```

2. **列名使用 snake_case**
   ```sql
   ✅ CREATE TABLE users (
       id BIGINT,
       user_name VARCHAR(255),
       email_address VARCHAR(255),
       created_at TIMESTAMP,
       updated_at TIMESTAMP
   )
   ❌ CREATE TABLE users (
       ID,
       userName,
       EmailAddress,
       CreatedAt
   )
   ```

3. **主键命名规范**
   ```sql
   ✅ CREATE TABLE users (
       id BIGINT PRIMARY KEY,
       ...
   )
   ❌ CREATE TABLE users (
       user_id BIGINT PRIMARY KEY,  (除非有特殊原因)
       ...
   )
   ```

4. **外键命名规范**
   ```sql
   ✅ CREATE TABLE content_items (
       id BIGINT PRIMARY KEY,
       user_id BIGINT REFERENCES users(id),
       source_id BIGINT REFERENCES data_sources(id),
       ...
   )
   ❌ CREATE TABLE content_items (
       content_id BIGINT PRIMARY KEY,
       user BIGINT REFERENCES users(id),
       ...
   )
   ```

5. **索引命名规范**
   ```sql
   ✅ CREATE INDEX idx_users_email ON users(email_address)
   ✅ CREATE INDEX idx_content_items_source_id ON content_items(source_id)
   ✅ CREATE UNIQUE INDEX uq_users_email ON users(email_address)
   ❌ CREATE INDEX index1 ON users(email_address)
   ❌ CREATE INDEX users_email ON users(email_address)
   ```

6. **约束命名规范**
   ```sql
   ✅ CONSTRAINT fk_content_user FOREIGN KEY (user_id) REFERENCES users(id)
   ✅ CONSTRAINT ck_score_range CHECK (score >= 0 AND score <= 100)
   ✅ CONSTRAINT uq_email UNIQUE (email_address)
   ❌ CONSTRAINT fk1 FOREIGN KEY
   ❌ CONSTRAINT check1 CHECK
   ```

7. **字段类型和时间字段命名**
   ```sql
   ✅ created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   ✅ updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   ✅ deleted_at TIMESTAMP NULL
   ✅ published_at TIMESTAMP NULL
   ❌ create_date DATE
   ❌ createTime TIMESTAMP
   ```

### 🟡 SHOULD - 强烈建议

1. **表名长度4-30个字符**
   ```
   ✅ users (5个字符)
   ✅ content_items (13个字符)
   ❌ u (太短)
   ❌ very_long_table_name_that_describes_something (太长)
   ```

2. **避免歧义的表名**
   ```
   ✅ data_sources
   ✅ raw_news
   ✅ processed_news
   ❌ data (太通用)
   ❌ news (不清晰是原始还是处理过的)
   ```

---

## API路由命名

### 🔴 MUST - 严格遵守

1. **路由使用 kebab-case，全小写**
   ```
   ✅ GET    /api/v1/contents
   ✅ GET    /api/v1/contents/{id}
   ✅ GET    /api/v1/data-sources
   ✅ POST   /api/v1/admin/review/{id}/decision
   ✅ DELETE /api/v1/admin/sources/{id}
   ❌ GET    /api/v1/getContents
   ❌ GET    /api/v1/contents_all
   ❌ GET    /api/v1/Contents
   ```

2. **路由应该使用名词，不用动词**
   ```
   ✅ GET    /api/v1/contents
   ✅ POST   /api/v1/contents
   ✅ PUT    /api/v1/contents/{id}
   ✅ DELETE /api/v1/contents/{id}
   ❌ GET    /api/v1/get-contents
   ❌ POST   /api/v1/create-content
   ❌ PUT    /api/v1/update-content/{id}
   ```

3. **资源ID使用 {id} 或 {resource_id}**
   ```
   ✅ GET    /api/v1/contents/{id}
   ✅ GET    /api/v1/users/{user_id}
   ✅ GET    /api/v1/sources/{source_id}/items
   ❌ GET    /api/v1/contents/{content_id}
   ❌ GET    /api/v1/content/{contentId}
   ```

4. **子资源使用分层结构**
   ```
   ✅ GET    /api/v1/contents/{id}/reviews
   ✅ POST   /api/v1/contents/{id}/publish
   ✅ GET    /api/v1/sources/{id}/items
   ❌ GET    /api/v1/reviews-for-content/{id}
   ❌ GET    /api/v1/items-of-source/{id}
   ```

5. **版本隔离在路径中**
   ```
   ✅ /api/v1/contents
   ✅ /api/v2/contents
   ❌ /api/contents?version=1
   ❌ /api/v1.0/contents
   ```

### 🟡 SHOULD - 强烈建议

1. **使用RESTful约定**
   ```
   Collection:
   GET    /api/v1/contents          (列表)
   POST   /api/v1/contents          (创建)

   Item:
   GET    /api/v1/contents/{id}     (详情)
   PUT    /api/v1/contents/{id}     (更新)
   DELETE /api/v1/contents/{id}     (删除)

   Custom Action:
   POST   /api/v1/contents/{id}/publish  (自定义操作)
   ```

2. **路由应该反映业务实体**
   ```
   ✅ /api/v1/contents
      /api/v1/sources
      /api/v1/reviews
   ```

---

## Git 分支命名

### 🔴 MUST - 严格遵守

1. **分支名使用 kebab-case**
   ```
   ✅ feature/001-add-rss-parser
   ✅ bugfix/fix-timeout-error
   ✅ hotfix/critical-security-patch
   ✅ refactor/optimize-database-queries
   ❌ feature/addRssParser
   ❌ feature_add_rss_parser
   ❌ Feature/AddRssParser
   ```

2. **分支前缀规范**
   ```
   ✅ feature/      (新功能)
   ✅ bugfix/       (bug修复)
   ✅ hotfix/       (紧急修复)
   ✅ refactor/     (代码重构)
   ✅ docs/         (文档更新)
   ✅ test/         (测试相关)
   ✅ chore/        (杂务，依赖更新等)
   ❌ wip/          (Work in Progress不允许)
   ❌ temp/         (临时分支不允许)
   ```

3. **分支名应该清晰表达目的**
   ```
   ✅ feature/001-add-rss-feed-support
   ✅ bugfix/fix-simhash-collision-bug
   ✅ hotfix/handle-database-timeout
   ❌ feature/new-stuff
   ❌ feature/try-something
   ❌ feature/wip
   ```

4. **分支名长度限制**
   ```
   推荐：prefix/ticket-description
   ✅ feature/001-add-rss-parser          (30字符)
   ✅ bugfix/fix-timeout-in-ai-processing (35字符)
   ❌ feature/very-long-branch-name-that-describes-everything-in-excessive-detail (太长)
   ```

### 🟡 SHOULD - 强烈建议

1. **分支从 develop 创建**
   ```bash
   ✅ git checkout develop
      git pull origin develop
      git checkout -b feature/001-add-feature
   ```

2. **删除合并后的分支**
   ```bash
   ✅ git branch -d feature/001-add-rss-parser (已合并后删除)
   ```

---

## Git 提交信息命名

### 🔴 MUST - 严格遵守

遵循 **Conventional Commits** 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

1. **Type（类型）**
   ```
   ✅ feat:      新功能
   ✅ fix:       bug修复
   ✅ refactor:  代码重构
   ✅ test:      测试代码
   ✅ docs:      文档更新
   ✅ chore:     杂务，依赖更新
   ✅ perf:      性能优化
   ✅ ci:        CI/CD配置
   ✅ style:     代码格式（不改变功能）
   ✅ revert:    撤销之前的提交
   ❌ update:    (不允许)
   ❌ add:       (不允许)
   ❌ WIP:       (不允许)
   ```

2. **Scope（作用域）**
   ```
   ✅ collection
   ✅ ai
   ✅ content
   ✅ publishing
   ✅ api
   ✅ database
   ✅ cache
   ✅ auth
   ✅ config
   ```

3. **Subject（主题）**
   ```
   ✅ add RSS feed parser
   ✅ handle timeout error gracefully
   ✅ optimize database query performance
   ❌ Add RSS feed parser (首字母大写不允许)
   ❌ add rss feed parser. (末尾不用句号)
   ❌ Fix bug (太模糊)
   ```

4. **Body（正文，可选）**
   ```
   详细说明修改的原因和内容
   - 什么问题
   - 为什么修复
   - 怎样修复
   ```

5. **Footer（页脚，可选）**
   ```
   ✅ Fixes #123
   ✅ Closes #456
   ✅ BREAKING CHANGE: API endpoint changed
   ```

### 完整示例

```
feat(collection): add RSS feed parser

- Implement RSS 2.0 and Atom feed parsing
- Support feed validation and error handling
- Add deduplication based on feed item GUID

Closes #123
```

```
fix(ai): handle timeout error in content processing

The AI service sometimes times out when processing large documents.
This change adds exponential backoff retry logic and proper error logging.

Fixes #456
```

```
refactor(database): optimize content query performance

- Add database index on source_id and created_at
- Reduce N+1 queries in content listing
- Improve pagination handling

Performance improvement: ~40% faster on large datasets
```

### 🟡 SHOULD - 强烈建议

1. **一个提交对应一个逻辑改动**
   ```
   ✅ commit 1: feat(api): add new endpoint
      commit 2: test(api): add tests for new endpoint

   ❌ commit 1: feat(api): add new endpoint and fix bug and update docs
   ```

2. **提交信息用现在时，用祈使语**
   ```
   ✅ add RSS parser
   ✅ fix timeout issue
   ❌ added RSS parser
   ❌ fixed timeout issue
   ```

3. **每天至少提交一次**
   ```
   避免大量代码在本地未提交
   ```

---

## 常量和枚举命名

### 🔴 MUST - 严格遵守

1. **枚举值使用 UPPER_CASE**
   ```python
   ✅ class ContentStatus(Enum):
           DRAFT = "draft"
           REVIEWING = "reviewing"
           PUBLISHED = "published"
           ARCHIVED = "archived"

   ❌ class ContentStatus(Enum):
           Draft = "draft"
           draft = "draft"
   ```

2. **枚举类名使用 PascalCase**
   ```python
   ✅ class ContentStatus(Enum):
   ✅ class ReviewDecision(Enum):
   ✅ class PublishingChannel(Enum):
   ❌ class content_status(Enum):
   ```

3. **boolean常量清晰表达含义**
   ```python
   ✅ IS_PRODUCTION = True
   ✅ ENABLE_CACHING = False
   ✅ REQUIRE_REVIEW = True
   ❌ PROD = True
   ❌ CACHE = False
   ```

---

## 命名检查清单

提交代码前检查：

- [ ] 所有文件名使用 snake_case
- [ ] 所有类名使用 PascalCase
- [ ] 所有函数名使用 snake_case
- [ ] 布尔函数使用 is_/has_/can_ 前缀
- [ ] 常量使用 UPPER_CASE
- [ ] 数据库表名使用 snake_case 复数形式
- [ ] API路由使用 kebab-case
- [ ] Git分支名使用 prefix/description 格式
- [ ] Git提交信息遵循 Conventional Commits
- [ ] 没有单字母变量（循环除外）
- [ ] 没有歧义或过度缩写的名字

---

**记住：** 好的名字是最好的注释！名字应该自解释，让读者一眼就能理解意图。

